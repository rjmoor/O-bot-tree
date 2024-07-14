class CombinedStrategy:
    def __init__(self, data: pd.DataFrame, param_sets: Dict[str, Dict[str, int]]):
        self.data = data
        self.param_sets = param_sets
        self.strategies = []
        for strategy_name, params in param_sets.items():
            strategy_class = get_strategy_class(strategy_name)
            if strategy_class:
                self.strategies.append(strategy_class(self.data, **params))

    def backtest(self):
        for strategy in self.strategies:
            self.data = strategy.generate_signals(self.data)
        
        self.data['Position'] = self.data.apply(self.combine_signals, axis=1)
        self.data['Return'] = self.data['close'].pct_change()
        self.data['Strategy_Return'] = self.data['Return'] * self.data['Position']
        total_return = self.data['Strategy_Return'].sum()
        num_trades = self.data['Position'].abs().sum()
        win_rate = (self.data['Strategy_Return'] > 0).mean()

        return self.data, total_return, num_trades, win_rate

    def combine_signals(self, row):
        combined_signal = 0
        for strategy in self.strategies:
            combined_signal += row.get(strategy.signal_column, 0)
        return np.sign(combined_signal)
