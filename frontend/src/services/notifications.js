import api from '../api';

export const getNotifications = () => api.get('/notifications/');
export const createNotification = (data) => api.post('/notifications/', data);
export const getNotificationById = (id) => api.get(`/notifications/${id}`);
export const markNotificationAsRead = (id) => api.patch(`/notifications/${id}/read`);
export const markAllNotificationsAsRead = () => api.patch('/notifications/read-all');
export const getUnreadNotificationsCount = () => api.get('/notifications/unread-count');
export const deleteNotification = (id) => api.delete(`/notifications/${id}`);
