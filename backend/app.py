import base64
import io
import logging
import time
from datetime import datetime, timedelta, timezone
from threading import Thread

from backend.backtest.backtest_strategy import backtest_strategy
import defs
import matplotlib
import matplotlib.pyplot as plt
import mplfinance as mpf
import pandas as pd
import requests
import variables
from backtest import optimize_strategy
from dateutil.parser import parse
from flask import (Flask, jsonify, redirect, render_template, request, send_file, url_for)
from flask_assets import Bundle, Environment
from utils.indicators.strategies import SMAStrategy, EMAStrategy, RSIStrategy, SMACrossoverStrategy, EMACrossoverStrategy
from macd_indicator import MACDIndicator
from stochastic_indicator import StochasticIndicator  # Import StochasticIndicator
from optimization import optimize_strategy
from backend.oanda_api.oanda_api import OandaAPI

matplotlib.use("Agg")

# Configure logging
logging.basicConfig(
    filename="./logs/OandaAPIData.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s:%(message)s",
)

app = Flask(__name__)

assets = Environment(app)
scss = Bundle('static/styles/main.scss', filters='pyscss', output='static/styles/main.css')
assets.register('scss_all', scss)

class TradeBot:
    def __init__(self):
        self.api = OandaAPI()
        self.running = False
        self.macd_indicator = MACDIndicator()  # Initialize MACDIndicator
        self.stochastic_indicator = StochasticIndicator()  # Initialize StochasticIndicator

    def start(self):
        self.running = True
        self.thread = Thread(target=self.run)
        self.thread.start()

    def stop(self):
        self.running = False
        self.thread.join()

    def run(self):
        while self.running:
            for pair in variables.LIVE_TRADING["TRADE_INSTRUMENTS"]:
                granularity = variables.LIVE_TRADING["TRADING_GRANULARITY"]
                count = variables.LIVE_TRADING["TRADING_COUNT"]
                data, message = self.api.get_historical_data(pair, granularity, count)
                if data is not None:
                    for indicator, params in variables.OPTIMIZATION_RANGES.items():
                        param_range = params[next(iter(params))]
                        optimization_results, _ = optimize_strategy(
                            data, indicator, param_range
                        )
                        self.execute_trade(pair, optimization_results, data)
                else:
                    logging.error(
                        f"Failed to get historical data for {pair}: {message}"
                    )
            time.sleep(3600)  # Run every hour

    def execute_trade(self, pair, optimization_results, data):
        # Implement trading logic here using the best parameters from optimization_results
        macd_state = self.macd_indicator.check_green_light(data)
        stochastic_state = self.stochastic_indicator.get_signal_state(data)
        
        if macd_state and stochastic_state == 'green':
            # Example: Execute trade if both MACD and Stochastic are green
            print(f"Green light for {pair}: Execute trade")
        elif stochastic_state == 'yellow':
            print(f"Yellow light for {pair}: Setup active, prepare to trade")
        else:
            print(f"Red light for {pair}: Not favorable to trade")

trade_bot = TradeBot()


def get_tradingview_symbol(oanda_symbol):
    return oanda_symbol.replace("_", "")


@app.route("/")
def index():
    oanda_api = OandaAPI()
    account_info, message = oanda_api.check_account()
    if account_info:
        return render_template("index.html", account_info=account_info)
    else:
        return f"<h1>Error: {message}</h1>", 500


@app.route("/auto_trades")
def auto_trades():
    oanda_api = OandaAPI()
    instruments = variables.LIVE_TRADING["TRADE_INSTRUMENTS"]
    selected_instrument = request.args.get("instrument", instruments[0])
    candlestick_chart = None

    if request.method == "POST":
        try:
            instrument = request.form["instrument"]
            units = int(request.form["units"])
            side = request.form["side"]
            stop_loss = request.form["stop_loss"]
            take_profit = request.form["take_profit"]

            stop_loss = float(stop_loss) if stop_loss else None
            take_profit = float(take_profit) if take_profit else None

            trade, message = oanda_api.place_trade(
                instrument, units, side, stop_loss, take_profit
            )
            if trade:
                return redirect(url_for("manual_trades", instrument=instrument))
            else:
                return f"<h1>Error: {message}</h1>", 500
        except KeyError as e:
            logging.error(f"Missing form data: {e}")
            return f"<h1>Error: Missing form data - {e}</h1>", 400

    # Get historical data and generate candlestick chart
    data, message = oanda_api.get_historical_data(selected_instrument, "H1", 100)
    if data is not None:
        fig, ax = plt.subplots()
        mpf.plot(data, type="candle", style="charles", ax=ax)
        img = io.BytesIO()
        plt.savefig(img, format="png")
        img.seek(0)
        plt.close(fig)
        candlestick_chart = base64.b64encode(img.getvalue()).decode()

    trades, message = oanda_api.get_open_trades()
    if trades is not None:
        return render_template(
            "manual_trades.html",
            trades=trades,
            instruments=instruments,
            selected_instrument=selected_instrument,
            candlestick_chart=candlestick_chart,
        )
    else:
        return render_template(
            "manual_trades.html",
            trades=[],
            instruments=instruments,
            selected_instrument=selected_instrument,
            candlestick_chart=candlestick_chart,
            error=message,
        )


@app.route("/manual_trades", methods=["GET", "POST"])
def manual_trades():
    oanda_api = OandaAPI()
    instruments = ["EUR_USD", "GBP_USD", "USD_JPY"]
    selected_instrument = request.args.get('instrument', 'EUR_USD')
    message = None
    success = None

    if request.method == 'POST':
        instrument = request.form['instrument']
        units = int(request.form['units'])
        side = request.form['side']
        stop_loss = float(request.form['stop_loss']) if request.form['stop_loss'] else None
        take_profit = float(request.form['take_profit']) if request.form['take_profit'] else None
        trailing_stop_loss = False

        response, message = oanda_api.place_trade(instrument, units, side, stop_loss, take_profit, trailing_stop_loss)
        if response:
            success = "Trade placed successfully!"

        if stop_loss:
            stop_loss = float(stop_loss)
        if take_profit:
            take_profit = float(take_profit)

        trade, message = oanda_api.place_trade(
            instrument, units, side, stop_loss, take_profit
        )
        if trade:
            return render_template(
                "response.html", message=message, theme="dark", success=True
            )
        else:
            return render_template(
                "response.html", message=message, theme="dark", success=False
            )
    else:
        selected_instrument = request.args.get("instrument", "EUR_USD")
        trades, message = oanda_api.get_open_trades()
        tradingview_symbol = selected_instrument.replace("_", "")

        return render_template(
            "manual_trades.html",
            instruments=instruments,
            selected_instrument=selected_instrument,
            trades=trades,
            tradingview_symbol=tradingview_symbol,
        )


@app.route("/close_trade/<trade_id>", methods=["POST"])
def close_trade(trade_id):
    oanda_api = OandaAPI()
    trade, message = oanda_api.close_trade(trade_id)
    if trade:
        return redirect(url_for("manual_trades"))
    else:
        return f"<h1>Error: {message}</h1>", 500


@app.route("/positions")
def positions():
    oanda_api = OandaAPI()
    positions, message = oanda_api.get_open_positions()
    if positions:
        return render_template("positions.html", positions=positions)
    else:
        return f"<h1>Error: {message}</h1>", 500


@app.route("/backtest", methods=["GET", "POST"])
def backtest():
    if request.method == "POST":
        pair = request.form["pair"]
        granularity = request.form["granularity"]
        count = int(request.form["count"])
        indicators = request.form.getlist("indicators")
    else:
        pair = "EUR_USD"
        granularity = "D"
        count = 500
        indicators = ["SMA"]

    oanda_api = OandaAPI()
    data, message = oanda_api.get_historical_data(pair, granularity, count)
    if data is not None:
        backtest_data, total_return, num_trades, win_rate = backtest_strategy(
            data, indicators
        )

        fig, ax = plt.subplots()
        ax.plot(backtest_data.index, backtest_data["close"], label="Close Price")
        if "SMA" in indicators:
            ax.plot(backtest_data.index, backtest_data["SMA"], label="SMA")
        if "EMA" in indicators:
            ax.plot(backtest_data.index, backtest_data["EMA"], label="EMA")
        if "RSI" in indicators:
            ax.plot(backtest_data.index, backtest_data["RSI"], label="RSI")
        if "MACD" in indicators:
            ax.plot(backtest_data.index, backtest_data["MACD"], label="MACD")
        if "BOLLINGER_BANDS" in indicators:
            ax.plot(
                backtest_data.index,
                backtest_data["Upper_Band"],
                label="Upper Bollinger Band",
            )
            ax.plot(
                backtest_data.index,
                backtest_data["Lower_Band"],
                label="Lower Bollinger Band",
            )
        if "STOCHASTIC" in indicators:
            ax.plot(backtest_data.index, backtest_data["%K"], label="Stochastic %K")
            ax.plot(backtest_data.index, backtest_data["%D"], label="Stochastic %D")

        buy_signals = backtest_data[backtest_data["Position"] == 1]
        ax.plot(
            buy_signals.index,
            backtest_data.loc[buy_signals.index, "close"],
            "^",
            markersize=10,
            color="g",
            lw=0,
            label="Buy Signal",
        )

        sell_signals = backtest_data[backtest_data["Position"] == -1]
        ax.plot(
            sell_signals.index,
            backtest_data.loc[sell_signals.index, "close"],
            "v",
            markersize=10,
            color="r",
            lw=0,
            label="Sell Signal",
        )

        ax.set_title(f"{pair} Backtest")
        ax.set_xlabel("Date")
        ax.set_ylabel("Price")
        ax.legend()

        img = io.Bytes.IO()
        plt.savefig(img, format="png")
        img.seek(0)
        plt.close(fig)

        plot_url = base64.b64encode(img.getvalue()).decode()

        return render_template(
            "backtest.html",
            plot_url=plot_url,
            total_return=total_return,
            num_trades=num_trades,
            win_rate=win_rate,
        )
    else:
        return f"<h1>Error: {message}</h1>", 500


@app.route("/optimize", methods=["POST"])
def optimize():
    strategy_name = request.form["strategy"]
    param_range = request.form["range"].split(",")

    oanda_api = OandaAPI()
    data, message = oanda_api.get_historical_data("EUR_USD", "D", 500)

    if data is not None:
        if strategy_name == 'SMA':
            results = optimize_strategy(data, SMAStrategy, {'single': list(map(int, param_range))})
        elif strategy_name == 'EMA':
            results = optimize_strategy(data, EMAStrategy, {'single': list(map(int, param_range))})
        elif strategy_name == 'RSI':
            results = optimize_strategy(data, RSIStrategy, {'single': list(map(int, param_range))})
        elif strategy_name == 'SMACrossover':
            fast_range = list(map(int, param_range[0].split("-")))
            slow_range = list(map(int, param_range[1].split("-")))
            results = optimize_strategy(data, SMACrossoverStrategy, {'fast': fast_range, 'slow': slow_range})
        elif strategy_name == 'EMACrossover':
            fast_range = list(map(int, param_range[0].split("-")))
            slow_range = list(map(int, param_range[1].split("-")))
            results = optimize_strategy(data, EMACrossoverStrategy, {'fast': fast_range, 'slow': slow_range})

        return render_template(
            "optimization_results.html",
            best_params=results['best_params'],
            performance=results['performance']
        )
    else:
        return f"<h1>Error: {message}</h1>", 500

@app.route("/plot/<string:plot_type>")
def plot(plot_type):
    oanda_api = OandaAPI()
    if plot_type == "balance":
        account_info, _ = oanda_api.check_account()
        balance = float(account_info["balance"])
        margin_used = float(account_info["margin_used"])
        margin_available = float(account_info["margin_available"])

        fig, ax = plt.subplots()
        labels = "Balance", "Margin Used", "Margin Available"
        sizes = [balance, margin_used, margin_available]
        ax.pie(sizes, labels=labels, autopct="%1.1f%%", startangle=90)
        ax.axis("equal")

        img = io.Bytes.IO()
        plt.savefig(img, format="png")
        img.seek(0)
        plt.close(fig)
        return send_file(img, mimetype="image/png")
    else:
        return "<h1>Plot type not supported</h1>", 400

@app.route("/settings")
def settings():
    # Placeholder for settings route
    return render_template("settings.html")

@app.route('/error')
def error():
    message = request.args.get('message', 'An unknown error occurred')
    return render_template('error.html', message=message)

if __name__ == "__main__":
    trade_bot.start()
    app.run(debug=True)
