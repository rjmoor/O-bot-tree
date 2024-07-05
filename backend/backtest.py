import pandas as pd

def backtest_strategy(data, indicators, param=None):
    if 'SMA' in indicators:
        if param:
            data['SMA'] = data['close'].rolling(window=param).mean()
        else:
            data['SMA'] = data['close'].rolling(window=50).mean()
        data.dropna(inplace=True)
        data['Signal'] = 0
        data.loc[data['close'] > data['SMA'], 'Signal'] = 1
        data['Position'] = data['Signal'].diff()

    if 'EMA' in indicators:
        data['EMA'] = data['close'].ewm(span=50, adjust=False).mean()
        data.dropna(inplace=True)
        data['Signal'] = 0
        data.loc[data['close'] > data['EMA'], 'Signal'] = 1
        data['Position'] = data['Signal'].diff()

    if 'RSI' in indicators:
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        data['RSI'] = 100 - (100 / (1 + rs))
        data.dropna(inplace=True)

    if 'MACD' in indicators:
        exp1 = data['close'].ewm(span=12, adjust=False).mean()
        exp2 = data['close'].ewm(span=26, adjust=False).mean()
        data['MACD'] = exp1 - exp2
        data['Signal_line'] = data['MACD'].ewm(span=9, adjust=False).mean()
        data.dropna(inplace=True)

    if 'BOLLINGER_BANDS' in indicators:
        data['MA20'] = data['close'].rolling(window=20).mean()
        data['stddev'] = data['close'].rolling(window=20).std()
        data['Upper_Band'] = data['MA20'] + (data['stddev'] * 2)
        data['Lower_Band'] = data['MA20'] - (data['stddev'] * 2)
        data.dropna(inplace=True)

    if 'STOCHASTIC' in indicators:
        low14 = data['low'].rolling(window=14).min()
        high14 = data['high'].rolling(window=14).max()
        data['%K'] = 100 * ((data['close'] - low14) / (high14 - low14))
        data['%D'] = data['%K'].rolling(window=3).mean()
        data.dropna(inplace=True)

    data['Return'] = data['close'].pct_change()
    data['Strategy_Return'] = data['Return'] * data['Position'].shift(1)

    total_return = data['Strategy_Return'].cumsum().iloc[-1]
    num_trades = data['Position'].abs().sum()
    win_rate = (data['Position'] == 1).sum() / num_trades if num_trades > 0 else 0

    return data, total_return, num_trades, win_rate

def optimize_strategy(data, indicator, param_range):
    best_param = None
    best_return = -float('inf')
    best_num_trades = 0
    best_win_rate = 0
    
    for param in param_range:
        backtest_data, total_return, num_trades, win_rate = backtest_strategy(data, [indicator], param)
        
        if total_return > best_return:
            best_return = total_return
            best_param = param
            best_num_trades = num_trades
            best_win_rate = win_rate
    
    optimization_results = {
        'best_param': best_param,
        'total_return': best_return,
        'num_trades': best_num_trades,
        'win_rate': best_win_rate
    }
    
    return optimization_results, backtest_data
