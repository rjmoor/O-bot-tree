STATE_MACHINE = True 

STATE_RED = 'red'        
STATE_YELLOW = 'yellow'  
STATE_GREEN = 'green'    
current_state = STATE_RED

SWITCHES = {
    "RSI": True,
    "MACD": True,
    "SMA": False,
    "EMA": False,
    "BOLLINGER_BANDS": False,
    "STOCHASTIC": False
}

BACKTESTING = {
    "BT_TYPE" : 'Strategy', 
}

OPTIMIZATION_RANGES = {
    "RSI": {
        "RSI_PERIOD": [10, 20, 60],
        "RSI_OVERBOUGHT": [50, 60, 70],
        "RSI_OVERSOLD": [30, 40, 50]
    },
    "MACD": {
        "MACD_FAST_PERIOD": [5, 10, 15],
        "MACD_SLOW_PERIOD": [20, 25, 30],
        "MACD_SIGNAL_PERIOD": [5, 10, 15]
    },
    "SMA": {
        "SMA_PERIOD": [50, 100, 200],
        "Fast_Period": [10, 20, 30],
        "Slow_Period": [50, 100, 200]
    },
    "EMA": {
        "EMA_PERIOD": [50, 100, 200],
        "Fast_Period": [10, 20, 30],
        "Slow_Period": [50, 100, 200]
    },
    "BOLLINGER_BANDS": {
        "BOLLINGER_BANDS_PERIOD": [10, 20, 30],
        "BOLLINGER_BANDS_STD_DEV": [1, 2, 3]
    },
    "STOCHASTIC": {
        "STOCHASTIC_K_PERIOD": [10, 14, 18],
        "STOCHASTIC_D_PERIOD": [3, 5, 7]
    }
}

LIVE_TRADING = {
    "TRADE_INSTRUMENTS" : ["EUR_USD", "GBP_USD", "USD_JPY"],
    "TRADE_UNITS" : 1000,
    "TRADING_COUNT" : 100,
    "GRANULARITY" : ["M1", "M5", "M15", "M30", "H1", "H4", "D"],
    
    "STOP_LOSS" : 20, 
    "TAKE_PROFIT" : 50, 
    "TRAILING_STOP_LOSS" : 10, 
    
    "TIMEFRAME" : "H1", 
    "TRADING_GRANULARITY" : 'H1',
    
    "ORDER_TYPE" : 'MARKET',
    

    "INDICATORS": {
        "RSI": {
            "enabled": SWITCHES["RSI"],
            "period": OPTIMIZATION_RANGES["RSI"]["RSI_PERIOD"],
            "overbought": OPTIMIZATION_RANGES["RSI"]["RSI_OVERBOUGHT"],
            "oversold": OPTIMIZATION_RANGES["RSI"]["RSI_OVERSOLD"]
        },
        "MACD": {
            "enabled": SWITCHES["MACD"],
            "fast_period": OPTIMIZATION_RANGES["MACD"]["MACD_FAST_PERIOD"],
            "slow_period": OPTIMIZATION_RANGES["MACD"]["MACD_SLOW_PERIOD"],
            "signal_period": OPTIMIZATION_RANGES["MACD"]["MACD_SIGNAL_PERIOD"]
        },
        "SMA": {
            "enabled": SWITCHES["SMA"],
            "period": OPTIMIZATION_RANGES["SMA"]["SMA_PERIOD"],
            "fast": OPTIMIZATION_RANGES["SMA"]["Fast_Period"],
            "slow": OPTIMIZATION_RANGES["SMA"]["Slow_Period"]
        },
        "EMA": {
            "enabled": SWITCHES["EMA"],
            "period": OPTIMIZATION_RANGES["EMA"]["EMA_PERIOD"],
            "fast": OPTIMIZATION_RANGES["EMA"]["Fast_Period"],
            "slow": OPTIMIZATION_RANGES["EMA"]["Slow_Period"]
        },
        "BOLLINGER_BANDS": {
            "enabled": SWITCHES["BOLLINGER_BANDS"],
            "period": OPTIMIZATION_RANGES["BOLLINGER_BANDS"]["BOLLINGER_BANDS_PERIOD"],
            "std_dev": OPTIMIZATION_RANGES["BOLLINGER_BANDS"]["BOLLINGER_BANDS_STD_DEV"]
        },
        "STOCHASTIC": {
            "enabled": SWITCHES["STOCHASTIC"],
            "k_period": OPTIMIZATION_RANGES["STOCHASTIC"]["STOCHASTIC_K_PERIOD"],
            "d_period": OPTIMIZATION_RANGES["STOCHASTIC"]["STOCHASTIC_D_PERIOD"]
        }
    },
}
