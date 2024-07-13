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

        return self.data, total_return, num_trades, win_rate
    
    def calculate_ema(self, data: pd.DataFrame) -> pd.DataFrame:
        data['EMA'] = data['close'].ewm(span=self.period, adjust=False).mean()
        return data

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        data = self.calculate_ema(data)
        data['Signal'] = 0
        data['Signal'] = data['close'] > data['EMA']
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
