import json
import logging
import os
import sqlite3
import time
from datetime import datetime

import pandas as pd
import requests
from sqlalchemy import create_engine

import defs 

class PopulateHistory:
    def __init__(self, db_name='forex_data.db'):
        self.conn = sqlite3.connect(db_name)
        self.engine = create_engine(f'sqlite:///{db_name}')
        self.api = OandaAPI()
        self.setup_logging()
    
    def setup_logging(self):
        # Create logs directory if it doesn't exist
        if not os.path.exists('logs'):
            os.makedirs('logs')
        # Configure logging
        logging.basicConfig(
            filename=f'logs/populate_history_{datetime.now().strftime("%Y%m%d")}.log',
            level=logging.INFO,
            format='%(asctime)s %(levelname)s:%(message)s'
        )
        logging.info('Logging configured successfully.')
    
    def create_tables(self, instrument):
        try:
            with self.conn:
                # Create tables for daily, monthly, and minute data for the given instrument
                self.conn.execute(f'''
                    CREATE TABLE IF NOT EXISTS {instrument}_daily (
                        id INTEGER PRIMARY KEY,
                        time TEXT,
                        open REAL,
                        high REAL,
                        low REAL,
                        close REAL
                    )
                ''')
                self.conn.execute(f'''
                    CREATE TABLE IF NOT EXISTS {instrument}_monthly (
                        id INTEGER PRIMARY KEY,
                        time TEXT,
                        open REAL,
                        high REAL,
                        low REAL,
                        close REAL
                    )
                ''')
                self.conn.execute(f'''
                    CREATE TABLE IF NOT EXISTS {instrument}_minute (
                        id INTEGER PRIMARY KEY,
                        time TEXT,
                        open REAL,
                        high REAL,
                        low REAL,
                        close REAL
                    )
                ''')
            logging.info(f"Tables for {instrument} created successfully.")
        except Exception as e:
            logging.error(f"Error creating tables for {instrument}: {e}")

    def populate_table(self, instrument, granularity, table_name):
        try:
            # Get historical data
            data, message = self.api.get_historical_data(instrument, granularity, 5000)
            if data is not None:
                data['time'] = pd.to_datetime(data['time'])
                data = data.sort_values(by='time', ascending=False)
                data.to_sql(table_name, self.engine, if_exists='replace', index=False)
                logging.info(f"Populated {table_name} with {granularity} data for {instrument}")
                print(f"Populated {table_name} with {granularity} data for {instrument}")
            else:
                logging.error(f"Failed to get historical data for {instrument}: {message}")
        except Exception as e:
            logging.error(f"Error populating table {table_name} for {instrument}: {e}")

    def populate_all_instruments(self):
        try:
            instruments = self.api.get_instruments()  # Assuming this method returns a list of all instruments
            for instrument in instruments:
                self.create_tables(instrument)
                self.populate_table(instrument, 'D', f'{instrument}_daily')
                self.populate_table(instrument, 'M', f'{instrument}_monthly')
                self.populate_table(instrument, 'M1', f'{instrument}_minute')
            logging.info("All instruments populated successfully.")
        except Exception as e:
            logging.error(f"Error populating instruments: {e}")

class OandaAPI:
    def __init__(self):
        self.api_url = defs.OANDA_URL
        self.api_key = defs.API_KEY
        self.account_id = defs.ACCOUNT_ID  # Ensure you have the account ID in your defs file
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

    def get_historical_data(self, instrument, granularity, count):
        endpoint = f"/instruments/{instrument}/candles"
        params = {
            "granularity": granularity,
            "count": count,
            "price": "M"
        }
        try:
            response = requests.get(self.api_url + endpoint, headers=self.headers, params=params)
            if response.status_code == 200:    
                data = response.json()
                df = pd.DataFrame([{
                    "time": candle["time"],
                    "open": candle["mid"]["o"],
                    "high": candle["mid"]["h"],
                    "low": candle["mid"]["l"],
                    "close": candle["mid"]["c"]
                } for candle in data["candles"]])
                return df, "Success"
            else:
                return None, response.text
        except requests.exceptions.RequestException as e:
            logging.error(f"Request error: {e}")
            return None, str(e)

    def get_instruments(self):
        endpoint = f"/accounts/{self.account_id}/instruments"
        try:
            response = requests.get(self.api_url + endpoint, headers=self.headers)
            if response.status_code == 200:
                data = response.json()
                instruments = [instrument["name"] for instrument in data["instruments"]]
                return instruments
            else:
                logging.error(f"Failed to get instruments from {endpoint}")
                return []
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to get instruments: {e}")
            return []

if __name__ == "__main__":
    populator = PopulateHistory()
    populator.populate_all_instruments()
