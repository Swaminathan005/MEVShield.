import React, { useState, useEffect } from 'react';
import { getStatus } from '../api/api';
import { startStream, pauseStream, resetStream } from '../api/api';

const Controls = () => {
  const [status, setStatus] = useState('STOPPED');
  const [speed, setSpeed] = useState('1x'); // 1x, 2x, 5x

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const res = await getStatus();
        setStatus(res.status);
      } catch (error) {
        console.error('Failed to fetch status:', error);
      }
    };

    fetchStatus();
    const interval = setInterval(fetchStatus, 1000);
    return () => clearInterval(interval);
  }, []);

  const handleStart = async () => {
    await startStream();
    // status will be updated by the effect
  };

  const handlePause = async () => {
    await pauseStream();
  };

  const handleReset = async () => {
    await resetStream();
  };

  return (
    <section className="controls">
      <div className="control-buttons">
        <button onClick={handleStart} disabled={status === 'RUNNING'}>
          ▶ START
        </button>
        <button onClick={handlePause} disabled={status !== 'RUNNING'}>
          ⏸ PAUSE
        </button>
        <button onClick={handleReset} disabled={status === 'STOPPED'}>
          ↻ RESET
        </button>
      </div>
      <div className="speed-control">
        <span>Replay Speed:</span>
        <button onClick={() => setSpeed('1x')} className={speed === '1x' ? 'active' : ''}>
          1x
        </button>
        <button onClick={() => setSpeed('2x')} className={speed === '2x' ? 'active' : ''}>
          2x
        </button>
        <button onClick={() => setSpeed('5x')} className={speed === '5x' ? 'active' : ''}>
          5x
        </button>
      </div>
    </section>
  );
};

export default Controls;
