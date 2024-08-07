import logging
from datetime import datetime
import pandas as pd
from backend.strategies.momentum_strategy import MomentumStrategy
import backend.variables as variables
from backend.oanda_api.oanda_api import OandaAPI
from backend.utils.utility import configure_logging

configure_logging("control_system")

class ControlSystem:
    
    def __init__(self):
        self.api = OandaAPI()

    def get_historical_data(self, instrument, granularity):
        data, message = self.api.get_historical_data(instrument, granularity, 5000)
        if data is not None:
            logging.info(f"Retrieved historical data for {instrument}: {data.head()}")
            logging.debug(f"DataFrame columns for {instrument}: {data.columns}")

            if 'time' not in data.columns:
                logging.error(f"Missing 'time' column in the historical data for {instrument}.")
                logging.error(f"Data columns: {data.columns}")
                return None

            data['time'] = pd.to_datetime(data['time'])
            data = data.sort_values(by='time', ascending=False)
            return data
        else:
            logging.error(f"Failed to retrieve data: {message}")
            return None

    def analyze_instrument(self, instrument):
        logging.info(f"Analyzing {instrument} at monthly level.")
        monthly_data = self.get_historical_data(instrument, 'M')
        if monthly_data is not None:
            strategy = MomentumStrategy(monthly_data, variables.RSI_PARAMS, variables.STOCHASTIC_PARAMS)
            monthly_report = strategy.backtest()
            if monthly_report['total_return'] > 0 and monthly_report['win_rate'] > 0.5:
                variables.current_state = variables.STATE_GREEN
                logging.info(f"State set to GREEN for {instrument} based on monthly analysis.")
                
                logging.info(f"Analyzing {instrument} at daily level.")
                daily_data = self.get_historical_data(instrument, 'D')
                if daily_data is not None:
                    strategy = MomentumStrategy(daily_data, variables.RSI_PARAMS, variables.STOCHASTIC_PARAMS)
                    daily_report = strategy.backtest()
                    if daily_report['total_return'] > 0 and daily_report['win_rate'] > 0.5:
                        variables.current_state = variables.STATE_GREEN
                        logging.info(f"State set to GREEN for {instrument} based on daily analysis.")
                        
                        logging.info(f"Analyzing {instrument} at minute level.")
                        minute_data = self.get_historical_data(instrument, 'M1')
                        if minute_data is not None:
                            strategy = MomentumStrategy(minute_data, variables.RSI_PARAMS, variables.STOCHASTIC_PARAMS)
                            minute_report = strategy.backtest()
                            if minute_report['total_return'] > 0 and minute_report['win_rate'] > 0.5:
                                logging.info(f"Executing trade for {instrument} based on minute analysis.")
                                # Execute trade logic here
                            else:
                                variables.current_state = variables.STATE_YELLOW
                                logging.info(f"State set to YELLOW for {instrument} based on minute analysis.")
                        else:
                            variables.current_state = variables.STATE_YELLOW
                            logging.info(f"State set to YELLOW for {instrument} based on daily analysis.")
                    else:
                        variables.current_state = variables.STATE_YELLOW
                        logging.info(f"State set to YELLOW for {instrument} based on daily analysis.")
                else:
                    variables.current_state = variables.STATE_RED
                    logging.info(f"State set to RED for {instrument} based on daily analysis.")
            else:
                variables.current_state = variables.STATE_RED
                logging.info(f"State set to RED for {instrument} based on monthly analysis.")

    def run_analysis(self):
        instruments = variables.AUTO_TRADING["TRADE_INSTRUMENTS"]
        for instrument in instruments:
            self.analyze_instrument(instrument)

if __name__ == "__main__":
    control_system = ControlSystem()
    control_system.run_analysis()
