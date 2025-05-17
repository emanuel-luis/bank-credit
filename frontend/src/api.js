import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || `http://${import.meta.env.VITE_BACKEND_HOST || 'localhost'}:${import.meta.env.VITE_BACKEND_PORT || '8000'}`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add a request interceptor to include JWT if present
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default api;
