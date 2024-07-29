import json
import logging
import os
import time
from datetime import datetime, timedelta, timezone

import pandas as pd
import requests

import backend.defs as defs
from backend.utils.utility import configure_logging


configure_logging("oanda")    

class OandaAPI:
    
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
        logging.error(f"Max retries exceeded for {url}")
        return None

    def check_account(self):
        url = f"{defs.OANDA_URL}/accounts/{defs.ACCOUNT_ID}"
        try:
            response = self._request_with_retries("GET", url, headers={'Authorization': f'Bearer {defs.API_KEY}'})
            if response is None:
                logging.error("No response received for check_account")
                return None, "No response received"
            if response and response.status_code == 200:
                account_info = response.json()['account']
                account_id = account_info['id']
                balance = account_info['balance']
                open_exchanges = self.get_open_exchanges()
                logging.info("Account information retrieved successfully!")
                return {
                    "account_id": account_id,
                    "balance": balance,
                    "open_exchanges": open_exchanges,
                    "margin_used": account_info['marginUsed'],
                    "margin_available": account_info['marginAvailable'],
                    "open_trades": account_info['openTradeCount'],
                    "open_positions": account_info['openPositionCount'],
                    "unrealized_pl": account_info['unrealizedPL']
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

    def get_open_trades(self):
        url = f"{defs.OANDA_URL}/accounts/{defs.ACCOUNT_ID}/openTrades"
        try:
            response = self._request_with_retries("GET", url, headers={'Authorization': f'Bearer {defs.API_KEY}'})
            if response is None:
                logging.error("No response received for get_open_trades")
                return None, "No response received"
            if response.status_code == 200:
                return response.json()['trades'], "Open trades retrieved successfully!"
            else:
                logging.error(f"Failed to retrieve open trades: {response.status_code} {response.text}")
                return None, f"Failed to retrieve open trades: {response.status_code} {response.text}"
        except Exception as e:
            logging.error(f"Error retrieving open trades: {e}")
            return None, str(e)

    def get_open_positions(self):
        url = f"{defs.OANDA_URL}/accounts/{defs.ACCOUNT_ID}/openPositions"
        try:
            response = self._request_with_retries("GET", url, headers={'Authorization': f'Bearer {defs.API_KEY}'})
            if response is None:
                logging.error("No response received for get_open_positions")
                return None, "No response received"
            if response.status_code == 200:
                return response.json()['positions'], "Open positions retrieved successfully!"
            else:
                logging.error(f"Failed to retrieve open positions: {response.status_code} {response.text}")
                return None, f"Failed to retrieve open positions: {response.status_code} {response.text}"
        except Exception as e:
            logging.error(f"Error retrieving open positions: {e}")
            return None, str(e)


    def get_historical_data(self, instrument, granularity='D', count=500):
        url = f"{defs.OANDA_URL}/instruments/{instrument}/candles"
        params = {
            'granularity': granularity,
            'count': count,
            'price': 'M'
        }
        response = self._request_with_retries("GET", url, headers={'Authorization': f'Bearer {defs.API_KEY}'}, params=params)
        if response is None:
            logging.error("No response received for get_historical_data")
            return None, "No response received"
        if response.status_code == 200:
            data = response.json().get('candles', [])
            print("PRCode: oanda_api - I got historical data here!")
            if not data:
                logging.error("No candles data found in the response")
                return None, "No candles data found in the response"
            
            df = pd.DataFrame.from_records([{
                'time': candle['time'],
                'open': candle['mid']['o'],
                'high': candle['mid']['h'],
                'low': candle['mid']['l'],
                'close': candle['mid']['c']
            } for candle in data if 'mid' in candle and 'time' in candle])
            
            if 'time' not in df.columns:
                logging.error("No 'time' column in the historical data")
                return None, "No 'time' column in the historical data"
            
            df['time'] = pd.to_datetime(df['time'])
            df.set_index('time', inplace=True)
            
            df['open'] = pd.to_numeric(df['open'])
            df['high'] = pd.to_numeric(df['high'])
            df['low'] = pd.to_numeric(df['low'])
            df['close'] = pd.to_numeric(df['close'])
            
            logging.info(f"Retrieved historical data for {instrument}: {df.head()}")
            return df, "Historical data retrieved successfully!"
        elif response:
            logging.error(f"Got a response but failed to retrieve historical data: {response.status_code} {response.text}")
            return None, f"Failed to retrieve historical data: {response.status_code} {response.text}"
        elif response is None:
            logging.error(f"There was an error... failed to retrieve a response for historical data: {response.status_code} {response.text}")
            return None, f"Failed to retrieve historical data: {response.status_code} {response.text}"
        else:
            logging.error("Failed to retrieve historical data: No response received")
            return None, "No response received"

    def set_stop_loss(self, price):
        return {"price": str(price)}

    def set_take_profit(self, price):
        return {"price": str(price)}
    
    def place_trade(self, instrument, units, side, order_type, price=None, stop_loss=None, take_profit=None, trailing_stop_loss=None):
        url = f"{defs.OANDA_URL}/accounts/{defs.ACCOUNT_ID}/orders"
        order = {
            "units": str(units) if side == 'buy' else str(-units),
            "instrument": instrument,
            "timeInForce": "GTC",
            "type": order_type,
            "positionFill": "DEFAULT"
        }
        if price:
            order["price"] = str(price)
        if stop_loss:
            order["stopLossOnFill"] = self.set_stop_loss(stop_loss)
        if take_profit:
            order["takeProfitOnFill"] = self.set_take_profit(take_profit)

        data = {"order": order}
        try:
            response = self._request_with_retries("POST", url, headers={'Authorization': f'Bearer {defs.API_KEY}'}, data=json.dumps(data))
            if response is None:
                logging.error("No response received for place_trade")
                return None, "No response received"
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
            if response is None:
                logging.error("No response received for close_trade")
                return None, "No response received"
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
        open_positions, message = self.get_open_positions()
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
