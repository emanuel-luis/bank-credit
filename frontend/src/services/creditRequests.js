import api from '../api';

export const createCreditRequest = (data) => api.post('/requests/', data);
export const getCreditRequests = () => api.get('/requests/');
export const getCreditRequestById = (id) => api.get(`/requests/${id}`);
export const updateCreditRequestStatus = (id, status) => api.patch(`/requests/${id}/status`, { status });
export const getRequestHistory = (id) => api.get(`/requests/${id}/history`);
export const getRequestStatus = (id) => api.get(`/requests/${id}/status`);
export const getEstimatedTime = (id) => api.get(`/requests/${id}/estimated-time`);
export const routeRequestToNext = (id) => api.post(`/requests/${id}/route`);
