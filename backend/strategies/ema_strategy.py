import pandas as pd

class EMAStrategy:
    def __init__(self, data, Fast_Period, Slow_Period):
        self.data = data
        self.Fast_Period = Fast_Period
        self.Slow_Period = Slow_Period

    def calculate_ema(self):
        self.data['EMA_Fast'] = self.data['close'].ewm(span=self.Fast_Period, adjust=False).mean()
        self.data['EMA_Slow'] = self.data['close'].ewm(span=self.Slow_Period, adjust=False).mean()
        return self.data

    def generate_signal(self):
        self.data = self.calculate_ema()
        self.data['Signal'] = 0
        self.data.loc[self.data['EMA_Fast'] > self.data['EMA_Slow'], 'Signal'] = 1
        self.data.loc[self.data['EMA_Fast'] < self.data['EMA_Slow'], 'Signal'] = -1
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