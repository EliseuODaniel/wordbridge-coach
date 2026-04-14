import api from './apiClient';

export interface LLMProfile {
  id: string;
  name: string;
  provider: string;
  model: string;
  context_window: number;
  supports_streaming: boolean;
  supports_json: boolean;
  estimated_vram: string;
  quality_tier: string;
  speed_tier: string;
  description: string;
}

export interface UserLLMPreferences {
  id: string;
  user_id: string;
  chat_model_profile: string;
  teacher_model_profile: string;
  created_at: string;
  updated_at: string;
}

export interface UpdateLLMPreferencesRequest {
  chat_model_profile?: string;
  teacher_model_profile?: string;
}

export const llmProfilesApi = {
  getProfiles: async (userId?: string): Promise<{ profiles: LLMProfile[] }> => {
    const params = userId ? { user_id: userId } : {};
    const response = await api.get('/api/v1/llm-profiles', { params });
    return response.data;
  },

  getMyPreferences: async (userId?: string): Promise<UserLLMPreferences> => {
    const params = userId ? { user_id: userId } : {};
    const response = await api.get('/api/v1/users/me/llm-preferences', { params });
    return response.data;
  },

  updateMyPreferences: async (
    requestData: UpdateLLMPreferencesRequest,
    userId?: string
  ): Promise<UserLLMPreferences> => {
    const params = userId ? { user_id: userId } : {};
    const response = await api.put('/api/v1/users/me/llm-preferences', requestData, { params });
    return response.data;
  },
};
