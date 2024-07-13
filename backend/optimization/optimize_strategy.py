import pandas as pd


class OptimizeStrategy:
    def __init__(self, data: pd.DataFrame, strategy_class, param_range: dict):
        self.data = data
        self.strategy_class = strategy_class
        self.param_range = param_range

    def optimize(self):
        best_params = None
        best_performance = -float('inf')

        # Example optimization loop for a single parameter
        for param in self.param_range['single']:
            strategy = self.strategy_class(period=param)
            _, total_return, _, _ = strategy.backtest(self.data)
            if total_return > best_performance:
                best_performance = total_return
                best_params = {'period': param}

        return {'best_params': best_params, 'performance': best_performance}
