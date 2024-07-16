import pandas as pd
import logging
from datetime import datetime
import backend.defs as defs
import backend.variables as variables

def convert_to_dataframe(data):
    df = pd.DataFrame(data)
    df['time'] = pd.to_datetime(df['time'])
    return df

# Used for backtesting and trading bot helper functions
def fetch_instruments(self):
    url = f"{defs.OANDA_URL}/accounts/{defs.ACCOUNT_ID}/instruments"
    response = self._request_with_retries("GET", url, headers={'Authorization': f'Bearer {defs.API_KEY}'})
    return response.status_code, response.json()

# utility.py (Add state machine functions)
def transition_state(new_state):
    global current_state
    if new_state in [variables.STATE_RED, variables.STATE_YELLOW, variables.STATE_GREEN]:
        current_state = new_state

def configure_logging():
    log_directory = '../logs'
    log_filename = f"{log_directory}/Data_{datetime.now().strftime('%Y-%m-%d')}.log"
    logging.basicConfig(
        filename=log_filename,
        level=logging.INFO,
        format="%(asctime)s %(levelname)s:%(message)s",
    )
    logging.getLogger().addHandler(logging.StreamHandler())  # Optional: To also log to console
    logging.info("Logging configured successfully.")
