// API Configuration with environment variable support
export const API_BASE_URL = process.env.REACT_APP_API_URL 
  ? process.env.REACT_APP_API_URL
  : `${window.location.protocol}//${window.location.host}/api/v1`;

export const WS_BASE_URL = process.env.REACT_APP_WS_URL
  ? process.env.REACT_APP_WS_URL
  : `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws`;

// Helper function to get full API URL
export const getApiUrl = (endpoint) => {
  return `${API_BASE_URL}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;
};

// Helper function to get WebSocket URL
export const getWebSocketUrl = (endpoint, token) => {
  const baseUrl = `${WS_BASE_URL}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;
  return token ? `${baseUrl}?token=${token}` : baseUrl;
};
