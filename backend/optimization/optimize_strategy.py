class OptimizeStrategy:
    def __init__(self, data, strategy_class, param_sets):
        self.data = data
        self.strategy_class = strategy_class
        self.param_sets = param_sets

    def optimize(self):
        best_params = None
        best_performance = -float('inf')

        for param_set in self.param_sets:
            try:
                # Convert parameters to integer
                param_set = {key: int(value) for key, value in param_set.items() if isinstance(value, (int, str, float))}
                strategy = self.strategy_class(self.data, **param_set)
                _, total_return, _, _ = strategy.backtest()

                if total_return > best_performance:
                    best_performance = total_return
                    best_params = param_set
            except Exception as e:
                print(f"Error during optimization with parameters {param_set}: {e}")

        return {
            'best_params': best_params,
            'performance': best_performance
        }
