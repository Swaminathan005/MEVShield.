import React from 'react';

const TransactionDetails = ({ transaction }) => {
  if (!transaction) {
    return (
      <div className="transaction-details">
        <p>Select a transaction to see details</p>
      </div>
    );
  }

  // We have the features stored in the transaction object (from the backend)
  const { features } = transaction;
  const featureNames = [
    "LOG_VALUE_ETH", "LOG_AMOUNT_USD", "LOG_PREVIOUS_USD", "LOG_NEXT_USD",
    "LOG_GAS_PRICE", "LOG_PRIORITY_FEE", "VALUE_ETH", "AMOUNT_USD",
    "GAS_USED", "GAS_PRICE_WEI", "PRIORITY_FEE_WEI", "INPUT_SIZE_BYTES",
    "POOL_TRADES_IN_BLOCK", "HAS_PREV_TRADE", "HAS_NEXT_TRADE",
    "IS_ISOLATED_POOL_TRADE", "PREVIOUS_GAP", "NEXT_GAP",
    "PRIORITY_FEE_RATIO_PREV", "USD_RATIO_PREV", "PREVIOUS_INPUT_SIZE", "NEXT_INPUT_SIZE"
  ];

  // We'll show the first 6 features for simplicity
  const featuresToShow = featureNames.slice(0, 6).map((name, i) => ({
    name,
    value: features[i]
  }));

  return (
    <section className="transaction-details">
      <h2>TRANSACTION DETAILS</h2>
      <div className="details-grid">
        <div>
          <p><strong>Transaction Hash:</strong> {transaction.tx_hash}</p>
          <p><strong>Block Number:</strong> {transaction.block_number}</p>
          <p><strong>Transaction Index:</strong> {transaction.transaction_index}</p>
          <p><strong>Risk Score:</strong> {transaction.risk_score.toFixed(4)}</p>
          <p><strong>Decision:</strong> <span className={transaction.risk_level.toLowerCase()}>{transaction.risk_level}</span></p>
        </div>
        <div>
          <h3>Transaction Features</h3>
          <ul className="feature-list">
            {featuresToShow.map(({name, value}) => (
              <li key={name}>
                <strong>{name}:</strong> {value}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  );
};

export default TransactionDetails;
