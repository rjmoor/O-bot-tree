import base64
import io
import logging
import os
import time
from datetime import datetime
from threading import Thread

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
from backend import variables
from backend.variables import STATE_MACHINE
from flask import (Flask, jsonify, redirect, render_template, request,
                send_file, session, url_for)
from flask_assets import Bundle, Environment
from backend.tradebot import TradeBot

from backend.backtest.backtest_strategy import BacktestStrategy
from backend.control.control_system import ControlSystem
from backend.indicators.macd_indicator import MACDIndicator
from backend.indicators.stochastic_indicator import StochasticIndicator
from backend.oanda_api.oanda_api import OandaAPI
from backend.optimization.optimize_strategy import OptimizeStrategy
from backend.strategies.ema_crossover_strategy import EMACrossoverStrategy
from backend.strategies.ema_strategy import EMAStrategy
from backend.strategies.momentum_strategy import MomentumStrategy
from backend.strategies.rsi_strategy import RSIStrategy
from backend.strategies.sma_crossover_strategy import SMACrossoverStrategy
from backend.strategies.sma_strategy import SMAStrategy
from backend.utils.utility import configure_logging

app = Flask(__name__)
configure_logging("app")
control_system = ControlSystem()
app.secret_key = os.getenv('SECRET_KEY', 'Rahm')
bot_thread = None

matplotlib.use("Agg")

assets = Environment(app)
scss = Bundle('static/styles/main.scss', filters='pyscss', output='static/styles/main.css')
assets.register('scss_all', scss)
assets.auto_build = True
assets.debug = True

trade_bot = TradeBot()

@app.route("/")
def index():
    oanda_api = OandaAPI()
    account_info, message = oanda_api.check_account()
    if account_info:
        return render_template("index.html", account_info=account_info, state_machine=STATE_MACHINE)
    else:
        return f"<h1>Error: {message}</h1>", 500

@app.route("/logs")
def fetch_logs():
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')
    try:
        log_filename = f'logs/app_{datetime.now().strftime("%Y%m%d")}.log'
        logging.basicConfig(
            filename=log_filename,
            level=logging.INFO,
            format='%(asctime)s %(levelname)s:%(message)s'
        )
        logging.info('Logging configured successfully.')
        return log_filename
    except Exception as e:
        logging.error(f"Error configuring logging: {e}")
        return f"Error configuring logging: {e}"

@app.route("/start_bot", methods=["POST"])
def start_bot():
    global bot_thread
    if not bot_thread:
        bot_thread = Thread(target=control_system.run_analysis)
        bot_thread.start()
        return jsonify({"status": "success"})
    else:
        return jsonify({"status": "Bot is already running"})

@app.route("/stop_bot", methods=["POST"])
def stop_bot():
    global bot_thread
    if bot_thread:
        variables.STATE_MACHINE = False
        bot_thread.join()
        bot_thread = None
        return jsonify({"status": "success"})
    else:
        return jsonify({"status": "Bot is not running"})

@app.route("/execute_trades", methods=["POST"])
def execute_trades():
    try:
        instruments = request.form.getlist('instruments')
        for instrument in instruments:
            control_system.run_analysis(instrument)
            if control_system.current_state == variables.STATE_GREEN:
                # Implement trade execution logic here
                pass
        return jsonify({"status": "Trades executed successfully."})
    except Exception as e:
        logging.error(f"Error executing trades: {e}")
        return jsonify({"status": "Error executing trades.", "error": str(e)})

@app.route("/auto_trades", methods=["POST"])
def auto_trades():
    try:
        instruments = request.form.getlist('instruments')
        for instrument in instruments:
            data = control_system.get_historical_data(instrument, 'M')  # Monthly data
            strategy = MomentumStrategy(data, rsi_params, stochastic_params)
            report = strategy.backtest()
            
            if report['total_return'] > 0 and report['win_rate'] > 0.5:  # Example conditions
                variables.current_state = variables.STATE_GREEN
                logging.info(f"State set to GREEN for {instrument} based on monthly analysis.")
                data = control_system.get_historical_data(instrument, 'D')  # Daily data
                strategy = MomentumStrategy(data, rsi_params, stochastic_params)
                report = strategy.backtest()
                
                if report['total_return'] > 0 and report['win_rate'] > 0.5:
                    variables.current_state = variables.STATE_GREEN
                    logging.info(f"State set to GREEN for {instrument} based on daily analysis.")
                    data = control_system.get_historical_data(instrument, 'M1')  # Minute data
                    strategy = MomentumStrategy(data, rsi_params, stochastic_params)
                    report = strategy.backtest()
                    
                    if report['total_return'] > 0 and report['win_rate'] > 0.5:
                        # Execute trade logic here
                        logging.info(f"Executing trade for {instrument}")
                    else:
                        variables.current_state = variables.STATE_YELLOW
                        logging.info(f"State set to YELLOW for {instrument} based on minute analysis.")
                else:
                    variables.current_state = variables.STATE_YELLOW
                    logging.info(f"State set to YELLOW for {instrument} based on daily analysis.")
            else:
                variables.current_state = variables.STATE_RED
                logging.info(f"State set to RED for {instrument} based on monthly analysis.")
        
        return jsonify({"status": "Auto trades executed successfully."})
    except Exception as e:
        logging.error(f"Error executing auto trades: {e}")
        return jsonify({"status": "Error executing auto trades.", "error": str(e)})

@app.route('/get_state', methods=['GET'])
def get_state():
    state = 'on' if STATE_MACHINE else 'off'
    return jsonify({'state': state, 'status': 'success'})

@app.route('/set_state', methods=['POST'])
def set_state():
    global STATE_MACHINE
    new_state = request.form.get('state')
    data = request.json
    if ('state' in data or new_state == 'on'):
        STATE_MACHINE = data['state'] == 'on'
        logging.info(f"State changed to {new_state}")
        return jsonify({"status": "State updated successfully.", "new_state": new_state})
    return jsonify({"status": "Invalid state.", "error": "Invalid state value provided."})

@app.route("/select_strategy", methods=["POST"])
def select_strategy():
    strategy = request.form.get('strategy')
    if strategy in ['RSI', 'SMA', 'EMA', 'MACD', 'BOLLINGER_BANDS', 'STOCHASTIC']:
        variables.selected_strategy = strategy
        logging.info(f"Strategy selected: {strategy}")
        return jsonify({"status": "Strategy selected successfully.", "selected_strategy": strategy})
    else:
        return jsonify({"status": "Invalid strategy.", "error": "Invalid strategy value provided."})

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
        strategy = BacktestStrategy(data, indicators)  # Instantiate the class
        backtest_data, total_return, num_trades, win_rate = strategy.backtest()  # Call the method

        fig, ax = plt.subplots(figsize=(14, 10))  # Adjust the figure size for larger plot
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

        img = io.BytesIO()
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
            pair=pair,
            granularity=granularity,
            count=count,
            indicators=indicators
        )
    else:
        return f"<h1>Error: {message}</h1>", 500

@app.route("/optimize", methods=["GET", "POST"])
def optimize():
    try:
        strategy_names = request.form.getlist("strategies")
        param_ranges = request.form["range"].split(",")

        oanda_api = OandaAPI()
        data, message = oanda_api.get_historical_data("EUR_USD", "D", 500)
        if data is None:
            return f"<h1>Error: {message}</h1>", 500

        strategy_classes = [get_strategy_class(name) for name in strategy_names if get_strategy_class(name)]
        param_dict = {name: variables.OPTIMIZATION_RANGES[name] for name in strategy_names}

        optimizer = OptimizeStrategy(data, strategy_classes, param_dict)
        best_combinations = optimizer.optimize()

        session['best_combinations'] = best_combinations  # Save to session

        # Generate report
        report = generate_report(best_combinations)

        return render_template(
            "optimization_results.html",
            report=report
        )

    except KeyError as e:
        logging.error(f"Missing form data: {e}")
        return f"<h1>Error: Missing form data - {e}</h1>", 400
    except Exception as e:
        logging.error(f"Unhandled exception: {e}")
        return f"<h1>Error: {e}</h1>", 500

@app.route("/download_report")
def download_report():
    best_combinations = session.get('best_combinations', [])
    if not best_combinations:
        return f"<h1>No report available</h1>", 400

    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')

    for i, (params, performance, total_return, num_trades, win_rate, results) in enumerate(best_combinations):
        df = pd.DataFrame(results)
        sheet_name = f"Strategy_{i+1}_Grade_{chr(65+i)}"
        df.to_excel(writer, sheet_name=sheet_name, index=False)
        worksheet = writer.sheets[sheet_name]
        worksheet.write('K1', 'Params')
        worksheet.write('K2', str(params))
        worksheet.write('L1', 'Performance')
        worksheet.write('L2', performance)
        worksheet.write('M1', 'Total Return')
        worksheet.write('M2', total_return)
        worksheet.write('N1', 'Number of Trades')
        worksheet.write('N2', num_trades)
        worksheet.write('O1', 'Win Rate')
        worksheet.write('O2', win_rate)

    writer.save()
    output.seek(0)

    return send_file(output, attachment_filename='optimization_report.xlsx', as_attachment=True)

def generate_report(best_combinations):
    report = []
    for i, (params, performance, total_return, num_trades, win_rate, results) in enumerate(best_combinations):
        grade = 'A' if i == 0 else 'B' if i == 1 else 'C' if i == 2 else 'D'
        report.append({
            'params': params,
            'performance': performance,
            'total_return': total_return,
            'num_trades': num_trades,
            'win_rate': win_rate,
            'grade': grade
        })
    return report

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

        img = io.BytesIO()
        plt.savefig(img, format="png")
        img.seek(0)
        plt.close(fig)
        return send_file(img, mimetype="image/png")
    else:
        return "<h1>Plot type not supported</h1>", 400

@app.route("/settings")
def settings():
    return render_template("settings.html")

@app.route('/error')
def error():
    message = request.args.get('message', 'An unknown error occurred')
    return render_template('error.html', message=message)

if __name__ == "__main__":
    trade_bot.start()
    app.run(debug=True)
