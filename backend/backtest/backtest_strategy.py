import pandas as pd
import numpy as np  # Add this import

class BacktestStrategy:
    def __init__(self, data, indicators):
        self.data = data
        self.indicators = indicators

    def backtest(self):
        for indicator in self.indicators:
            if indicator == 'SMA':
                self.data['SMA'] = self.data['close'].rolling(window=20).mean()
            elif indicator == 'EMA':
                self.data['EMA'] = self.data['close'].ewm(span=20, adjust=False).mean()
            elif indicator == 'RSI':
                self.data['RSI'] = self.calculate_rsi()
            elif indicator == 'MACD':
                self.data['MACD'], self.data['Signal'], self.data['Histogram'] = self.calculate_macd()
            elif indicator == 'BOLLINGER_BANDS':
                self.data['Upper_Band'], self.data['Lower_Band'] = self.calculate_bollinger_bands()
            elif indicator == 'STOCHASTIC':
                self.data['%K'], self.data['%D'] = self.calculate_stochastic()

        self.data['Position'] = 0
        self.data['Position'][20:] = np.where(self.data['SMA'][20:] > self.data['close'][20:], 1, -1)
        self.data['Return'] = self.data['close'].pct_change()
        self.data['Strategy_Return'] = self.data['Return'] * self.data['Position'].shift()

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
