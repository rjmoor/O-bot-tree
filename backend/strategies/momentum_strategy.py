import pandas as pd

class MomentumStrategy:
    def __init__(self, data: pd.DataFrame):
        self.data = data

    def apply_rsi(self, period=14):
        delta = self.data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        self.data['RSI'] = 100 - (100 / (1 + rs))

    def apply_stochastic(self, k_period=14, d_period=3):
        self.data['L14'] = self.data['low'].rolling(window=k_period).min()
        self.data['H14'] = self.data['high'].rolling(window=k_period).max()
        self.data['%K'] = 100 * ((self.data['close'] - self.data['L14']) / (self.data['H14'] - self.data['L14']))
        self.data['%D'] = self.data['%K'].rolling(window=d_period).mean()

    def generate_signals(self, indicator='RSI', rsi_overbought=70, rsi_oversold=30, stochastic_overbought=80, stochastic_oversold=20):
        self.data['Signal'] = 0
        if indicator == 'RSI':
            self.data['Signal'][self.data['RSI'] > rsi_overbought] = -1
            self.data['Signal'][self.data['RSI'] < rsi_oversold] = 1
        elif indicator == 'Stochastic':
            self.data['Signal'][self.data['%K'] > stochastic_overbought] = -1
            self.data['Signal'][self.data['%K'] < stochastic_oversold] = 1

    def backtest(self):
        self.data['Position'] = self.data['Signal'].shift(1)
        self.data['Strategy_Return'] = self.data['Position'] * self.data['close'].pct_change()
        self.data['Cumulative_Return'] = (1 + self.data['Strategy_Return']).cumprod() - 1
        total_return = self.data['Cumulative_Return'].iloc[-1]
        num_trades = self.data['Position'].diff().fillna(0).abs().sum()
        win_rate = (self.data['Strategy_Return'] > 0).mean()
        return self.data, total_return, num_trades, win_rate
