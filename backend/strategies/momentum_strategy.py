import logging
import pandas as pd
from backend.strategies.rsi_strategy import RSIStrategy
from backend.indicators.stochastic_indicator import StochasticIndicator
from backend.utils.utility import configure_logging

configure_logging("momentum_strategy")

class MomentumStrategy:
    def __init__(self, data, rsi_params, stochastic_params):
        self.data = data
        self.rsi_strategy = RSIStrategy(data, **rsi_params)
        self.stochastic_indicator = StochasticIndicator(data, **stochastic_params)

    def apply_rsi(self):
        self.data = self.rsi_strategy.calculate_rsi()

    def apply_stochastic(self):
        self.data = self.stochastic_indicator.calculate_stochastic()

    def generate_signals(self):
        self.apply_rsi()
        self.apply_stochastic()

        self.data['Signal'] = 0
        # RSI signals
        self.data.loc[self.data['RSI'] > self.rsi_strategy.RSI_OVERBOUGHT, 'Signal'] = -1
        self.data.loc[self.data['RSI'] < self.rsi_strategy.RSI_OVERSOLD, 'Signal'] = 1

        # Stochastic signals
        self.data.loc[self.data['%K'] > 80, 'Signal'] = -1
        self.data.loc[self.data['%K'] < 20, 'Signal'] = 1

        # Combine RSI and Stochastic signals
        self.data['Combined_Signal'] = self.data['Signal']
        logging.info(f"Combined Signal: {self.data['Combined_Signal'].value_counts()}")
        

    def backtest(self):
        logging.info(f"Analyzing the backtest...")        
        self.generate_signals()
        self.data['Position'] = self.data['Combined_Signal'].shift()
        self.data['Return'] = self.data['close'].pct_change()
        self.data['Strategy_Return'] = self.data['Return'] * self.data['Position']
        total_return = self.data['Strategy_Return'].sum()
        num_trades = self.data['Position'].abs().sum()
        win_rate = (self.data['Strategy_Return'] > 0).mean()
        
        return {
        'total_return': total_return,
        'num_trades': num_trades,
        'win_rate': win_rate,
        'data': self.data
        }
