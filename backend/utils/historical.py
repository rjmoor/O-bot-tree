import requests
import pandas as pd
from datetime import datetime, timedelta
import os
import defs  # Make sure your API keys and URLs are defined here
import logging
import schedule
import time

# Configure logging
logging.basicConfig(filename='./logs/forex_data_generator.log', level=logging.INFO, format='%(asctime)s %(levelname)s:%(message)s')

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
            
            # Ensure numeric types for calculations
            df['open'] = pd.to_numeric(df['open'])
            df['high'] = pd.to_numeric(df['high'])
            df['low'] = pd.to_numeric(df['low'])
            df['close'] = pd.to_numeric(df['close'])
            
            return df
        else:
            logging.error(f"Failed to retrieve historical data for {instrument}: {response.status_code} {response.text}")
            return None

def store_historical_data():
    oanda_api = OandaAPI()
    major_pairs = ['EUR_USD', 'GBP_USD', 'USD_JPY', 'AUD_USD', 'USD_CHF', 'USD_CAD', 'NZD_USD']

    for pair in major_pairs:
        df = oanda_api.get_historical_data(pair)
        if df is not None:
            file_path = f'historical_data/{pair}.csv'
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            df.to_csv(file_path)
            logging.info(f"Historical data for {pair} stored successfully.")
        else:
            logging.error(f"Failed to store historical data for {pair}.")

def run_daily():
    store_historical_data()

    # Schedule the task to run daily
    schedule.every().day.at("00:00").do(store_historical_data)
    
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == '__main__':
    run_daily()
