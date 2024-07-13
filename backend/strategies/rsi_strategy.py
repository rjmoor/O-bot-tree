import pandas as pd

class RSIStrategy:
    def __init__(self, data, RSI_PERIOD, RSI_OVERBOUGHT, RSI_OVERSOLD):
        self.data = data
        self.RSI_PERIOD = int(RSI_PERIOD)
        self.RSI_OVERBOUGHT = int(RSI_OVERBOUGHT)
        self.RSI_OVERSOLD = int(RSI_OVERSOLD)

    def calculate_rsi(self):
        delta = self.data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.RSI_PERIOD).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.RSI_PERIOD).mean()
        rs = gain / loss
        self.data['RSI'] = 100 - (100 / (1 + rs))
        return self.data

    def generate_signal(self):
        self.data = self.calculate_rsi()
        self.data['Signal'] = 0
        self.data['Signal'][self.data['RSI'] > self.RSI_OVERBOUGHT] = -1
        self.data['Signal'][self.data['RSI'] < self.RSI_OVERSOLD] = 1
        self.data['Position'] = self.data['Signal'].shift()
        return self.data

    def backtest(self):
        self.data = self.generate_signal()
        self.data['Strategy'] = self.data['Position'].shift() * self.data['close'].pct_change()
        self.data['Strategy'] = self.data['Strategy'].fillna(0)
        self.data['Cumulative_Return'] = (1 + self.data['Strategy']).cumprod() - 1
        total_return = self.data['Cumulative_Return'].iloc[-1]
        num_trades = self.data['Position'].diff().fillna(0).abs().sum() / 2
        win_rate = len(self.data[self.data['Strategy'] > 0]) / num_trades if num_trades != 0 else 0
        return self.data, total_return, num_trades, win_rate
