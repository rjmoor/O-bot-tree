import base64
import io
import logging
import time
from datetime import datetime, timedelta, timezone

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
import requests
from dateutil.parser import parse
from flask import Flask, jsonify, render_template, request, send_file

import backend.defs as defs

matplotlib.use('Agg')

# Configure logging
logging.basicConfig(filename='OandaAPIData.log', level=logging.INFO, format='%(asctime)s %(levelname)s:%(message)s')

app = Flask(__name__)

class OandaAPI:
    def __init__(self):
        self.session = requests.Session()

    def _request_with_retries(self, method, url, headers=None, params=None, data=None, max_retries=5, backoff_factor=0.3):
        for attempt in range(max_retries):
            try:
                response = self.session.request(method, url, headers=headers, params=params, data=data)
                if response.status_code in [200, 201, 202]:
                    return response
                elif response.status_code == 503:
                    raise requests.exceptions.RequestException("Service unavailable (503)")
            except requests.exceptions.RequestException as e:
                wait_time = backoff_factor * (2 ** attempt)
                logging.warning(f"Request failed (attempt {attempt + 1}/{max_retries}): {e}. Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
        raise requests.exceptions.RequestException("Max retries exceeded")

    def check_account(self):
        url = f"{defs.OANDA_URL}/accounts/{defs.ACCOUNT_ID}"
        try:
            response = self._request_with_retries("GET", url, headers={'Authorization': f'Bearer {defs.API_KEY}'})
            if response.status_code == 200:
                account_info = response.json()['account']
                account_id = account_info['id']
                balance = account_info['balance']
                open_exchanges = self.get_open_exchanges()
                logging.info("Account information retrieved successfully!")
                return {
                    "account_id": account_id,
                    "balance": balance,
                    "open_exchanges": open_exchanges,
                    "margin_used": account_info['marginUsed'],
                    "margin_available": account_info['marginAvailable'],
                    "open_trades": account_info['openTradeCount'],
                    "open_positions": account_info['openPositionCount'],
                    "unrealized_pl": account_info['unrealizedPL']
                }, "Account information retrieved successfully!"
            else:
                logging.error(f"Failed to retrieve account information: {response.status_code} {response.text}")
                return None, f"Failed to retrieve account information: {response.status_code} {response.text}"
        except Exception as e:
            logging.error(f"Error checking account: {e}")
            return None, str(e)

    def get_open_exchanges(self):
        now_utc = datetime.now(timezone.utc)
        exchanges = {
            'Sydney': {'open': 22, 'close': 6},
            'Tokyo': {'open': 0, 'close': 8},
            'London': {'open': 8, 'close': 16},
            'New York': {'open': 13, 'close': 21}
        }

        open_exchanges = []
        for exchange, hours in exchanges.items():
            open_time = now_utc.replace(hour=hours['open'], minute=0, second=0, microsecond=0)
            close_time = now_utc.replace(hour=hours['close'], minute=0, second=0, microsecond=0)

            if hours['close'] < hours['open']:
                close_time += timedelta(days=1)

            if open_time <= now_utc < close_time:
                open_exchanges.append(exchange)

        return open_exchanges

    def get_open_trades(self):
        url = f"{defs.OANDA_URL}/accounts/{defs.ACCOUNT_ID}/openTrades"
        try:
            response = self._request_with_retries("GET", url, headers={'Authorization': f'Bearer {defs.API_KEY}'})
            if response.status_code == 200:
                return response.json()['trades'], "Open trades retrieved successfully!"
            else:
                logging.error(f"Failed to retrieve open trades: {response.status_code} {response.text}")
                return None, f"Failed to retrieve open trades: {response.status_code} {response.text}"
        except Exception as e:
            logging.error(f"Error retrieving open trades: {e}")
            return None, str(e)

    def get_open_positions(self):
        url = f"{defs.OANDA_URL}/accounts/{defs.ACCOUNT_ID}/openPositions"
        try:
            response = self._request_with_retries("GET", url, headers={'Authorization': f'Bearer {defs.API_KEY}'})
            if response.status_code == 200:
                return response.json()['positions'], "Open positions retrieved successfully!"
            else:
                logging.error(f"Failed to retrieve open positions: {response.status_code} {response.text}")
                return None, f"Failed to retrieve open positions: {response.status_code} {response.text}"
        except Exception as e:
            logging.error(f"Error retrieving open positions: {e}")
            return None, str(e)

    def get_historical_data(self, instrument, granularity='D', count=500):
        url = f"{defs.OANDA_URL}/instruments/{instrument}/candles"
        params = {
            'granularity': granularity,
            'count': count,
            'price': 'M'
        }
        response = self._request_with_retries("GET", url, headers={'Authorization': f'Bearer {defs.API_KEY}'}, params=params)
        if response.status_code == 200:
            data = response.json()['candles']
            df = pd.DataFrame.from_records([{
                'time': candle['time'],
                'open': candle['mid']['o'],
                'high': candle['mid']['h'],
                'low': candle['mid']['l'],
                'close': candle['mid']['c']
            } for candle in data])
            df['time'] = pd.to_datetime(df['time'])
            df.set_index('time', inplace=True)
            
            df['open'] = pd.to_numeric(df['open'])
            df['high'] = pd.to_numeric(df['high'])
            df['low'] = pd.to_numeric(df['low'])
            df['close'] = pd.to_numeric(df['close'])
            
            return df, "Historical data retrieved successfully!"
        else:
            logging.error(f"Failed to retrieve historical data: {response.status_code} {response.text}")
            return None, f"Failed to retrieve historical data: {response.status_code} {response.text}"

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

@app.route('/')
def index():
    oanda_api = OandaAPI()
    account_info, message = oanda_api.check_account()
    if account_info:
        return render_template('index.html', account_info=account_info)
    else:
        return f"<h1>Error: {message}</h1>", 500

@app.route('/trades')
def trades():
    oanda_api = OandaAPI()
    trades, message = oanda_api.get_open_trades()
    if trades:
        return render_template('trades.html', trades=trades)
    else:
        return f"<h1>Error: {message}</h1>", 500

@app.route('/positions')
def positions():
    oanda_api = OandaAPI()
    positions, message = oanda_api.get_open_positions()
    if positions:
        return render_template('positions.html', positions=positions)
    else:
        return f"<h1>Error: {message}</h1>", 500

@app.route('/backtest', methods=['GET', 'POST'])
def backtest():
    if request.method == 'POST':
        pair = request.form['pair']
        granularity = request.form['granularity']
        count = int(request.form['count'])
        indicators = request.form.getlist('indicators')
    else:
        pair = 'EUR_USD'
        granularity = 'D'
        count = 500
        indicators = ['SMA']

    oanda_api = OandaAPI()
    data, message = oanda_api.get_historical_data(pair, granularity, count)
    if data is not None:
        backtest_data, total_return, num_trades, win_rate = backtest_strategy(data, indicators)
        
        fig, ax = plt.subplots()
        ax.plot(backtest_data.index, backtest_data['close'], label='Close Price')
        if 'SMA' in indicators:
            ax.plot(backtest_data.index, backtest_data['SMA'], label='SMA')
        if 'EMA' in indicators:
            ax.plot(backtest_data.index, backtest_data['EMA'], label='EMA')
        if 'RSI' in indicators:
            ax.plot(backtest_data.index, backtest_data['RSI'], label='RSI')
        if 'MACD' in indicators:
            ax.plot(backtest_data.index, backtest_data['MACD'], label='MACD')
        if 'BOLLINGER_BANDS' in indicators:
            ax.plot(backtest_data.index, backtest_data['Upper_Band'], label='Upper Bollinger Band')
            ax.plot(backtest_data.index, backtest_data['Lower_Band'], label='Lower Bollinger Band')
        if 'STOCHASTIC' in indicators:
            ax.plot(backtest_data.index, backtest_data['%K'], label='Stochastic %K')
            ax.plot(backtest_data.index, backtest_data['%D'], label='Stochastic %D')
        
        buy_signals = backtest_data[backtest_data['Position'] == 1]
        ax.plot(buy_signals.index, backtest_data.loc[buy_signals.index, 'close'], '^', markersize=10, color='g', lw=0, label='Buy Signal')
        
        sell_signals = backtest_data[backtest_data['Position'] == -1]
        ax.plot(sell_signals.index, backtest_data.loc[sell_signals.index, 'close'], 'v', markersize=10, color='r', lw=0, label='Sell Signal')
        
        ax.set_title(f'{pair} Backtest')
        ax.set_xlabel('Date')
        ax.set_ylabel('Price')
        ax.legend()
        
        img = io.BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        plt.close(fig)
        
        plot_url = base64.b64encode(img.getvalue()).decode()
        
        return render_template('backtest.html', plot_url=plot_url, total_return=total_return, num_trades=num_trades, win_rate=win_rate)
    else:
        return f"<h1>Error: {message}</h1>", 500

@app.route('/optimize', methods=['POST'])
def optimize():
    indicator = request.form['indicator']
    parameter = request.form['parameter']
    param_range = list(map(int, request.form['range'].split(',')))
    
    oanda_api = OandaAPI()
    data, message = oanda_api.get_historical_data('EUR_USD')
    
    if data is not None:
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
        
        # Plot the P/L chart
        fig, ax = plt.subplots()
        ax.plot(backtest_data.index, backtest_data['Strategy_Return'].cumsum(), label='Cumulative P/L')
        ax.set_title('Optimization P/L')
        ax.set_xlabel('Date')
        ax.set_ylabel('Cumulative P/L')
        ax.legend()
        
        img = io.BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        plt.close(fig)
        
        pl_chart_url = base64.b64encode(img.getvalue()).decode()
        
        return render_template('backtest.html', plot_url=None, total_return=best_return, num_trades=best_num_trades, win_rate=best_win_rate, optimization_results=optimization_results, pl_chart_url=pl_chart_url)
    else:
        return f"<h1>Error: {message}</h1>", 500

@app.route('/plot/<string:plot_type>')
def plot(plot_type):
    oanda_api = OandaAPI()
    if plot_type == 'balance':
        account_info, _ = oanda_api.check_account()
        balance = float(account_info['balance'])
        margin_used = float(account_info['margin_used'])
        margin_available = float(account_info['margin_available'])
        
        fig, ax = plt.subplots()
        labels = 'Balance', 'Margin Used', 'Margin Available'
        sizes = [balance, margin_used, margin_available]
        ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
        ax.axis('equal')
        
        img = io.BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        plt.close(fig)
        return send_file(img, mimetype='image/png')
    else:
        return "<h1>Plot type not supported</h1>", 400

if __name__ == '__main__':
    app.run(debug=True)
