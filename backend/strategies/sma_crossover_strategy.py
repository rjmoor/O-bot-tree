import pandas as pd
import numpy as np

class SMACrossoverStrategy:
    def __init__(self, fast_period=12, slow_period=26):
        self.fast_period = fast_period
        self.slow_period = slow_period

    def apply_sma_crossover(self, data: pd.DataFrame) -> pd.DataFrame:
        # Calculate fast SMA
        data['SMA_fast'] = data['close'].rolling(window=self.fast_period, min_periods=1).mean()
        # Calculate slow SMA
        data['SMA_slow'] = data['close'].rolling(window=self.slow_period, min_periods=1).mean()
        # Generate signals
        data['Signal'] = 0
        data['Signal'] = np.where(data['SMA_fast'] > data['SMA_slow'], 1, -1)
        data['Position'] = data['Signal'].shift(1)
        return data

    def backtest(self, data: pd.DataFrame) -> (pd.DataFrame, float, int, float):
        data = self.apply_sma_crossover(data)
        data['Strategy_Return'] = data['Position'] * data['close'].pct_change()
        data['Cumulative_Return'] = (1 + data['Strategy_Return']).cumprod() - 1
        total_return = data['Cumulative_Return'].iloc[-1]
        num_trades = data['Position'].diff().fillna(0).abs().sum()
        win_rate = (data['Strategy_Return'] > 0).mean()
        return data, total_return, num_trades, win_rate

    def optimize(self, data: pd.DataFrame, fast_range: list, slow_range: list) -> dict:
        best_params = None
        best_performance = -float('inf')
        for fast in fast_range:
            for slow in slow_range:
                if fast < slow:
                    self.fast_period = fast
                    self.slow_period = slow
                    _, total_return, _, _ = self.backtest(data)
                    if total_return > best_performance:
                        best_performance = total_return
                        best_params = {'fast': fast, 'slow': slow}
        return {'best_params': best_params, 'performance': best_performance}
