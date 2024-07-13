import pandas as pd

class EMACrossoverStrategy:
    def __init__(self, data, fast_period=10, slow_period=30):
        self.data = data
        self.fast_period = fast_period
        self.slow_period = slow_period

    def calculate_ema(self):
        self.data['EMA_Fast'] = self.data['close'].ewm(span=self.fast_period, adjust=False).mean()
        self.data['EMA_Slow'] = self.data['close'].ewm(span=self.slow_period, adjust=False).mean()

    def generate_signals(self):
        self.data['Signal'] = 0
        self.data['Signal'][self.data['EMA_Fast'] > self.data['EMA_Slow']] = 1
        self.data['Signal'][self.data['EMA_Fast'] < self.data['EMA_Slow']] = -1

    def backtest(self):
        self.calculate_ema()
        self.generate_signals()
        self.data['Position'] = self.data['Signal'].shift()
        self.data['Return'] = self.data['close'].pct_change()
        self.data['Strategy_Return'] = self.data['Return'] * self.data['Position']
        
        total_return = self.data['Strategy_Return'].sum()
        num_trades = self.data['Position'].abs().sum()
        win_rate = (self.data['Strategy_Return'] > 0).mean()

        return self.data, total_return, num_trades, win_rate
