import logging
import requests
import pandas as pd
from datetime import datetime, timedelta, timezone
import defs

# Configure logging
logging.basicConfig(filename='./logs/OandaAPIData.log', level=logging.INFO, format='%(asctime)s %(levelname)s:%(message)s')

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
        raise requests.exceptions.RequestException("Max retries exceeded")

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
        if response.status_code == 200:
            data = response.json()['candles']
            df = pd.DataFrame.from_records([{
                'time': candle['time'],
                'open': candle['mid']['o'],
                'high': candle['mid']['h'],
                'low': candle['mid']['l'],
                'close': candle['mid']['c']
            } for candle in data])
            df['time'] = pd.to_datetime(df['time'])
            df.set_index('time', inplace=True)
            
            df['open'] = pd.to_numeric(df['open'])
            df['high'] = pd.to_numeric(df['high'])
            df['low'] = pd.to_numeric(df['low'])
            df['close'] = pd.to_numeric(df['close'])
            
            return df, "Historical data retrieved successfully!"
        else:
            logging.error(f"Failed to retrieve historical data: {response.status_code} {response.text}")
            return None, f"Failed to retrieve historical data: {response.status_code} {response.text}"
