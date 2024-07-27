import logging
from typing import Dict

import numpy as np
import pandas as pd

from backend.utils.utility import configure_logging, get_strategy_class


class CombinedStrategy:
    configure_logging("comb_strat")
    def __init__(self, data: pd.DataFrame, param_sets: Dict[str, Dict[str, int]]):
        self.data = data
        self.param_sets = param_sets
        self.strategies = []
        logging.info(f"Backtesting combined strategies with parameters: {param_sets}")
        for strategy_name, params in param_sets.items():
            if (strategy_class := get_strategy_class(strategy_name)):
                self.strategies.append(strategy_class(self.data, **params))
                logging.info(f"Added strategy: {strategy_name} with parameters: {params}")

    def backtest(self):
        for strategy in self.strategies:
            self.data = strategy.generate_signals(self.data)
        
        self.data['Position'] = self.data.apply(self.combine_signals, axis=1)
        self.data['Return'] = self.data['close'].pct_change()
        self.data['Strategy_Return'] = self.data['Return'] * self.data['Position']
        total_return = self.data['Strategy_Return'].sum()
        num_trades = self.data['Position'].abs().sum()
        win_rate = (self.data['Strategy_Return'] > 0).mean()
        logging.info(f"Backtested combined strategies with total return: {total_return}, number of trades: {num_trades}, win rate: {win_rate}")

        return self.data, total_return, num_trades, win_rate

    def combine_signals(self, row):
        combined_signal = sum(row.get(strategy.signal_column, 0) for strategy in self.strategies)
        combined_signal += row.get(self.strategies.signal_column, 0)
        return np.sign(combined_signal)
