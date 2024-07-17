import logging 
import pandas as pd
import numpy as np
from backend.utils.utility import configure_logging

class BacktestStrategy:
    configure_logging("back_strat")
    def __init__(self, data, indicators):
        self.data = data
        self.indicators = indicators
        logging.info(f"Backtesting strategy with indicators: {indicators}")

    def generate_signals(self):
        # Assuming generate_signals method generates buy/sell signals based on indicators
        for indicator in self.indicators:
            if indicator == 'SMA':
                self.data['SMA'] = self.data['close'].rolling(window=14).mean()
                self.data['Signal'] = 0
                self.data['Signal'][14:] = np.where(self.data['close'][14:] > self.data['SMA'][14:], 1, -1)
            elif indicator == 'EMA':
                self.data['EMA'] = self.data['close'].ewm(span=14, adjust=False).mean()
                self.data['Signal'] = 0
                self.data['Signal'][14:] = np.where(self.data['close'][14:] > self.data['EMA'][14:], 1, -1)
            elif indicator == 'RSI':
                delta = self.data['close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                RS = gain / loss
                self.data['RSI'] = 100 - (100 / (1 + RS))
                self.data['Signal'] = 0
                self.data['Signal'][14:] = np.where(self.data['RSI'][14:] < 30, 1, np.where(self.data['RSI'][14:] > 70, -1, 0))
            elif indicator == 'MACD':
                exp1 = self.data['close'].ewm(span=12, adjust=False).mean()
                exp2 = self.data['close'].ewm(span=26, adjust=False).mean()
                self.data['MACD'] = exp1 - exp2
                self.data['Signal'] = 0
                self.data['Signal'][26:] = np.where(self.data['MACD'][26:] > self.data['MACD'].ewm(span=9, adjust=False).mean(), 1, -1)
            elif indicator == 'BOLLINGER_BANDS':
                self.data['SMA'] = self.data['close'].rolling(window=20).mean()
                self.data['STD'] = self.data['close'].rolling(window=20).std()
                self.data['Upper_Band'] = self.data['SMA'] + (self.data['STD'] * 2)
                self.data['Lower_Band'] = self.data['SMA'] - (self.data['STD'] * 2)
                self.data['Signal'] = 0
                self.data['Signal'][20:] = np.where(self.data['close'][20:] < self.data['Lower_Band'][20:], 1, np.where(self.data['close'][20:] > self.data['Upper_Band'][20:], -1, 0))
            elif indicator == 'STOCHASTIC':
                low_14 = self.data['low'].rolling(window=14).min()
                high_14 = self.data['high'].rolling(window=14).max()
                self.data['%K'] = 100 * ((self.data['close'] - low_14) / (high_14 - low_14))
                self.data['%D'] = self.data['%K'].rolling(window=3).mean()
                self.data['Signal'] = 0
                self.data['Signal'][14:] = np.where(self.data['%K'][14:] > 80, -1, np.where(self.data['%K'][14:] < 20, 1, 0))
                        

    def backtest(self):
        self.generate_signals()
        self.data['Position'] = self.data['Signal'].shift()
        self.data['Return'] = self.data['close'].pct_change()
        self.data['Strategy_Return'] = self.data['Return'] * self.data['Position']
        total_return = self.data['Strategy_Return'].sum()
        num_trades = self.data['Position'].abs().sum()
        win_rate = (self.data['Strategy_Return'] > 0).mean()

        report = {
            'total_return': total_return,
            'num_trades': num_trades,
            'win_rate': win_rate,
            'data': self.data
        }
        return report

