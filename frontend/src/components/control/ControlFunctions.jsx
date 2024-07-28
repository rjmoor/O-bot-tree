import '../../../main.css';

function startBot() {
    fetch('/start_bot', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                alert('Bot started successfully');
            } else {
                alert('Failed to start bot');
            }
        });
}

function stopBot() {
    fetch('/stop_bot', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                alert('Bot stopped successfully');
            } else {
                alert('Failed to stop bot');
            }
        });
}

function fetchIndicatorStatus() {
    const instrument = document.getElementById('instrumentSelect').value;
    fetch(`/indicator_status?instrument=${instrument}`)
        .then(response => response.json())
        .then(data => {
            document.getElementById('RSIStatus').className = 'status-indicator RSI ' + data.RSI;
            document.getElementById('SMAStatus').className = 'status-indicator SMA ' + data.SMA;
            document.getElementById('EMAStatus').className = 'status-indicator EMA ' + data.EMA;
            document.getElementById('MACDStatus').className = 'status-indicator MACD ' + data.MACD;
            document.getElementById('BollingerBandsStatus').className = 'status-indicator BollingerBands ' + data.BollingerBands;
            document.getElementById('StochasticStatus').className = 'status-indicator Stochastic ' + data.Stochastic;

            // Update traffic light
            fetchStateMachineStatus();
        });
}

function fetchStateMachineStatus() {
    fetch('/get_state')
        .then(response => response.json())
        .then(data => {
            document.getElementById('redLight').classList.toggle('on', data.state === 'off');
            document.getElementById('greenLight').classList.toggle('on', data.state === 'on');
        });
}

function toggleStateMachine() {
    const switchState = document.getElementById('stateMachineSwitch').checked;
    const newState = switchState ? 'on' : 'off';
    fetch('/set_state', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ state: newState })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            fetchStateMachineStatus();
        } else {
            alert('Failed to change state machine status');
        }
    });
}

function updateInstrument() {
    fetchIndicatorStatus();
    const instrument = document.getElementById('instrumentSelect').value;
    new TradingView.widget({
        "width": 800,
        "height": 300,
        "symbol": instrument,
        "interval": "D",
        "timezone": "Etc/UTC",
        "theme": "dark",
        "style": "1",
        "locale": "en",
        "toolbar_bg": "#f1f3f6",
        "enable_publishing": false,
        "allow_symbol_change": true,
        "container_id": "tradingview_chart"
    });
}

// Initial fetch for the default instrument
fetchIndicatorStatus();
new TradingView.widget({
    "width": 800,
    "height": 300,
    "symbol": "OANDA:EURUSD",
    "interval": "D",
    "timezone": "Etc/UTC",
    "theme": "dark",
    "style": "1",
    "locale": "en",
    "toolbar_bg": "#f1f3f6",
    "enable_publishing": false,
    "allow_symbol_change": true,
    "container_id": "tradingview_chart"
});
