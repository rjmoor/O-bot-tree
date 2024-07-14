import itertools
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple


class OptimizeStrategy:
    def __init__(
        self,
        data: pd.DataFrame,
        strategy_classes: List[type],
        param_ranges: Dict[str, Dict[str, List[int]]],
    ):
        self.data = data
        self.strategy_classes = strategy_classes
        self.param_ranges = param_ranges

    def optimize(self) -> List[Tuple[Dict[str, Dict[str, int]], float, int, float]]:
        best_combinations = []

        # Optimize each strategy individually
        individual_best_params = {}
        for strategy_class in self.strategy_classes:
            best_params, best_performance, best_results = (
                self.optimize_individual_strategy(strategy_class)
            )
            individual_best_params[strategy_class.__name__] = (
                best_params,
                best_performance,
                best_results,
            )

        # Generate combinations of the best parameters
        combination_params = self.create_combinations(individual_best_params)

        # Backtest each combination and evaluate performance
        combination_results = []
        for param_set in combination_params:
            try:
                combined_strategy = CombinedStrategy(self.data, param_set)
                results, total_return, num_trades, win_rate = (
                    combined_strategy.backtest()
                )
                performance = self.evaluate_performance(
                    total_return, num_trades, win_rate
                )
                combination_results.append(
                    (
                        param_set,
                        performance,
                        total_return,
                        num_trades,
                        win_rate,
                        results,
                    )
                )
            except Exception as e:
                logging.error(
                    f"Error during combination optimization with parameters {param_set}: {str(e)}"
                )

        # Sort and select top 3 combinations
        combination_results.sort(key=lambda x: x[1], reverse=True)
        best_combinations = combination_results[:3]

        return best_combinations

    def optimize_individual_strategy(
        self, strategy_class
    ) -> Tuple[Dict[str, int], float, List]:
        best_params = None
        best_performance = float("-inf")
        best_results = None

        param_grid = self.create_param_grid(self.param_ranges[strategy_class.__name__])

        for param_set in param_grid:
            try:
                strategy = strategy_class(self.data, **param_set)
                results, total_return, num_trades, win_rate = strategy.backtest()
                performance = self.evaluate_performance(
                    total_return, num_trades, win_rate
                )

                if performance > best_performance:
                    best_performance = performance
                    best_params = param_set
                    best_results = (results, total_return, num_trades, win_rate)

            except Exception as e:
                logging.error(
                    f"Error during optimization with parameters {param_set}: {str(e)}"
                )

        return best_params, best_performance, best_results

    def create_param_grid(
        self, param_ranges: Dict[str, List[int]]
    ) -> List[Dict[str, int]]:
        keys, values = zip(*param_ranges.items())
        param_grid = [dict(zip(keys, v)) for v in itertools.product(*values)]
        return param_grid

    def create_combinations(
        self, individual_best_params: Dict[str, Tuple[Dict[str, int], float, List]]
    ) -> List[Dict[str, Dict[str, int]]]:
        combined_params = []
        param_names = list(individual_best_params.keys())
        param_values = [
            individual_best_params[param_name][0] for param_name in param_names
        ]
        for combination in itertools.product(*param_values):
            combined_params.append(dict(zip(param_names, combination)))
        return combined_params

    def evaluate_performance(
        self, total_return: float, num_trades: int, win_rate: float
    ) -> float:
        # Define a performance metric combining total return, number of trades, and win rate
        return total_return * win_rate * num_trades
