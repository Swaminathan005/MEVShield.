const API_BASE_URL = 'http://localhost:8000';

export const startStream = async () => {
  const response = await fetch(`${API_BASE_URL}/api/start`, {
    method: 'POST',
  });
  return response.json();
};

export const pauseStream = async () => {
  const response = await fetch(`${API_BASE_URL}/api/pause`, {
    method: 'POST',
  });
  return response.json();
};

export const resetStream = async () => {
  const response = await fetch(`${API_BASE_URL}/api/reset`, {
    method: 'POST',
  });
  return response.json();
};

export const getStatus = async () => {
  const response = await fetch(`${API_BASE_URL}/api/status`);
  return response.json();
};

export const getTransactions = async () => {
  const response = await fetch(`${API_BASE_URL}/api/transactions`);
  return response.json();
};

export const getStatistics = async () => {
  const response = await fetch(`${API_BASE_URL}/api/statistics`);
  return response.json();
};
