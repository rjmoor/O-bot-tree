import pandas as pd
import numpy as np

class BreakoutStrategy:
    def __init__(self, data, ema_params, sma_params, bb_params):
        self.data = data
        self.ema_params = ema_params
        self.sma_params = sma_params
        self.bb_params = bb_params

    def calculate_ema(self):
        self.data['EMA'] = self.data['close'].ewm(span=self.ema_params['period'], adjust=False).mean()

    def calculate_sma(self):
        self.data['SMA'] = self.data['close'].rolling(window=self.sma_params['period']).mean()

    def calculate_bb(self):
        self.data['SMA'] = self.data['close'].rolling(window=self.bb_params['period']).mean()
        self.data['STD'] = self.data['close'].rolling(window=self.bb_params['period']).std()
        self.data['Upper_Band'] = self.data['SMA'] + (self.data['STD'] * self.bb_params['std_dev'])
        self.data['Lower_Band'] = self.data['SMA'] - (self.data['STD'] * self.bb_params['std_dev'])

    def generate_signals(self):
        self.calculate_ema()
        self.calculate_sma()
        self.calculate_bb()
        self.data['Signal'] = 0
        self.data['Signal'] = np.where(self.data['close'] > self.data['Upper_Band'], 1, np.where(self.data['close'] < self.data['Lower_Band'], -1, 0))

    def backtest(self):
        self.generate_signals()
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
