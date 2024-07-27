import pandas as pd

class BollingerBandsIndicator:
    def __init__(self, data, window=20, num_std_dev=2):
        self.data = data
        self.window = window
        self.num_std_dev = num_std_dev

    def calculate(self):
        rolling_mean = self.data['close'].rolling(window=self.window).mean()
        rolling_std = self.data['close'].rolling(window=self.window).std()
        
        self.data['Upper_Band'] = rolling_mean + (rolling_std * self.num_std_dev)
        self.data['Lower_Band'] = rolling_mean - (rolling_std * self.num_std_dev)
        self.data['Bollinger_Mid'] = rolling_mean
        
        return self.data
