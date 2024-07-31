import pandas as pd


class ATRIndicator:
    def __init__(self, period):
        self.period = period

    def apply(self, data: pd.DataFrame) -> pd.DataFrame:
        high_low = data['High'] - data['Low']
        high_Close = np.abs(data['High'] - data['Close'].shift())
        low_Close = np.abs(data['Low'] - data['Close'].shift())
        ranges = pd.concat([high_low, high_Close, low_Close], axis=1)
        true_range = ranges.max(axis=1)
        data['ATR'] = true_range.rolling(window=self.period).mean()
        return data

    def get_current_value(self, data: pd.DataFrame) -> float:
        self.apply(data)
        return data['ATR'].iloc[-1]

    def get_signal(self, data: pd.DataFrame) -> int:
        self.apply(data)
        return 1 if data['Close'].iloc[-1] > data['ATR'].iloc[-1] else -1  

    def calculate_atr(self, data, window=14):
        high_low = data['High'] - data['Low']
        high_close = np.abs(data['High'] - data['Close'].shift())
        low_close = np.abs(data['Low'] - data['Close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        atr = true_range.rolling(window=window).mean()
        return atr
    
    def generate_signal(self, data):
        data['Signal'] = 0
        data.loc[data['Close'] > data['ATR'], 'Signal'] = 1
        data.loc[data['Close'] < data['ATR'], 'Signal'] = -1
        return data