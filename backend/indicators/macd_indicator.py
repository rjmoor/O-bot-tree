import pandas as pd

class MACDIndicator:
    def __init__(self, fast_period=12, slow_period=26, signal_period=9):
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period

    def calculate_macd(self, data: pd.DataFrame) -> pd.DataFrame:
        # Calculate the short-term EMA
        data['EMA_short'] = data['close'].ewm(span=self.fast_period, adjust=False).mean()
        # Calculate the long-term EMA
        data['EMA_long'] = data['close'].ewm(span=self.slow_period, adjust=False).mean()
        # Calculate the MACD line
        data['MACD'] = data['EMA_short'] - data['EMA_long']
        # Calculate the Signal line
        data['Signal'] = data['MACD'].ewm(span=self.signal_period, adjust=False).mean()
        # Calculate the Histogram
        data['Histogram'] = data['MACD'] - data['Signal']
        return data

    def generate_signal(self, data: pd.DataFrame) -> pd.DataFrame:
        data = self.calculate_macd(data)
        data['MACD_Signal'] = 0
        # Generate signals: 1 for buy, -1 for sell
        data['MACD_Signal'] = data.apply(
            lambda row: 1 if row['MACD'] > row['Signal'] else (-1 if row['MACD'] < row['Signal'] else 0), axis=1
        )
        return data

    def check_green_light(self, data: pd.DataFrame) -> bool:
        # Ensure the data has been processed with generate_signal
        if 'MACD_Signal' not in data.columns:
            data = self.generate_signal(data)
        
        # Check for green light condition
        latest_signal = data.iloc[-1]['MACD_Signal']
        return latest_signal == 1
