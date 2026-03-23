/**
 * LLM Settings Panel
 *
 * Allows users to select different models for Chat vs Teacher analysis.
 * Displays model profiles with metadata (VRAM, quality, speed tiers).
 */

import React, { useState, useEffect } from 'react';
import { getApiErrorMessage, llmProfilesApi, type LLMProfile } from '../services/api';

interface LLMSettingsPanelProps {
  userId?: string;
  isOpen: boolean;
  onClose: () => void;
}

export const LLMSettingsPanel: React.FC<LLMSettingsPanelProps> = ({ userId, isOpen, onClose }) => {
  const [profiles, setProfiles] = useState<LLMProfile[]>([]);
  const [chatModel, setChatModel] = useState<string>('');
  const [teacherModel, setTeacherModel] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Load profiles and preferences on mount
  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        setError(null);

        // Load available profiles
        const profilesData = await llmProfilesApi.getProfiles(userId);
        setProfiles(profilesData.profiles);

        // Load user preferences
        const prefsData = await llmProfilesApi.getMyPreferences(userId);
        setChatModel(prefsData.chat_model_profile);
        setTeacherModel(prefsData.teacher_model_profile);

      } catch (err) {
        console.error('[LLM_SETTINGS] Failed to load data:', err);
        setError(getApiErrorMessage(err, 'Failed to load LLM settings'));
      } finally {
        setLoading(false);
      }
    };

    if (isOpen) {
      loadData();
    }
  }, [isOpen, userId]);

  // Save preferences
  const handleSave = async () => {
    try {
      setSaving(true);
      setError(null);
      setSuccessMessage(null);

      await llmProfilesApi.updateMyPreferences({
        chat_model_profile: chatModel,
        teacher_model_profile: teacherModel,
      }, userId);

      setSuccessMessage('Model preferences saved successfully!');
      setTimeout(() => setSuccessMessage(null), 3000);

    } catch (err) {
      console.error('[LLM_SETTINGS] Failed to save:', err);
      setError(getApiErrorMessage(err, 'Failed to save preferences'));
    } finally {
      setSaving(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-gray-800 rounded-xl shadow-xl border border-gray-700 p-6 max-w-2xl w-full mx-4">
        {/* Header */}
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold text-gray-100">⚙️ LLM Settings</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-200 text-2xl leading-none"
          >
            ×
          </button>
        </div>

        {/* Loading state */}
        {loading && (
          <div className="text-center py-8">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500"></div>
            <p className="mt-2 text-gray-400">Loading settings...</p>
          </div>
        )}

        {/* Error state */}
        {error && (
          <div className="bg-red-900 bg-opacity-20 border border-red-700 text-red-200 px-4 py-3 rounded-lg mb-4">
            {error}
          </div>
        )}

        {/* Success message */}
        {successMessage && (
          <div className="bg-green-900 bg-opacity-20 border border-green-700 text-green-200 px-4 py-3 rounded-lg mb-4">
            ✓ {successMessage}
          </div>
        )}

        {/* Settings form */}
        {!loading && (
          <div className="space-y-6">
            {/* Chat Model Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                💬 Chat Model
                <span className="ml-2 text-xs text-gray-400">Used for conversational responses</span>
              </label>
              <select
                value={chatModel}
                onChange={(e) => setChatModel(e.target.value)}
                disabled={saving}
                className="w-full px-4 py-2 bg-gray-700 text-gray-100 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 border border-gray-600 disabled:opacity-50"
              >
                {profiles.map((profile) => (
                  <option key={profile.id} value={profile.id}>
                    {profile.name} ({profile.quality_tier} quality, {profile.speed_tier} speed) - {profile.estimated_vram}
                  </option>
                ))}
              </select>
              {profiles.find(p => p.id === chatModel) && (
                <p className="mt-1 text-xs text-gray-400">
                  {profiles.find(p => p.id === chatModel)?.description}
                </p>
              )}
            </div>

            {/* Teacher Model Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                👨‍🏫 Teacher Model
                <span className="ml-2 text-xs text-gray-400">Used for grammar/corrections analysis</span>
              </label>
              <select
                value={teacherModel}
                onChange={(e) => setTeacherModel(e.target.value)}
                disabled={saving}
                className="w-full px-4 py-2 bg-gray-700 text-gray-100 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 border border-gray-600 disabled:opacity-50"
              >
                {profiles.map((profile) => (
                  <option key={profile.id} value={profile.id}>
                    {profile.name} ({profile.quality_tier} quality, {profile.speed_tier} speed) - {profile.estimated_vram}
                  </option>
                ))}
              </select>
              {profiles.find(p => p.id === teacherModel) && (
                <p className="mt-1 text-xs text-gray-400">
                  {profiles.find(p => p.id === teacherModel)?.description}
                </p>
              )}
            </div>

            {/* Info box */}
            <div className="bg-blue-900 bg-opacity-20 border border-blue-700 text-blue-200 px-4 py-3 rounded-lg text-sm">
              <p className="font-medium mb-1">💡 Tip:</p>
              <ul className="list-disc list-inside space-y-1 text-xs">
                <li><strong>Chat:</strong> Faster models = quicker responses</li>
                <li><strong>Teacher:</strong> Higher quality = better grammar analysis</li>
                <li>You can use different models for each!</li>
              </ul>
            </div>

            {/* Actions */}
            <div className="flex justify-end gap-3 pt-4 border-t border-gray-700">
              <button
                onClick={onClose}
                disabled={saving}
                className="px-4 py-2 bg-gray-700 text-gray-300 rounded-lg hover:bg-gray-600 disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                onClick={handleSave}
                disabled={saving}
                className="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 flex items-center gap-2"
              >
                {saving ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    Saving...
                  </>
                ) : (
                  'Save Preferences'
                )}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
