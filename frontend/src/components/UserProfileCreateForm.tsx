import React from 'react';

import { NATIVE_LANGUAGES, TARGET_LANGUAGES, VOCABULARY_GOALS } from './userSelectionConfig';

interface UserProfileCreateFormProps {
  loading: boolean;
  nativeLanguage: string;
  newUsername: string;
  targetLanguage: string;
  wordGoalRank: number;
  onNativeLanguageChange: (value: string) => void;
  onSubmit: (event: React.FormEvent) => Promise<void>;
  onTargetLanguageChange: (value: string) => void;
  onUsernameChange: (value: string) => void;
  onWordGoalRankChange: (value: number) => void;
}

const UserProfileCreateForm: React.FC<UserProfileCreateFormProps> = ({
  loading,
  nativeLanguage,
  newUsername,
  targetLanguage,
  wordGoalRank,
  onNativeLanguageChange,
  onSubmit,
  onTargetLanguageChange,
  onUsernameChange,
  onWordGoalRankChange,
}) => {
  return (
    <form onSubmit={onSubmit} className="space-y-4">
      <div>
        <input
          type="text"
          value={newUsername}
          onChange={(event) => onUsernameChange(event.target.value)}
          placeholder="Enter your name"
          className="w-full px-4 py-3 bg-gray-700 text-gray-100 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 placeholder-gray-500"
          disabled={loading}
          autoComplete="name"
          data-testid="profile-create-name"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-400 mb-2">
          I want to learn:
        </label>
        <div className="flex gap-2 bg-gray-700 rounded-lg p-1">
          {TARGET_LANGUAGES.map((lang) => (
            <button
              key={lang.code}
              type="button"
              onClick={() => onTargetLanguageChange(lang.code)}
              className={`
                flex-1 px-3 py-2 rounded-md font-medium transition-all duration-200 text-sm
                ${targetLanguage === lang.code
                  ? 'bg-primary-600 text-white shadow-sm'
                  : 'text-gray-300 hover:text-white hover:bg-gray-600'
                }
              `}
              data-testid={`profile-target-${lang.code}`}
            >
              <span className="mr-2">{lang.flag}</span>
              {lang.name}
            </button>
          ))}
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-400 mb-2">
          My native language:
        </label>
        <select
          value={nativeLanguage}
          onChange={(event) => onNativeLanguageChange(event.target.value)}
          className="w-full px-4 py-2 bg-gray-700 text-gray-100 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 border border-gray-600"
          disabled={loading}
          data-testid="profile-native-lang"
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
        <div className="bg-gray-700 rounded-lg p-3 border border-gray-600" data-testid="profile-goal-options">
          <div className="grid grid-cols-2 gap-2">
            {VOCABULARY_GOALS.map((goal) => (
              <button
                key={goal.rank}
                type="button"
                onClick={() => onWordGoalRankChange(goal.rank)}
                className={`px-3 py-2 text-sm rounded transition-colors ${
                  wordGoalRank === goal.rank
                    ? 'bg-blue-600 text-white font-medium'
                    : 'bg-gray-600 text-gray-300 hover:bg-gray-500'
                }`}
                disabled={loading}
                aria-pressed={wordGoalRank === goal.rank}
                data-testid={`profile-goal-${goal.rank}`}
              >
                {goal.label}
              </button>
            ))}
          </div>
          <div className="mt-2 text-xs text-gray-400 text-center" data-testid="profile-goal-description">
            {VOCABULARY_GOALS.find((goal) => goal.rank === wordGoalRank)?.description}
          </div>
        </div>
      </div>

      <button
        type="submit"
        disabled={!newUsername.trim() || loading}
        className="w-full px-4 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 focus:ring-offset-gray-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
        data-testid="profile-create-start"
      >
        {loading ? (
          <div className="flex items-center justify-center">
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
            Creating Profile...
          </div>
        ) : (
          'Create & Start Learning'
        )}
      </button>
    </form>
  );
};

export default UserProfileCreateForm;
