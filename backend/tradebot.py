import logging
import time
from threading import Thread

from backend import variables
from backend.utils import historical
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

from flask import Flask, jsonify

app = Flask(__name__)

class TradeBot:
    def __init__(self):
        self.api = OandaAPI()
        self.control_system = ControlSystem()
        self.running = False
        self.state = None
        self.backtest_results = []
        self.thread = None

    def start(self):
        if not self.running:
            self.running = True
            if self.thread is None or not self.thread.is_alive():
                self.thread = Thread(target=self.run)
                self.thread.start()
            
    def set_state(self, state):
        self.state = state
        self.execute_state_actions()

    def execute_state_actions(self, sec):
        self.sec = sec
        if self.state == 'RED':
            self.enable_manual_trading()
            self.check_account_info()
            self.autofill_database()
            self.sec = 180  # Run every three minutes
        elif self.state == 'GREEN':
            self.download_historical_data()
            self.perform_backtesting()
            self.optimize_parameters()
            self.enable_auto_trading()
            self.integrate_money_management()
            self.sec = 120  # Run every two minutes
        elif self.state == 'YELLOW':
            self.confirm_momentum_strategy()
            self.standby_for_entry()
            self.sec = 30  # Run every half of  minute

    def stop(self):
        if self.running:
            self.running = False
            self.thread.join()

    def run(self):
        if not variables.STATE_MACHINE:
            logging.info("State machine is off. Exiting.")
            return

        while self.running:
            self.execute_state_actions(self.sec)
            time.sleep(self.sec)  # Run every interval minute(s)

    def enable_manual_trading(self):
        logging.info("Manual trading enabled.")
        # Implement manual trading logic if needed.
        # For example, provide an interface to manually input trades.

    def check_account_info(self):
        if (account_info := self.api.get_account_info()):
            logging.info(f"Account Info: {account_info}")
        else:
            logging.error("Failed to retrieve account information.")

    def autofill_database(self):
        # Assume you have a method to autofill the database
        if (success := self.api.autofill_database()):
            logging.info("Database autofilled successfully.")
        else:
            logging.error("Failed to autofill the database.")

    def download_historical_data(self):
        for pair in variables.AUTO_TRADING["TRADE_INSTRUMENTS"]:
            logging.info(f"Analyzing {pair} at {variables.AUTO_TRADING['TRADING_GRANULARITY']} level.")
            granularity = variables.AUTO_TRADING["TRADING_GRANULARITY"]
            count = variables.AUTO_TRADING["TRADING_COUNT"]
            data, message = self.api.get_historical_data(pair, granularity, count)
            if data is not None and not data.empty:
                logging.info(f"Successfully retrieved historical data for {pair}.")
            else:
                logging.error(f"Failed to get historical data again for {pair}: {message}")

    def perform_backtesting(self):
        self.backtest_results = []  # Clear previous results
        for pair in variables.AUTO_TRADING["TRADE_INSTRUMENTS"]:
            granularity = variables.AUTO_TRADING["TRADING_GRANULARITY"]
            count = variables.AUTO_TRADING["TRADING_COUNT"]
            data, message = self.api.get_historical_data(pair, granularity, count)
            if data is not None:
                for strategy_name, params in variables.OPTIMIZATION_RANGES.items():
                    if strategy_class := self.get_strategy_class(strategy_name):
                        param_sets = self.create_param_sets(params)
                        for param_set in param_sets:
                            strategy = strategy_class(data, **param_set)
                            results = strategy.backtest()
                            self.store_backtest_results(pair, strategy_name, param_set, results)
            else:
                logging.error(f"Failed to perform backtesting for {pair}: {message}")

    def optimize_parameters(self):
        for pair in variables.AUTO_TRADING["TRADE_INSTRUMENTS"]:
            granularity = variables.AUTO_TRADING["TRADING_GRANULARITY"]
            count = variables.AUTO_TRADING["TRADING_COUNT"]
            data, message = self.api.get_historical_data(pair, granularity, count)
            if data is not None:
                for strategy_name, params in variables.OPTIMIZATION_RANGES.items():
                    if strategy_class := self.get_strategy_class(strategy_name):
                        param_sets = self.create_param_sets(params)
                        optimizer = OptimizeStrategy(data, strategy_class, param_sets)
                        optimization_results = optimizer.optimize()
                        logging.info(f"Optimized parameters for {pair} using {strategy_name}.")
            else:
                logging.error(f"Failed to optimize parameters for {pair}: {message}")

    def enable_auto_trading(self):
        logging.info("Auto trading enabled.")
        # Implement auto trading logic, e.g., initiate trades based on signals from strategies.

    def integrate_money_management(self):
        logging.info("Money management integrated.")
        # Implement money management rules, such as risk management, position sizing, etc.

    def confirm_momentum_strategy(self):
        logging.info("Momentum strategy confirmed. No entry at the moment.")
        # Implement logic to check momentum strategy without executing trades.

    def standby_for_entry(self):
        logging.info("Standing by to enter position based on momentum strategy.")
        # Implement logic to monitor the market and be ready to execute trades when conditions are met.

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
        results = strategy.backtest()
        self.store_backtest_results(pair, 'Momentum', param_set, results)

        # Implement trading logic based on backtest results
        if results['total_return'] > 0:
            logging.info(f"Positive return for {pair}: Execute trade")
        else:
            logging.info(f"No positive return for {pair}: Do not trade")

    def store_backtest_results(self, pair, strategy_name, param_set, results):
        total_return, num_trades, win_rate = results['total_return'], results['num_trades'], results['win_rate']
        self.backtest_results.append({
            'pair': pair,
            'strategy': strategy_name,
            'params': param_set,
            'total_return': total_return,
            'num_trades': num_trades,
            'win_rate': win_rate
        })
        logging.info(f"Backtest results for {pair} using {strategy_name} with parameters {param_set}:")
        logging.info(f"Total Return: {total_return}, Number of Trades: {num_trades}, Win Rate: {win_rate}")

    def get_strategy_class(self, strategy_name):
        strategy_classes = {
            'RSI': RSIStrategy,
            'SMA': SMAStrategy,
            'EMA': EMAStrategy,
            'SMACrossover': SMACrossoverStrategy,
            'EMACrossover': EMACrossoverStrategy
        }
        return strategy_classes.get(strategy_name)

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

if __name__ == '__main__':
    trade_bot = TradeBot()
    trade_bot.set_state('GREEN')
    trade_bot.start()
    app.run(host='0.0.0.0', port=5000)
