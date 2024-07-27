// src/components/BacktestPlot.js
import React, { useEffect, useState } from 'react';
import axios from 'axios';
import './BacktestPlot.css';

const BacktestPlot = () => {
    const [plot, setPlot] = useState('');

    useEffect(() => {
        const fetchPlot = async () => {
            try {
                const response = await axios.post('http://192.168.1.73:5000/start-backtest'); // Update with your backend's IP and port
                setPlot(response.data.plot);
            } catch (error) {
                console.error('Error fetching backtest plot:', error);
            }
        };

        fetchPlot();
    }, []);

    if (!plot) {
        return <div>Loading plot...</div>;
    }

    return (
        <div className="backtest-plot">
            <h2>Backtest Plot</h2>
            <img src={`data:image/png;base64,${plot}`} alt="Backtest Plot" />
        </div>
    );
};

export default BacktestPlot;
