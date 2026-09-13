import React, { useState, useEffect } from 'react';
import { getTransactions } from '../api/api';

const TransactionTable = ({ onTransactionSelect }) => {
  const [transactions, setTransactions] = useState([]);

  useEffect(() => {
    const fetchTransactions = async () => {
      try {
        const data = await getTransactions();
        setTransactions(data);
      } catch (error) {
        console.error('Failed to fetch transactions:', error);
      }
    };

    fetchTransactions();
    const interval = setInterval(fetchTransactions, 1000); // every second
    return () => clearInterval(interval);
  }, []);

  const handleRowClick = (tx) => {
    if (onTransactionSelect) {
      onTransactionSelect(tx);
    }
  };

  return (
    <section className="transaction-table">
      <h2>LIVE TRANSACTION STREAM</h2>
      <table>
        <thead>
          <tr>
            <th>Block</th>
            <th>Transaction</th>
            <th>Risk Score</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {transactions.map((tx, index) => (
            <tr 
              key={index} 
              className={tx.risk_level}
              onClick={() => handleRowClick(tx)}
              style={{ cursor: 'pointer' }}
            >
              <td>{tx.block_number.toLocaleString()}</td>
              <td>
                {`${tx.tx_hash.slice(0, 6)}...${tx.tx_hash.slice(-4)}`}
              </td>
              <td>{tx.risk_score.toFixed(4)}</td>
              <td>{tx.risk_level}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
};

export default TransactionTable;
