import api from '../api';

export const getProcessGraph = () => api.get('/graph/');
export const visualizeProcessGraph = () => api.get('/graph/visualize');
