import numpy as np
import pandas as pd

class SMACrossoverStrategy:
    def __init__(self, fast_period, slow_period):
        self.fast_period = fast_period
        self.slow_period = slow_period

    def apply(self, data: pd.DataFrame) -> pd.DataFrame:
        data['Fast_SMA'] = data['close'].rolling(window=self.fast_period).mean()
        data['Slow_SMA'] = data['close'].rolling(window=self.slow_period).mean()
        data['Signal'] = 0
        data['Signal'][self.slow_period:] = np.where(data['Fast_SMA'][self.slow_period:] > data['Slow_SMA'][self.slow_period:], 1, -1)
        data['Position'] = data['Signal'].diff()
        return data

class EMACrossoverStrategy:
    def __init__(self, fast_period, slow_period):
        self.fast_period = fast_period
        self.slow_period = slow_period

    def apply(self, data: pd.DataFrame) -> pd.DataFrame:
        data['Fast_EMA'] = data['close'].ewm(span=self.fast_period, adjust=False).mean()
        data['Slow_EMA'] = data['close'].ewm(span=self.slow_period, adjust=False).mean()
        data['Signal'] = 0
        data['Signal'][self.slow_period:] = np.where(data['Fast_EMA'][self.slow_period:] > data['Slow_EMA'][self.slow_period:], 1, -1)
        data['Position'] = data['Signal'].diff()
        return data

class SMAIndicator:
    def __init__(self, period):
        self.period = period

    def apply(self, data: pd.DataFrame) -> pd.DataFrame:
        data['SMA'] = data['close'].rolling(window=self.period).mean()
        data['Signal'] = 0
        data['Signal'][self.period:] = np.where(data['close'][self.period:] > data['SMA'][self.period:], 1, -1)
        data['Position'] = data['Signal'].diff()
        return data

class EMAIndicator:
    def __init__(self, period):
        self.period = period

    def apply(self, data: pd.DataFrame) -> pd.DataFrame:
        data['EMA'] = data['close'].ewm(span=self.period, adjust=False).mean()
        data['Signal'] = 0
        data['Signal'][self.period:] = np.where(data['close'][self.period:] > data['EMA'][self.period:], 1, -1)
        data['Position'] = data['Signal'].diff()
        return data

class RSIIndicator:
    def __init__(self, period):
        self.period = period

    def apply(self, data: pd.DataFrame) -> pd.DataFrame:
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.period).mean()
        rs = gain / loss
        data['RSI'] = 100 - (100 / (1 + rs))
        data['Signal'] = 0
        data['Signal'][self.period:] = np.where(data['RSI'][self.period:] > 70, -1, np.where(data['RSI'][self.period:] < 30, 1, 0))
        data['Position'] = data['Signal'].diff()
        return data

class MACDIndicator:
    def __init__(self, fast_period, slow_period, signal_period):
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period

    def apply(self, data: pd.DataFrame) -> pd.DataFrame:
        data['Fast_EMA'] = data['close'].ewm(span=self.fast_period, adjust=False).mean()
        data['Slow_EMA'] = data['close'].ewm(span=self.slow_period, adjust=False).mean()
        data['MACD'] = data['Fast_EMA'] - data['Slow_EMA']
        data['Signal_Line'] = data['MACD'].ewm(span=self.signal_period, adjust=False).mean()
        data['Signal'] = 0
        data['Signal'][self.signal_period:] = np.where(data['MACD'][self.signal_period:] > data['Signal_Line'][self.signal_period:], 1, -1)
        data['Position'] = data['Signal'].diff()
        return data
    
class BollingerBandsIndicator:
    def __init__(self, period, std_dev):
        self.period = period
        self.std_dev = std_dev

    def apply(self, data: pd.DataFrame) -> pd.DataFrame:
        data['SMA'] = data['close'].rolling(window=self.period).mean()
        data['STD'] = data['close'].rolling(window=self.period).std()
        data['Upper_Band'] = data['SMA'] + (data['STD'] * self.std_dev)
        data['Lower_Band'] = data['SMA'] - (data['STD'] * self.std_dev)
        data['Signal'] = 0
        data['Signal'][self.period:] = np.where(data['close'][self.period:] > data['Upper_Band'][self.period:], -1, np.where(data['close'][self.period:] < data['Lower_Band'][self.period:], 1, 0))
        data['Position'] = data['Signal'].diff()
        return data
