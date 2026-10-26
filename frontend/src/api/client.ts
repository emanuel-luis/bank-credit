import axios from 'axios';

const TOKEN_KEY = 'access_token';

export const tokenStore = {
  get: () => localStorage.getItem(TOKEN_KEY),
  set: (token: string) => localStorage.setItem(TOKEN_KEY, token),
  clear: () => localStorage.removeItem(TOKEN_KEY),
};

const api = axios.create({ baseURL: import.meta.env.VITE_API_URL ?? '/api' });

api.interceptors.request.use((config) => {
  const token = tokenStore.get();
  if (token) config.headers.set('Authorization', `Bearer ${token}`);
  return config;
});

api.interceptors.response.use(undefined, (error: unknown) => {
  // A wrong password also answers 401; only an expired or invalid session redirects.
  if (
    axios.isAxiosError(error) &&
    error.response?.status === 401 &&
    tokenStore.get() &&
    !window.location.pathname.startsWith('/login')
  ) {
    tokenStore.clear();
    window.location.assign('/login');
  }
  return Promise.reject(error);
});

export default api;
