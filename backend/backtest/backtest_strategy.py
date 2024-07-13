import pandas as pd

class BacktestStrategy:
    def __init__(self, data, indicators):
        self.data = data
        self.indicators = indicators

    def apply_indicators(self):
        for indicator in self.indicators:
            if indicator == 'SMA':
                self.data['SMA'] = self.data['close'].rolling(window=20).mean()
            elif indicator == 'EMA':
                self.data['EMA'] = self.data['close'].ewm(span=20, adjust=False).mean()
            elif indicator == 'RSI':
                delta = self.data['close'].diff(1)
                gain = delta.where(delta > 0, 0)
                loss = -delta.where(delta < 0, 0)
                avg_gain = gain.rolling(window=14).mean()
                avg_loss = loss.rolling(window=14).mean()
                rs = avg_gain / avg_loss
                self.data['RSI'] = 100 - (100 / (1 + rs))
            elif indicator == 'MACD':
                self.data['EMA12'] = self.data['close'].ewm(span=12, adjust=False).mean()
                self.data['EMA26'] = self.data['close'].ewm(span=26, adjust=False).mean()
                self.data['MACD'] = self.data['EMA12'] - self.data['EMA26']
                self.data['Signal'] = self.data['MACD'].ewm(span=9, adjust=False).mean()
            elif indicator == 'BOLLINGER_BANDS':
                self.data['Middle_Band'] = self.data['close'].rolling(window=20).mean()
                self.data['Upper_Band'] = self.data['Middle_Band'] + 2 * self.data['close'].rolling(window=20).std()
                self.data['Lower_Band'] = self.data['Middle_Band'] - 2 * self.data['close'].rolling(window=20).std()
            elif indicator == 'STOCHASTIC':
                self.data['Lowest_Low'] = self.data['low'].rolling(window=14).min()
                self.data['Highest_High'] = self.data['high'].rolling(window=14).max()
                self.data['%K'] = 100 * (self.data['close'] - self.data['Lowest_Low']) / (self.data['Highest_High'] - self.data['Lowest_Low'])
                self.data['%D'] = self.data['%K'].rolling(window=3).mean()

    def backtest(self):
        self.apply_indicators()
        # Backtesting logic (example with SMA crossover strategy)
        self.data['Position'] = 0
        self.data['Position'][20:] = np.where(self.data['SMA'][20:] > self.data['close'][20:], 1, -1)
        self.data['Strategy_Return'] = self.data['Position'].shift(1) * self.data['close'].pct_change()
        self.data['Cumulative_Return'] = (1 + self.data['Strategy_Return']).cumprod() - 1
        total_return = self.data['Cumulative_Return'].iloc[-1]
        num_trades = self.data['Position'].diff().fillna(0).abs().sum()
        win_rate = (self.data['Strategy_Return'] > 0).mean()
        return self.data, total_return, num_trades, win_rate
