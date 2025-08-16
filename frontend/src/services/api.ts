import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8001';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const assetsApi = {
  getAll: () => apiClient.get('/api/assets'),
  getById: (id: string) => apiClient.get(`/api/assets/${id}`),
  create: (asset: any) => apiClient.post('/api/assets', asset),
  update: (id: string, asset: any) => apiClient.put(`/api/assets/${id}`, asset),
  delete: (id: string) => apiClient.delete(`/api/assets/${id}`),
};

export const healthCheck = () => apiClient.get('/health');