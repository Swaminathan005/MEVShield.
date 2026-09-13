import React, { useState, useEffect } from 'react';
import { getStatus } from '../api/api';

const Header = () => {
  const [apiConnected, setApiConnected] = useState(false);
  const [modelLoaded, setModelLoaded] = useState(false);
  // We don't have a direct Exasol check, so we'll assume it's connected if API is connected
  const [exasolConnected, setExasolConnected] = useState(false);

  useEffect(() => {
    const checkConnection = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/health');
        if (response.ok) {
          const data = await response.json();
          setApiConnected(true);
          setModelLoaded(data.model_loaded);
          setExasolConnected(true); // Assuming Exasol is connected if API is up
        } else {
          setApiConnected(false);
          setModelLoaded(false);
          setExasolConnected(false);
        }
      } catch (error) {
        setApiConnected(false);
        setModelLoaded(false);
        setExasolConnected(false);
      }
    };

    checkConnection();
    const interval = setInterval(checkConnection, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="header">
      <div className="header-content">
        <h1>MEV SHIELD</h1>
        <p>Real-Time MEV Attack Detection</p>
        <div className="indicators">
          <div className={`indicator ${apiConnected ? 'connected' : 'disconnected'}`}>
            ● API Connected
          </div>
          <div className={`indicator ${exasolConnected ? 'connected' : 'disconnected'}`}>
            ● Exasol Connected
          </div>
          <div className={`indicator ${modelLoaded ? 'connected' : 'disconnected'}`}>
            ● Model Loaded
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
