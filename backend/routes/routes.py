import base64
import io

import matplotlib.pyplot as plt
from backtest import backtest_strategy, optimize_strategy
from flask import Flask, render_template, request, send_file
from oanda_api import OandaAPI

app = Flask(__name__)

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
        optimization_results, backtest_data = optimize_strategy(data, indicator, param_range)
        
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
        
        return render_template('backtest.html', plot_url=None, total_return=optimization_results['total_return'], num_trades=optimization_results['num_trades'], win_rate=optimization_results['win_rate'], optimization_results=optimization_results, pl_chart_url=pl_chart_url)
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
