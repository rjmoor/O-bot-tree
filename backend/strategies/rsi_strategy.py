import pandas as pd

class RSIStrategy:
    def __init__(self, period=14, overbought=70, oversold=30):
        self.period = period
        self.overbought = overbought
        self.oversold = oversold

    def calculate_rsi(self, data: pd.DataFrame) -> pd.DataFrame:
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.period).mean()
        rs = gain / loss
        data['RSI'] = 100 - (100 / (1 + rs))
        return data

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        data = self.calculate_rsi(data)
        data['Signal'] = 0
        data['Signal'][data['RSI'] > self.overbought] = -1
        data['Signal'][data['RSI'] < self.oversold] = 1
        data['Position'] = data['Signal'].shift(1)
        return data

    def backtest(self, data: pd.DataFrame) -> (pd.DataFrame, float, int, float):
        data = self.generate_signals(data)
        data['Strategy_Return'] = data['Position'] * data['close'].pct_change()
        data['Cumulative_Return'] = (1 + data['Strategy_Return']).cumprod() - 1
        total_return = data['Cumulative_Return'].iloc[-1]
        num_trades = data['Position'].diff().fillna(0).abs().sum()
        win_rate = (data['Strategy_Return'] > 0).mean()
        return data, total_return, num_trades, win_rate

    def optimize(self, data: pd.DataFrame, param_range: list) -> dict:
        best_params = None
        best_performance = -float('inf')
        for param in param_range:
            self.period = param
            _, total_return, _, _ = self.backtest(data)
            if total_return > best_performance:
                best_performance = total_return
                best_params = {'period': param}
        return {'best_params': best_params, 'performance': best_performance}
