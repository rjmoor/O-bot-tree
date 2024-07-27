// src/components/AccountInfo.js
import React, { useEffect, useState } from 'react';
import axios from 'axios';
import './AccountInfo.css';

const AccountInfo = () => {
    const [accountInfo, setAccountInfo] = useState(null);

    useEffect(() => {
        const fetchAccountInfo = async () => {
            try {
                const response = await axios.get('http://127.0.0.1:5000/'); // Update with your backend's IP and port
                setAccountInfo(response.data);
            } catch (error) {
                console.error('Error fetching account information:', error);
            }
        };

        fetchAccountInfo();
    }, []);

    if (!accountInfo) {
        return <div>Loading account information...</div>;
    }

    return (
        <div className="account-info">
            <h2>Account Information</h2>
            <p><strong>Account ID:</strong> {accountInfo.account_id}</p>
            <p><strong>Balance:</strong> {accountInfo.balance}</p>
            <p><strong>Margin Available:</strong> {accountInfo.margin_available}</p>
            <p><strong>Margin Used:</strong> {accountInfo.margin_used}</p>
        </div>
    );
};

export default AccountInfo;
