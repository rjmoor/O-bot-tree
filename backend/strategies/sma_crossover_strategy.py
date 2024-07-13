import pandas as pd

class SMACrossoverStrategy:
    def __init__(self, data, fast_period=10, slow_period=30):
        self.data = data
        self.fast_period = fast_period
        self.slow_period = slow_period

    def calculate_sma(self):
        self.data['SMA_Fast'] = self.data['close'].rolling(window=self.fast_period).mean()
        self.data['SMA_Slow'] = self.data['close'].rolling(window=self.slow_period).mean()

    def generate_signals(self):
        self.data['Signal'] = 0
        self.data['Signal'][self.data['SMA_Fast'] > self.data['SMA_Slow']] = 1
        self.data['Signal'][self.data['SMA_Fast'] < self.data['SMA_Slow']] = -1

    def backtest(self):
        self.calculate_sma()
        self.generate_signals()
        self.data['Position'] = self.data['Signal'].shift()
        self.data['Return'] = self.data['close'].pct_change()
        self.data['Strategy_Return'] = self.data['Return'] * self.data['Position']
        
        total_return = self.data['Strategy_Return'].sum()
        num_trades = self.data['Position'].abs().sum()
        win_rate = (self.data['Strategy_Return'] > 0).mean()

        return self.data, total_return, num_trades, win_rate
