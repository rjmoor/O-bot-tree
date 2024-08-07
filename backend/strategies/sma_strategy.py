import pandas as pd

class SMAStrategy:
    def __init__(self, data, Fast_Period, Slow_Period):
        self.data = data
        self.Fast_Period = Fast_Period
        self.Slow_Period = Slow_Period

    def calculate_sma(self):
        self.data['SMA_Fast'] = self.data['close'].rolling(window=self.Fast_Period).mean()
        self.data['SMA_Slow'] = self.data['close'].rolling(window=self.Slow_Period).mean()
        return self.data

    def generate_signal(self):
        self.data = self.calculate_sma()
        self.data['Signal'] = 0
        self.data.loc[self.data['SMA_Fast'] > self.data['SMA_Slow'], 'Signal'] = 1
        self.data.loc[self.data['SMA_Fast'] < self.data['SMA_Slow'], 'Signal'] = -1
        return self.data

    def backtest(self):
        self.data = self.generate_signal()
        self.data['Position'] = self.data['Signal'].shift()
        self.data['Return'] = self.data['close'].pct_change()
        self.data['Strategy_Return'] = self.data['Return'] * self.data['Position']
        total_return = self.data['Strategy_Return'].sum()
        num_trades = self.data['Position'].abs().sum()
        win_rate = (self.data['Strategy_Return'] > 0).mean()

        return {
            'total_return': total_return,
            'num_trades': num_trades,
            'win_rate': win_rate,
            'data': self.data
        }
