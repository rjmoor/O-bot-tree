import logging
import time
from threading import Thread

from backend import variables
from backend.backtest.backtest_strategy import BacktestStrategy
from backend.control.control_system import ControlSystem
from backend.indicators.macd_indicator import MACDIndicator
from backend.indicators.stochastic_indicator import StochasticIndicator
from backend.indicators.bollinger_bands_indicator import BollingerBandsIndicator
from backend.oanda_api.oanda_api import OandaAPI
from backend.optimization.optimize_strategy import OptimizeStrategy
from backend.strategies.ema_crossover_strategy import EMACrossoverStrategy
from backend.strategies.ema_strategy import EMAStrategy
from backend.strategies.momentum_strategy import MomentumStrategy
from backend.strategies.rsi_strategy import RSIStrategy
from backend.strategies.sma_crossover_strategy import SMACrossoverStrategy
from backend.strategies.sma_strategy import SMAStrategy
from backend.utils.utility import configure_logging


class TradeBot:
    def __init__(self):
        self.api = OandaAPI()
        self.running = False

    def start(self):
        if not self.running:
            self.running = True
            self.thread = Thread(target=self.run)
            self.thread.start()
            
    def set_state(self, state):
        self.state = state
        self.execute_state_actions()

    def execute_state_actions(self):
        if self.state == 'RED':
            self.enable_manual_trading()
            self.check_account_info()
            self.autofill_database()
        elif self.state == 'GREEN':
            self.download_historical_data()
            self.perform_backtesting()
            self.optimize_parameters()
            self.enable_auto_trading()
            self.integrate_money_management()
        elif self.state == 'YELLOW':
            self.confirm_momentum_strategy()
            self.standby_for_entry()

    def stop(self):
        if self.running:
            self.running = False
            self.thread.join()

    def run(self):
        if not variables.STATE_MACHINE:
            logging.info("State machine is off. Exiting.")
            return

        while self.running:
            for pair in variables.LIVE_TRADING["TRADE_INSTRUMENTS"]:
                granularity = variables.LIVE_TRADING["TRADING_GRANULARITY"]
                count = variables.LIVE_TRADING["TRADING_COUNT"]
                data, message = self.api.get_historical_data(pair, granularity, count)
                if data is not None:
                    for strategy_name, params in variables.OPTIMIZATION_RANGES.items():
                        strategy_class = self.get_strategy_class(strategy_name)
                        if strategy_class:
                            param_sets = self.create_param_sets(params)
                            
                            for param_set in param_sets:
                                optimizer = OptimizeStrategy(data, strategy_class, [param_set])
                                optimization_results = optimizer.optimize()
                                self.execute_trade(pair, optimization_results, data, param_set)
                else:
                    logging.error(f"Failed to get historical data for {pair}: {message}")
            time.sleep(3600)  # Run every hour

    def execute_trade(self, pair, optimization_results, data, param_set):
        rsi_params = {
            'RSI_PERIOD': param_set.get('RSI_PERIOD', 14),
            'RSI_OVERBOUGHT': param_set.get('RSI_OVERBOUGHT', 70),
            'RSI_OVERSOLD': param_set.get('RSI_OVERSOLD', 30)
        }
        stochastic_params = {
            'k_period': param_set.get('STOCHASTIC_K_PERIOD', 14),
            'd_period': param_set.get('STOCHASTIC_D_PERIOD', 3)
        }

        strategy = MomentumStrategy(data, rsi_params, stochastic_params)
        _, total_return, num_trades, win_rate = strategy.backtest()

        # Implement trading logic based on backtest results
        if total_return > '0':
            logging.info(f"Positive return for {pair}: Execute trade")
        else:
            logging.info(f"No positive return for {pair}: Do not trade")

    def get_strategy_class(self, strategy_name):
        strategy_classes = {
            'RSI': RSIStrategy,
            'SMA': SMAStrategy,
            'EMA': EMAStrategy,
            'SMACrossover': SMACrossoverStrategy,
            'EMACrossover': EMACrossoverStrategy
        }
        return strategy_classes.get(strategy_name, None)

    def create_param_sets(self, params):
        if 'RSI_PERIOD' in params:
            return [{'RSI_PERIOD': period, 'RSI_OVERBOUGHT': overbought, 'RSI_OVERSOLD': oversold}
                    for period in params['RSI_PERIOD']
                    for overbought in params['RSI_OVERBOUGHT']
                    for oversold in params['RSI_OVERSOLD']]
        elif 'Fast_Period' in params and 'Slow_Period' in params:
            return [{'Fast_Period': fast, 'Slow_Period': slow}
                    for fast in params['Fast_Period']
                    for slow in params['Slow_Period']]
        elif 'STOCHASTIC_K_PERIOD' in params:
            return [{'STOCHASTIC_K_PERIOD': k_period, 'STOCHASTIC_D_PERIOD': d_period}
                    for k_period in params['STOCHASTIC_K_PERIOD']
                    for d_period in params['STOCHASTIC_D_PERIOD']]
        elif 'BOLLINGER_BANDS' in params:
            return [{'BOLLINGER_BANDS_PERIOD': period, 'BOLLINGER_BANDS_STD_DEV': std_dev}
                    for period in params['BOLLINGER_BANDS_PERIOD']
                    for std_dev in params['BOLLINGER_BANDS_STD_DEV']]
        else:
            return [{}]  # Default empty parameter set for strategies without additional params

    def enable_manual_trading(self):
        print("Manual trading enabled")

    def check_account_info(self):
        print("Checking account information")

    def autofill_database(self):
        print("Autofilling database")

    def download_historical_data(self):
        print("Downloading historical data")

    def perform_backtesting(self):
        print("Performing backtesting")

    def optimize_parameters(self):
        print("Optimizing parameters")

    def enable_auto_trading(self):
        print("Auto trading enabled")

    def integrate_money_management(self):
        print("Money management integrated")

    def confirm_momentum_strategy(self):
        print("Momentum strategy confirmed")

    def standby_for_entry(self):
        print("Standing by to enter position")