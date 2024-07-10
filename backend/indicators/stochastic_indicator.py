# stochastic_indicator.py

import pandas as pd

class StochasticIndicator:
    def __init__(self, k_window=14, d_window=3):
        self.k_window = k_window
        self.d_window = d_window

    def calculate_stochastic(self, data: pd.DataFrame) -> pd.DataFrame:
        data['Lowest_Low'] = data['low'].rolling(window=self.k_window).min()
        data['Highest_High'] = data['high'].rolling(window=self.k_window).max()
        data['%K'] = 100 * ((data['close'] - data['Lowest_Low']) / (data['Highest_High'] - data['Lowest_Low']))
        data['%D'] = data['%K'].rolling(window=self.d_window).mean()
        return data

    def generate_signal(self, data: pd.DataFrame) -> pd.DataFrame:
        data = self.calculate_stochastic(data)
        data['Stochastic_Signal'] = 0
        # Generate signals: 1 for buy, -1 for sell, 0 for no signal
        data['Stochastic_Signal'] = data.apply(
            lambda row: 1 if row['%K'] > row['%D'] and row['%K'] < 20 else
                        (-1 if row['%K'] < row['%D'] and row['%K'] > 80 else 0), axis=1
        )
        return data

    def get_signal_state(self, data: pd.DataFrame) -> str:
        if 'Stochastic_Signal' not in data.columns:
            data = self.generate_signal(data)

        latest_signal = data.iloc[-1]['Stochastic_Signal']
        if latest_signal == 1:
            return 'green'
        elif latest_signal == -1:
            return 'red'
        else:
            return 'yellow'
