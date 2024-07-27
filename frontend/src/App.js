// src/App.js
import React from 'react';
import AccountInfo from './components/AccountInfo';
import BacktestResults from './components/BacktestResults';
import BacktestPlot from './components/BacktestPlot';
import './App.css';

function App() {
    return (
        <div className="App">
            <header className="App-header">
                <h1>Trading Dashboard</h1>
            </header>
            <main>
                <AccountInfo />
                <BacktestPlot />
                <BacktestResults />
            </main>
        </div>
    );
}

export default App;
