import api from './apiClient';

export const healthApi = {
  checkHealth: async (): Promise<{ status: string; service: string }> => {
    const response = await api.get('/health');
    return response.data;
  },
};
