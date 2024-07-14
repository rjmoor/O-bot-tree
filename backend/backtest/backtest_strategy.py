import pandas as pd
import numpy as np  # Add this import

class BacktestStrategy:
    def __init__(self, data, indicators):
        self.data = data
        self.indicators = indicators

    def apply_indicators(self):
        # Apply the indicators to the data
        if 'SMA' in self.indicators:
            self.data['SMA'] = self.data['close'].rolling(window=20).mean()
        if 'EMA' in self.indicators:
            self.data['EMA'] = self.data['close'].ewm(span=20, adjust=False).mean()
        if 'RSI' in self.indicators:
            delta = self.data['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            self.data['RSI'] = 100 - (100 / (1 + rs))
        if 'MACD' in self.indicators:
            exp1 = self.data['close'].ewm(span=12, adjust=False).mean()
            exp2 = self.data['close'].ewm(span=26, adjust=False).mean()
            self.data['MACD'] = exp1 - exp2
            self.data['MACD_Signal'] = self.data['MACD'].ewm(span=9, adjust=False).mean()
        if 'BOLLINGER_BANDS' in self.indicators:
            self.data['Upper_Band'] = self.data['close'].rolling(window=20).mean() + (self.data['close'].rolling(window=20).std() * 2)
            self.data['Lower_Band'] = self.data['close'].rolling(window=20).mean() - (self.data['close'].rolling(window=20).std() * 2)
        if 'STOCHASTIC' in self.indicators:
            low_14 = self.data['low'].rolling(window=14).min()
            high_14 = self.data['high'].rolling(window=14).max()
            self.data['%K'] = 100 * ((self.data['close'] - low_14) / (high_14 - low_14))
            self.data['%D'] = self.data['%K'].rolling(window=3).mean()

            
    def generate_signals(self):
        # Generate buy and sell signals based on indicators
        self.data['Signal'] = 0
        
        if 'SMA' in self.indicators:
            self.data['Signal'] = self.data.apply(lambda row: 1 if row['close'] > row['SMA'] else -1 if row['close'] < row['SMA'] else 0, axis=1)
        
        if 'EMA' in self.indicators:
            self.data['Signal'] = self.data.apply(lambda row: 1 if row['close'] > row['EMA'] else -1 if row['close'] < row['EMA'] else 0, axis=1)
        
        if 'RSI' in self.indicators:
            self.data['Signal'] = self.data.apply(lambda row: -1 if row['RSI'] > 70 else 1 if row['RSI'] < 30 else 0, axis=1)
        
        if 'MACD' in self.indicators:
            self.data['Signal'] = self.data.apply(lambda row: 1 if row['MACD'] > row['MACD_Signal'] else -1 if row['MACD'] < row['MACD_Signal'] else 0, axis=1)
        
        if 'BOLLINGER_BANDS' in self.indicators:
            self.data['Signal'] = self.data.apply(lambda row: 1 if row['close'] < row['Lower_Band'] else -1 if row['close'] > row['Upper_Band'] else 0, axis=1)
        
        if 'STOCHASTIC' in self.indicators:
            self.data['Signal'] = self.data.apply(lambda row: -1 if row['%K'] > 80 else 1 if row['%K'] < 20 else 0, axis=1)


    def backtest(self):
        self.apply_indicators()
        self.generate_signals()
        
        self.data['Position'] = self.data['Signal'].shift()
        self.data['Return'] = self.data['close'].pct_change()
        self.data['Strategy_Return'] = self.data['Return'] * self.data['Position']
        
        total_return = self.data['Strategy_Return'].sum()
        num_trades = self.data['Position'].abs().sum()
        win_rate = (self.data['Strategy_Return'] > 0).mean()

        return self.data, total_return, num_trades, win_rate

    def calculate_rsi(self, period=14):
        delta = self.data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    def calculate_macd(self, fast_period=12, slow_period=26, signal_period=9):
        ema_fast = self.data['close'].ewm(span=fast_period, adjust=False).mean()
        ema_slow = self.data['close'].ewm(span=slow_period, adjust=False).mean()
        macd = ema_fast - ema_slow
        signal = macd.ewm(span=signal_period, adjust=False).mean()
        histogram = macd - signal
        return macd, signal, histogram

    def calculate_bollinger_bands(self, period=20, std_dev=2):
        sma = self.data['close'].rolling(window=period).mean()
        std = self.data['close'].rolling(window=period).std()
        upper_band = sma + (std_dev * std)
        lower_band = sma - (std_dev * std)
        return upper_band, lower_band

    def calculate_stochastic(self, k_period=14, d_period=3):
        low_min = self.data['low'].rolling(window=k_period).min()
        high_max = self.data['high'].rolling(window=k_period).max()
        self.data['%K'] = 100 * (self.data['close'] - low_min) / (high_max - low_min)
        self.data['%D'] = self.data['%K'].rolling(window=d_period).mean()
        return self.data['%K'], self.data['%D']
