import pandas as pd

class MACDStrategy:
    def __init__(self, data, fast_period=12, slow_period=26, signal_period=9):
        self.data = data
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period

    def calculate_macd(self):
        self.data['EMA_fast'] = self.data['close'].ewm(span=self.fast_period, adjust=False).mean()
        self.data['EMA_slow'] = self.data['close'].ewm(span=self.slow_period, adjust=False).mean()
        self.data['MACD'] = self.data['EMA_fast'] - self.data['EMA_slow']
        self.data['Signal'] = self.data['MACD'].ewm(span=self.signal_period, adjust=False).mean()
        self.data['Histogram'] = self.data['MACD'] - self.data['Signal']

    def generate_signals(self):
        self.data['Signal'] = 0
        self.data['Signal'][self.data['MACD'] > self.data['Signal']] = 1
        self.data['Signal'][self.data['MACD'] < self.data['Signal']] = -1

    def backtest(self):
        self.calculate_macd()
        self.generate_signals()
        self.data['Position'] = self.data['Signal'].shift()
        self.data['Return'] = self.data['close'].pct_change()
        self.data['Strategy_Return'] = self.data['Return'] * self.data['Position']
        
        total_return = self.data['Strategy_Return'].sum()
        num_trades = self.data['Position'].abs().sum()
        win_rate = (self.data['Strategy_Return'] > 0).mean()

        return self.data, total_return, num_trades, win_rate
