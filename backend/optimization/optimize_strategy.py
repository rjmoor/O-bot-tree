class OptimizeStrategy:
    def __init__(self, data, strategy_class, param_ranges):
        self.data = data
        self.strategy_class = strategy_class
        self.param_ranges = param_ranges

    def optimize(self):
        best_params = None
        best_performance = float('-inf')
        best_report = None

        for param_set in self.param_ranges:
            strategy = self.strategy_class(self.data, **param_set)
            report = strategy.backtest()
            performance = report['total_return']
            if performance > best_performance:
                best_performance = performance
                best_params = param_set
                best_report = report

        return {
            'best_params': best_params,
            'performance': best_performance,
            'report': best_report
        }
