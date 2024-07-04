import json
import logging
import time
from datetime import datetime, timedelta, timezone

import defs
import pandas as pd
import requests
from dateutil.parser import parse
from flask import Flask, jsonify, render_template

# Flask app
app = Flask(__name__)

# Configure logging
logging.basicConfig(filename='./logs/OandaAPIData.log', level=logging.INFO, format='%(asctime)s %(levelname)s:%(message)s')

class OandaAPI:
    # Connection and Initialization
    def __init__(self):
        self.session = requests.Session()

    def _request_with_retries(self, method, url, headers=None, params=None, data=None, max_retries=5, backoff_factor=0.3):
        for attempt in range(max_retries):
            try:
                response = self.session.request(method, url, headers=headers, params=params, data=data)
                if response.status_code in [200, 201, 202]:
                    return response
                elif response.status_code == 503:
                    raise requests.exceptions.RequestException("Service unavailable (503)")
            except requests.exceptions.RequestException as e:
                wait_time = backoff_factor * (2 ** attempt)
                logging.warning(f"Request failed (attempt {attempt + 1}/{max_retries}): {e}. Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
        raise requests.exceptions.RequestException("Max retries exceeded")
    
    def check_connection(self):
        url = f"{defs.OANDA_URL}/accounts/{defs.ACCOUNT_ID}"
        try:
            response = self._request_with_retries("GET", url, headers={'Authorization': f'Bearer {defs.API_KEY}'})
            if response.status_code == 200:
                logging.info("Connection successful!")
                return response.json(), "Connection successful!"
            else:
                logging.error(f"Failed to connect: {response.status_code} {response.text}")
                return None, f"Failed to connect: {response.status_code} {response.text}"
        except Exception as e:
            logging.error(f"Error checking connection: {e}")
            return None, str(e)

    # Account and Information methods
    def check_account(self):
        url = f"{defs.OANDA_URL}/accounts/{defs.ACCOUNT_ID}"
        try:
            response = self._request_with_retries("GET", url, headers={'Authorization': f'Bearer {defs.API_KEY}'})
            if response.status_code == 200:
                account_info = response.json()['account']
                account_id = account_info['id']
                balance = account_info['balance']
                open_exchanges = self.get_open_exchanges()
                logging.info("Account information retrieved successfully!")
                return {
                    "account_id": account_id,
                    "balance": balance,
                    "open_exchanges": open_exchanges
                }, "Account information retrieved successfully!"
            else:
                logging.error(f"Failed to retrieve account information: {response.status_code} {response.text}")
                return None, f"Failed to retrieve account information: {response.status_code} {response.text}"
        except Exception as e:
            logging.error(f"Error checking account: {e}")
            return None, str(e)

    def get_open_exchanges(self):
        now_utc = datetime.now(timezone.utc)
        exchanges = {
            'Sydney': {'open': 22, 'close': 6},
            'Tokyo': {'open': 0, 'close': 8},
            'London': {'open': 8, 'close': 16},
            'New York': {'open': 13, 'close': 21}
        }

        open_exchanges = []
        for exchange, hours in exchanges.items():
            open_time = now_utc.replace(hour=hours['open'], minute=0, second=0, microsecond=0)
            close_time = now_utc.replace(hour=hours['close'], minute=0, second=0, microsecond=0)

            if hours['close'] < hours['open']:
                close_time += timedelta(days=1)

            if open_time <= now_utc < close_time:
                open_exchanges.append(exchange)

        return open_exchanges

    def get_account_details(self):
        url = f'{defs.BASE_URL}/accounts/{defs.ACCOUNT_ID}'
        response = requests.get(url, headers=defs.SECURE_HEADER)
        return response.json()

    def get_instruments(self):
        url = f'{defs.BASE_URL}/accounts/{defs.ACCOUNT_ID}/instruments'
        response = self._request_with_retries("GET", url, headers=defs.SECURE_HEADER)
        return response.status_code, response.json()

    def get_instruments_df(self):
        code, data = self.get_instruments()
        if code == 200:
            df = pd.DataFrame.from_dict(data['instruments'])
            return df[['name', 'type', 'displayName', 'pipLocation', 'marginRate']]
        else:
            logging.error(f"Failed to fetch instruments: {code}")
            return None

    def get_candles(self, instrument, granularity='D', count=200):
        url = f'{defs.BASE_URL}/instruments/{instrument}/candles'
        params = {'granularity': granularity, 'count': count}
        response = requests.get(url, headers=defs.SECURE_HEADER, params=params)
        data = response.json()['candles']
        return convert_to_dataframe(data)
    
    def fetch_candles(self, pair_name, count=None, granularity="H1", date_from=None, date_to=None, as_df=False):
        url = f"{defs.OANDA_URL}/instruments/{pair_name}/candles"

        params = dict(
            granularity=granularity,
            price="MBA"
        )

        if date_from is not None and date_to is not None:
            params['to'] = int(date_to.timestamp())
            params['from'] = int(date_from.timestamp())
        elif count is not None:
            params['count'] = count
        else:
            params['count'] = 300

        response = self._request_with_retries("GET", url, headers={'Authorization': f'Bearer {defs.API_KEY}'}, params=params)

        if response.status_code != 200:
            logging.error(f"Failed to fetch candles: {response.status_code}")
            return response.status_code, None

        if as_df:
            json_data = response.json()['candles']
            return response.status_code, self.candles_to_df(json_data)
        else:
            return response.status_code, response.json()

    # Class methods
    @classmethod
    def candles_to_df(cls, json_data):
        prices = ['mid', 'bid', 'ask']
        ohlc = ['o', 'h', 'l', 'c']

        our_data = []
        for candle in json_data:
            if not candle['complete']:
                continue
            new_dict = {
                'time': candle['time'],
                'volume': candle['volume']
            }
            for price in prices:
                for oh in ohlc:
                    new_dict[f"{price}_{oh}"] = float(candle[price][oh])
            our_data.append(new_dict)
        df = pd.DataFrame.from_dict(our_data)
        df["time"] = [parse(x) for x in df.time]
        return df

    # Trades methods
    def place_trade(self, instrument, units, side, stop_loss=None, take_profit=None, trailing_stop_loss=None):
        url = f"{defs.OANDA_URL}/accounts/{defs.ACCOUNT_ID}/orders"
        order = {
            "units": str(units) if side == 'buy' else str(-units),
            "instrument": instrument,
            "timeInForce": "FOK",
            "type": "MARKET",
            "positionFill": "DEFAULT"
        }
        if stop_loss:
            order["stopLossOnFill"] = self.set_stop_loss(stop_loss, trailing=trailing_stop_loss)
        if take_profit:
            order["takeProfitOnFill"] = self.set_take_profit(take_profit)

        data = {"order": order}
        try:
            response = self._request_with_retries("POST", url, headers={'Authorization': f'Bearer {defs.API_KEY}'}, data=json.dumps(data))
            if response.status_code == 201:
                logging.info("Trade placed successfully!")
                return response.json(), "Trade placed successfully!"
            else:
                logging.error(f"Failed to place trade: {response.status_code} {response.text}")
                return None, f"Failed to place trade: {response.status_code} {response.text}"
        except Exception as e:
            logging.error(f"Error placing trade: {e}")
            return None, str(e)

    def close_trade(self, trade_id):
        url = f"{defs.OANDA_URL}/accounts/{defs.ACCOUNT_ID}/trades/{trade_id}/close"
        try:
            response = self._request_with_retries("PUT", url, headers={'Authorization': f'Bearer {defs.API_KEY}'})
            if response.status_code == 200:
                logging.info("Trade closed successfully!")
                return response.json(), "Trade closed successfully!"
            else:
                logging.error(f"Failed to close trade: {response.status_code} {response.text}")
                return None, f"Failed to close trade: {response.status_code} {response.text}"
        except Exception as e:
            logging.error(f"Error closing trade: {e}")
            return None, str(e)

    def close_all_trades(self):
        open_positions, message = self.check_open_positions()
        if not open_positions:
            logging.info("No open positions to close.")
            return None, "No open positions to close."

        closed_trades = []
        for position in open_positions['positions']:
            side = 'buy' if int(position['long']['units']) < 0 else 'sell'
            trade_id = position['long']['tradeIDs'][0] if side == 'sell' else position['short']['tradeIDs'][0]
            close_response, close_message = self.close_trade(trade_id)
            closed_trades.append((trade_id, close_message))

        logging.info("All open trades have been closed.")
        return closed_trades, "All open trades have been closed."

    def check_open_positions(self):
        url = f"{defs.OANDA_URL}/accounts/{defs.ACCOUNT_ID}/openPositions"
        try:
            response = self._request_with_retries("GET", url, headers={'Authorization': f'Bearer {defs.API_KEY}'})
            if response.status_code == 200:
                logging.info("Open positions retrieved successfully!")
                return response.json(), "Open positions retrieved successfully!"
            else:
                logging.error(f"Failed to retrieve open positions: {response.status_code} {response.text}")
                return None, f"Failed to retrieve open positions: {response.status_code} {response.text}"
        except Exception as e:
            logging.error(f"Error checking open positions: {e}")
            return None, str(e)

    def set_stop_loss(self, price, trailing=False):
        if trailing:
            return {"distance": str(price)}
        else:
            return {"price": str(price)}

    def set_take_profit(self, price):
        return {"price": str(price)}

    def place_order(self, instrument, units, order_type=ORDER_TYPE):
        url = f'{defs.BASE_URL}/accounts/{defs.ACCOUNT_ID}/orders'
        data = {
            'order': {
                'instrument': instrument,
                'units': str(units),
                'type': order_type,
                'positionFill': 'DEFAULT'
            }
        }
        response = requests.post(url, headers=defs.SECURE_HEADER, json=data)
        return response.json()

    def save_historical_data(self, instrument, granularity=TRADING_GRANULARITY, count=TRADING_COUNT, file_path='historical_data.csv'):
        try:
            df = self.get_candles(instrument, granularity, count)
            df.to_csv(file_path, index=False)
            logging.info(f"Historical data saved to {file_path}")
            return file_path
        except Exception as e:
            logging.error(f"Error saving historical data: {e}")
            return None


@app.route('/')
def index():
    oanda_api = OandaAPI()
    account_info, message = oanda_api.check_account()
    if account_info:
        return render_template('index.html', account_info=account_info)
    else:
        return f"<h1>Error: {message}</h1>", 500

if __name__ == '__main__':
    app.run(debug=True)