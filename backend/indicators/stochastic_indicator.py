import pandas as pd

class StochasticIndicator:
    def __init__(self, data, k_period, d_period):
        self.data = data
        self.k_period = k_period
        self.d_period = d_period

    def calculate_stochastic(self):
        self.data['Lowest_Low'] = self.data['low'].rolling(window=self.k_period).min()
        self.data['Highest_High'] = self.data['high'].rolling(window=self.k_period).max()
        self.data['%K'] = 100 * ((self.data['close'] - self.data['Lowest_Low']) / (self.data['Highest_High'] - self.data['Lowest_Low']))
        self.data['%D'] = self.data['%K'].rolling(window=self.d_period).mean()
        return self.data

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
