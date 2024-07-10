# optimization.py

import pandas as pd
from backtest import backtest_strategy
from strategies import SMACrossoverStrategy, EMACrossoverStrategy

def optimize_strategy(data: pd.DataFrame, strategy_class, param_ranges: dict) -> dict:
    best_params = None
    best_performance = None

    # Unpack the parameter ranges for crossover strategies
    if strategy_class in [SMACrossoverStrategy, EMACrossoverStrategy]:
        fast_range = param_ranges['fast']
        slow_range = param_ranges['slow']

        for fast_param in fast_range:
            for slow_param in slow_range:
                if fast_param >= slow_param:  # Skip invalid pairs
                    continue
                strategy = strategy_class(fast_param, slow_param)
                test_data = strategy.apply(data.copy())
                performance = backtest_strategy(test_data)
                if best_performance is None or performance['total_return'] > best_performance['total_return']:
                    best_performance = performance
                    best_params = {'fast': fast_param, 'slow': slow_param}
    else:
        for param in param_ranges['single']:
            strategy = strategy_class(param)
            test_data = strategy.apply(data.copy())
            performance = backtest_strategy(test_data)
            if best_performance is None or performance['total_return'] > best_performance['total_return']:
                best_performance = performance
                best_params = {'period': param}

    return {'best_params': best_params, 'performance': best_performance}
