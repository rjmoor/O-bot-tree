import numpy as np
import pandas as pd
from backend.strategies.rsi_strategy import RSIStrategy
from backend.strategies.sma_strategy import SMAStrategy
from backend.strategies.ema_strategy import EMAStrategy
from backend.strategies.sma_crossover_strategy import SMACrossoverStrategy
from backend.strategies.ema_crossover_strategy import EMACrossoverStrategy
from backend.indicators.macd_indicator import MACDIndicator
from backend.indicators.stochastic_indicator import StochasticIndicator
from backend.backtest.backtest_strategy import BacktestStrategy

class OptimizeStrategy:
    def __init__(self, data: pd.DataFrame, strategy_class, param_range: list):
        self.data = data
        self.strategy_class = strategy_class
        self.param_range = param_range

    def optimize(self):
        best_params = None
        best_performance = -np.inf

        if self.strategy_class in [RSIStrategy, SMAStrategy, EMAStrategy]:
            for param_set in self.param_range:
                strategy = self.strategy_class(period=param_set['period'])
                _, total_return, _, _ = strategy.backtest(self.data)
                if total_return > best_performance:
                    best_performance = total_return
                    best_params = param_set
        elif self.strategy_class in [SMACrossoverStrategy, EMACrossoverStrategy]:
            for param_set in self.param_range:
                strategy = self.strategy_class(fast=param_set['fast'], slow=param_set['slow'])
                _, total_return, _, _ = strategy.backtest(self.data)
                if total_return > best_performance:
                    best_performance = total_return
                    best_params = param_set
        elif self.strategy_class in [MACDIndicator, StochasticIndicator]:
            for param_set in self.param_range:
                indicator = self.strategy_class(**param_set)
                data_with_signals = indicator.generate_signal(self.data)
                strategy = BacktestStrategy(data_with_signals, indicators=['MACD'])
                _, total_return, _, _ = strategy.backtest()
                if total_return > best_performance:
                    best_performance = total_return
                    best_params = param_set

        return {'best_params': best_params, 'performance': best_performance}
