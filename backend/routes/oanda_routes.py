from flask import Blueprint, request, jsonify
from ..oanda_api.oanda_api import OandaAPIData

oanda_bp = Blueprint('oanda', __name__)
oanda_api = OandaAPIData()

@oanda_bp.route('/account-details', methods=['GET'])
def get_account_details():
    try:
        data = oanda_api.get_account_details()
        return jsonify(data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@oanda_bp.route('/instruments', methods=['GET'])
def get_instruments():
    try:
        status_code, data = oanda_api.get_instruments()
        return jsonify(data), status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@oanda_bp.route('/candles/<instrument>', methods=['GET'])
def get_candles(instrument):
    granularity = request.args.get('granularity', 'H1')
    count = request.args.get('count', 100)
    try:
        data = oanda_api.get_candles(instrument, granularity, count)
        return jsonify(data.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@oanda_bp.route('/place-order', methods=['POST'])
def place_order():
    data = request.get_json()
    instrument = data.get('instrument')
    units = data.get('units')
    order_type = data.get('orderType', 'MARKET')
    try:
        response = oanda_api.place_order(instrument, units, order_type)
        return jsonify(response), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
