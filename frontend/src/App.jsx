import React, { useState } from 'react';
import Header from './components/Header';
import Stats from './components/Stats';
import Controls from './components/Controls';
import TransactionTable from './components/TransactionTable';
import TransactionDetails from './components/TransactionDetails';
import TechnicalDetails from './components/TechnicalDetails';
import './index.css'; // Our custom CSS

function App() {
  const [selectedTransaction, setSelectedTransaction] = useState(null);

  return (
    <div className="App">
      <Header />
      <main className="main-content">
        <Stats />
        <Controls />
        <TransactionTable 
          onTransactionSelect={setSelectedTransaction} 
        />
        <TransactionDetails 
          transaction={selectedTransaction} 
        />
        <TechnicalDetails />
      </main>
    </div>
  );
}

export default App;
