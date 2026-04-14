import React from 'react';

import { NATIVE_LANGUAGES, TARGET_LANGUAGES, VOCABULARY_GOALS } from './userSelectionConfig';

interface UserProfileEditModalProps {
  editLoading: boolean;
  editNativeLanguage: string;
  editTargetLanguage: string;
  editUsername: string;
  editWordGoalRank: number;
  isOpen: boolean;
  onCancel: () => void;
  onNativeLanguageChange: (value: string) => void;
  onSave: () => Promise<void>;
  onTargetLanguageChange: (value: string) => void;
  onUsernameChange: (value: string) => void;
  onWordGoalRankChange: (value: number) => void;
}

const UserProfileEditModal: React.FC<UserProfileEditModalProps> = ({
  editLoading,
  editNativeLanguage,
  editTargetLanguage,
  editUsername,
  editWordGoalRank,
  isOpen,
  onCancel,
  onNativeLanguageChange,
  onSave,
  onTargetLanguageChange,
  onUsernameChange,
  onWordGoalRankChange,
}) => {
  if (!isOpen) {
    return null;
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-gray-800 rounded-lg p-6 max-w-md w-full">
        <h3 className="text-lg font-semibold text-gray-100 mb-4">
          Edit Profile
        </h3>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">
              Profile Name
            </label>
            <input
              type="text"
              value={editUsername}
              onChange={(event) => onUsernameChange(event.target.value)}
              className="w-full px-3 py-2 bg-gray-700 text-gray-100 rounded focus:outline-none focus:ring-2 focus:ring-primary-500"
              disabled={editLoading}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">
              Target Language:
            </label>
            <div className="grid grid-cols-2 gap-2">
              {TARGET_LANGUAGES.map((lang) => (
                <button
                  key={lang.code}
                  type="button"
                  onClick={() => onTargetLanguageChange(lang.code)}
                  className={`px-3 py-2 text-sm rounded font-medium transition-colors ${
                    editTargetLanguage === lang.code
                      ? 'bg-primary-600 text-white'
                      : 'bg-gray-600 text-gray-300 hover:bg-gray-500'
                  }`}
                >
                  <span className="mr-1">{lang.flag}</span>
                  {lang.name}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">
              Native Language:
            </label>
            <select
              value={editNativeLanguage}
              onChange={(event) => onNativeLanguageChange(event.target.value)}
              className="w-full px-3 py-2 bg-gray-600 text-gray-100 rounded focus:outline-none focus:ring-2 focus:ring-primary-500"
              disabled={editLoading}
            >
              {NATIVE_LANGUAGES.map((lang) => (
                <option key={lang.code} value={lang.code}>
                  {lang.flag} {lang.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">
              My vocabulary goal:
            </label>
            <div className="bg-gray-700 rounded-lg p-3 border border-gray-600">
              <div className="grid grid-cols-2 gap-2">
                {VOCABULARY_GOALS.map((goal) => (
                  <button
                    key={goal.rank}
                    type="button"
                    onClick={() => onWordGoalRankChange(goal.rank)}
                    className={`px-3 py-2 text-sm rounded transition-colors ${
                      editWordGoalRank === goal.rank
                        ? 'bg-blue-600 text-white font-medium'
                        : 'bg-gray-600 text-gray-300 hover:bg-gray-500'
                    }`}
                    disabled={editLoading}
                  >
                    {goal.label}
                  </button>
                ))}
              </div>
              <div className="mt-2 text-xs text-gray-400 text-center">
                {VOCABULARY_GOALS.find((goal) => goal.rank === editWordGoalRank)?.description}
              </div>
            </div>
          </div>
        </div>

        <div className="flex gap-3 mt-6">
          <button
            onClick={onSave}
            disabled={!editUsername.trim() || editLoading}
            className="flex-1 px-4 py-2 bg-primary-600 text-white rounded hover:bg-primary-700 disabled:opacity-50 transition-colors"
          >
            {editLoading ? 'Saving...' : 'Save Changes'}
          </button>
          <button
            onClick={onCancel}
            disabled={editLoading}
            className="flex-1 px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-500 disabled:opacity-50 transition-colors"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
};

export default UserProfileEditModal;
