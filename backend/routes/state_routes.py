from flask import Blueprint, request, jsonify
from ..variables import STATE_RED, STATE_YELLOW, STATE_GREEN

state_bp = Blueprint('state', __name__)

current_state = STATE_RED

@state_bp.route('/current', methods=['GET'])
def get_current_state():
    return jsonify({'state': current_state}), 200

@state_bp.route('/transition', methods=['POST'])
def transition_state():
    global current_state
    data = request.get_json()
    new_state = data.get('newState')
    if new_state in [STATE_RED, STATE_YELLOW, STATE_GREEN]:
        current_state = new_state
        return jsonify({'state': current_state}), 200
    else:
        return jsonify({'error': 'Invalid state'}), 400
