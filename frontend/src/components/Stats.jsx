import React, { useState, useEffect } from 'react';
import { getStatus, getStatistics } from '../api/api';

const Stats = () => {
  const [stats, setStats] = useState({
    total_scanned: 0,
    high_risk: 0,
    normal: 0,
    attack_rate: 0
  });
  const [status, setStatus] = useState('STOPPED');

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [statusRes, statsRes] = await Promise.all([
          getStatus(),
          getStatistics()
        ]);
        setStatus(statusRes.status);
        setStats(statsRes);
      } catch (error) {
        console.error('Failed to fetch stats:', error);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 1000); // every second
    return () => clearInterval(interval);
  }, []);

  return (
    <section className="stats">
      <div className="stat-card">
        <h3>TRANSACTIONS SCANNED</h3>
        <p>{stats.total_scanned.toLocaleString()}</p>
      </div>
      <div className="stat-card">
        <h3>HIGH RISK</h3>
        <p>{stats.high_risk.toLocaleString()}</p>
      </div>
      <div className="stat-card">
        <h3>NORMAL</h3>
        <p>{stats.normal.toLocaleString()}</p>
      </div>
      <div className="stat-card">
        <h3>ATTACK RATE</h3>
        <p>{stats.attack_rate.toFixed(2)}%</p>
      </div>
    </section>
  );
};

export default Stats;
