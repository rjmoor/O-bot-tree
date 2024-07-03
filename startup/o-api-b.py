# oanda_api.py
import json
import requests
import pandas as pd
import os
import pickle
from defs import ACCOUNT_ID, API_KEY, OANDA_URL, SECURE_HEADER
from forex_pairs import ForexPairsGenerator
from trading_indicators import TradingIndicators
from datetime import datetime

class OandaAPI:
    def __init__(self, api_key=API_KEY, account_id=ACCOUNT_ID, base_url=OANDA_URL):
        self.api_key = api_key
        self.account_id = account_id
        self.base_url = base_url
        self.forex_pairs_generator = ForexPairsGenerator()

    def _get_headers(self):
        return SECURE_HEADER

    def get_account_details(self):
        url = f"{self.base_url}/accounts/{self.account_id}"
        response = requests.get(url, headers=self._get_headers())
        return response.json()

    def get_instruments(self):
        url = f"{self.base_url}/accounts/{self.account_id}/instruments"
        response = requests.get(url, headers=self._get_headers())
        return response.json()
    
    def get_historical_data(self, instrument, granularity="D", count=500):
        url = f"{self.base_url}/instruments/{instrument}/candles"
        params = {
            "granularity": granularity,
            "count": count,
            "price": "M"  # Midpoint prices
        }
        response = requests.get(url, headers=self._get_headers(), params=params)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch historical data: {response.text}")
        return response.json()

    def save_historical_data(self, instrument, data, granularity, count, folder="backend/history_data"):
        if not os.path.exists(folder):
            os.makedirs(folder)
        file_path = os.path.join(folder, f"{instrument}_{granularity}_{count}.pkl")
        with open(file_path, "wb") as file:
            pickle.dump(data, file)

    def load_historical_data(self, instrument, granularity, count, folder="backend/history_data"):
        file_path = os.path.join(folder, f"{instrument}_{granularity}_{count}.pkl")
        if os.path.exists(file_path):
            with open(file_path, "rb") as file:
                return pickle.load(file)
        return None
    
    def update_historical_data(self, instrument, granularity="D", count=500):
        existing_data = self.load_historical_data(instrument, granularity, count)
        if existing_data:
            last_time = existing_data['candles'][-1]['time']
            last_time_dt = datetime.strptime(last_time, '%Y-%m-%dT%H:%M:%S.%fZ')
            now = datetime.now()
            days_diff = (now - last_time_dt).days
            if days_diff > 0:
                new_data = self.get_historical_data(instrument, granularity=granularity, count=days_diff)
                existing_data['candles'].extend(new_data['candles'])
                self.save_historical_data(instrument, existing_data, granularity, count)
        else:
            new_data = self.get_historical_data(instrument, granularity=granularity, count=count)
            self.save_historical_data(instrument, new_data, granularity, count)    
        
    def delete_historical_data(self, instrument, granularity, count, folder="backend/history_data"):
        file_path = os.path.join(folder, f"{instrument}_{granularity}_{count}.pkl")
        if os.path.exists(file_path):
            os.remove(file_path)
        
    def place_order(self, instrument, units, order_type="MARKET"):
        url = f"{self.base_url}/accounts/{self.account_id}/orders"
        data = {
            "order": {
                "instrument": instrument,
                "units": units,
                "type": order_type,
                "positionFill": "DEFAULT"
            }
        }
        response = requests.post(url, headers=self._get_headers(), data=json.dumps(data))
        return response.json()

    def place_trailing_stop_order(self, instrument, units, distance):
        url = f"{self.base_url}/accounts/{self.account_id}/orders"
        data = {
            "order": {
                "instrument": instrument,
                "units": units,
                "type": "MARKET_IF_TOUCHED",
                "trailingStopLossOnFill": {
                    "distance": distance
                },
                "positionFill": "DEFAULT"
            }
        }
        response = requests.post(url, headers=self._get_headers(), data=json.dumps(data))
        return response.json()

    def place_take_profit_order(self, instrument, units, take_profit_price):
        url = f"{self.base_url}/accounts/{self.account_id}/orders"
        data = {
            "order": {
                "instrument": instrument,
                "units": units,
                "type": "LIMIT",
                "price": take_profit_price,
                "positionFill": "DEFAULT"
            }
        }
        response = requests.post(url, headers=self._get_headers(), data=json.dumps(data))
        return response.json()

    def close_all_orders(self):
        open_trades = requests.get(f"{self.base_url}/accounts/{self.account_id}/openTrades", headers=self._get_headers()).json()
        for trade in open_trades.get("trades", []):
            trade_id = trade["id"]
            requests.put(f"{self.base_url}/accounts/{self.account_id}/trades/{trade_id}/close", headers=self._get_headers())
        return {"status": "All orders closed"}

    def get_all_forex_pairs(self):
        return self.forex_pairs_generator.generate_pairs()

    def get_tradable_forex_pairs(self):
        return [instrument["name"] for instrument in self.get_instruments().get("instruments", []) if "_USD" in instrument["name"]]

# Example usage
if __name__ == "__main__":
    oanda = OandaAPI()
    instrument = "EUR_USD"
    
    # Get account details
    account_details = oanda.get_account_details()
    print("Account Details:", account_details)

    # Get available instruments
    instruments = oanda.get_instruments()
    print("Instruments:", instruments)

    # Fetch and save historical data
    historical_data = oanda.get_historical_data(instrument, granularity='granularity', count='count')
    oanda.save_historical_data(instrument, historical_data, granularity='granularity', count='count')
    print(f"Saved historical data for {instrument}")

    # Get the latest price for a specific instrument
    instrument = "EUR_USD"
    price = oanda.get_price(instrument)
    print("Price:", price)

    # Place a market order
    order_response = oanda.place_order(instrument, units=100)
    print("Order Response:", order_response)

    # Place a trailing stop order
    trailing_stop_response = oanda.place_trailing_stop_order(instrument, units=100, distance="0.01")
    print("Trailing Stop Order Response:", trailing_stop_response)

    # Place a take profit order
    take_profit_response = oanda.place_take_profit_order(instrument, units=100, take_profit_price="1.2000")
    print("Take Profit Order Response:", take_profit_response)

    # Close all orders
    close_orders_response = oanda.close_all_orders()
    print("Close All Orders Response:", close_orders_response)

    # Get all Forex pairs
    forex_pairs = oanda.get_all_forex_pairs()
    print("Forex Pairs:", forex_pairs)