import api from '../api';

export const register = (data) => api.post('/auth/register', data, { headers: { 'Content-Type': 'application/json' } });
export const login = (data) => api.post('/auth/token', data, { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } });
export const getMe = () => api.get('/auth/me');
