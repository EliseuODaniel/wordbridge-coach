import api from './apiClient';
import type { JsonObject } from './apiErrors';

export interface User {
  id: string;
  username: string;
  language_preference: string;
  target_language: string;
  word_goal_rank: number;
  mode: string;
  created_at: string;
}

export interface CreateUserRequest {
  username: string;
  language_preference?: string;
  target_language?: string;
  word_goal_rank?: number;
  mode?: string;
}

export interface UpdateUserRequest {
  username?: string;
  language_preference?: string;
  target_language?: string;
  word_goal_rank?: number;
  mode?: string;
}

export const usersApi = {
  listUsers: async (): Promise<User[]> => {
    const response = await api.get('/api/v1/users/');
    return response.data;
  },

  createUser: async (userData: CreateUserRequest): Promise<User> => {
    const response = await api.post('/api/v1/users/', userData);
    return response.data;
  },

  getUser: async (userId: string): Promise<User> => {
    const response = await api.get(`/api/v1/users/${userId}`);
    return response.data;
  },

  updateUser: async (userId: string, userData: UpdateUserRequest): Promise<User> => {
    const response = await api.patch(`/api/v1/users/${userId}`, userData);
    return response.data;
  },

  deleteUser: async (userId: string): Promise<{ message: string; deleted_records: JsonObject }> => {
    const response = await api.delete(`/api/v1/users/${userId}`);
    return response.data;
  },
};
