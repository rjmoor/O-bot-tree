// src/components/BacktestResults.js
import React, { useEffect, useState } from 'react';
import axios from 'axios';
import './BacktestResults.css';

const BacktestResults = () => {
    const [results, setResults] = useState([]);

    useEffect(() => {
        const fetchResults = async () => {
            try {
                const response = await axios.get('http://localhost:5000/backtest-results');
                setResults(response.data);
            } catch (error) {
                console.error('Error fetching backtest results:', error);
            }
        };

        fetchResults();
    }, []);

    return (
        <div className="backtest-results">
            <h2>Backtest Results</h2>
            <table>
                <thead>
                    <tr>
                        <th>Pair</th>
                        <th>Strategy</th>
                        <th>Parameters</th>
                        <th>Total Return</th>
                        <th>Number of Trades</th>
                        <th>Win Rate</th>
                    </tr>
                </thead>
                <tbody>
                    {results.map((result, index) => (
                        <tr key={index}>
                            <td>{result.pair}</td>
                            <td>{result.strategy}</td>
                            <td>{JSON.stringify(result.params)}</td>
                            <td>{result.total_return}</td>
                            <td>{result.num_trades}</td>
                            <td>{result.win_rate}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
};

export default BacktestResults;
