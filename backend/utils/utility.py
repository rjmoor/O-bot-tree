# utility.py
import pandas as pd
from datetime import datetime, timedelta, timezone
import defs
import variables

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
