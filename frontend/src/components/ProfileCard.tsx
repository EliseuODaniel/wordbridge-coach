/** Profile Card Component */

import React from 'react';

export interface ProfileStats {
  mastered_words?: number;
  accuracy?: number;
}

export interface Profile {
  id: string;
  username: string;
  language_preference: string;
  target_language?: string;
  created_at: string;
  stats?: ProfileStats;
}

interface ProfileCardProps {
  profile: Profile;
  onStart: (profileId: string, mode: 'spec4' | 'lingvist' | 'chat') => void;
  onEdit: (profileId: string) => void;
  onDelete: (profileId: string) => void;
  isFocused?: boolean;
  selectedMode?: 'spec4' | 'lingvist' | 'chat';
}

const ProfileCard: React.FC<ProfileCardProps> = ({
  profile,
  onStart,
  onEdit,
  onDelete,
  isFocused = false,
  selectedMode = 'spec4'
}) => {
  const getLanguageName = (code: string) => {
    const languages: { [key: string]: { name: string; flag: string } } = {
      en: { name: 'English', flag: '🇺🇸' },
      fr: { name: 'French', flag: '🇫🇷' },
      pt: { name: 'Português', flag: '🇧🇷' },
      es: { name: 'Español', flag: '🇪🇸' }
    };
    return languages[code] || { name: code.toUpperCase(), flag: '🌐' };
  };

  const nativeLang = getLanguageName(profile.language_preference);
  const targetLang = profile.target_language ? getLanguageName(profile.target_language) : { name: 'English', flag: '🇺🇸' };

  const handleEditClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    onEdit(profile.id);
  };

  const handleDeleteClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    onDelete(profile.id);
  };

  const handleStartSpec4 = (e: React.MouseEvent) => {
    e.stopPropagation();
    onStart(profile.id, 'spec4');
  };

  const handleStartLingvist = (e: React.MouseEvent) => {
    e.stopPropagation();
    onStart(profile.id, 'lingvist');
  };

  const handleStartChat = (e: React.MouseEvent) => {
    e.stopPropagation();
    onStart(profile.id, 'chat');
  };

  return (
    <div
      className={`
        group relative bg-gray-800 rounded-lg p-4
        transition-all duration-200 border border-transparent
        hover:border-gray-600 hover:shadow-lg
        focus-within:ring-2 focus-within:ring-primary-500 focus-within:border-transparent
        ${isFocused ? 'ring-2 ring-primary-500 border-primary-500' : ''}
      `}
      data-testid={`profile-card-${profile.id}`}
    >
      {/* Main content */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex-1 min-w-0">
          <h3 className="text-lg font-semibold text-gray-100 truncate">
            {profile.username}
          </h3>

          <div className="text-sm text-gray-400 mt-1">
            Learning: {targetLang.flag} {targetLang.name} | Native: {nativeLang.flag} {nativeLang.name}
          </div>

          {profile.stats && (
            <div className="text-xs text-gray-500 mt-2">
              Mastered words: {profile.stats.mastered_words || 0} • Accuracy: {profile.stats.accuracy || 0}%
            </div>
          )}
        </div>
      </div>

      {/* Action buttons */}
      <div className="grid grid-cols-3 gap-2 mt-3">
        <button
          onClick={handleStartSpec4}
          className={`
            px-2 py-2 rounded-lg font-medium text-sm transition-all
            ${selectedMode === 'spec4'
              ? 'bg-primary-600 text-white shadow-lg'
              : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }
          `}
        >
          <div className="flex items-center justify-center gap-1">
            <span className="text-base">🎯</span>
            <span className="text-xs">Spec4</span>
          </div>
          <div className="text-xs opacity-75 mt-0.5">Multiple choice</div>
        </button>

        <button
          onClick={handleStartLingvist}
          className={`
            px-2 py-2 rounded-lg font-medium text-sm transition-all
            ${selectedMode === 'lingvist'
              ? 'bg-primary-600 text-white shadow-lg'
              : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }
          `}
        >
          <div className="flex items-center justify-center gap-1">
            <span className="text-base">✍️</span>
            <span className="text-xs">Lingvist</span>
          </div>
          <div className="text-xs opacity-75 mt-0.5">Cloze + hints</div>
        </button>

        <button
          onClick={handleStartChat}
          className={`
            px-2 py-2 rounded-lg font-medium text-sm transition-all
            ${selectedMode === 'chat'
              ? 'bg-purple-600 text-white shadow-lg'
              : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }
          `}
        >
          <div className="flex items-center justify-center gap-1">
            <span className="text-base">💬</span>
            <span className="text-xs">Chat</span>
          </div>
          <div className="text-xs opacity-75 mt-0.5">Conversational</div>
        </button>
      </div>

      {/* Edit/Delete buttons - only visible on hover */}
      <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200 flex gap-1">
        <button
          onClick={handleEditClick}
          className="p-1.5 text-gray-400 hover:text-gray-200 hover:bg-gray-700 rounded transition-colors"
          aria-label={`Edit ${profile.username}`}
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
          </svg>
        </button>

        <button
          onClick={handleDeleteClick}
          className="p-1.5 text-gray-400 hover:text-red-400 hover:bg-gray-700 rounded transition-colors"
          aria-label={`Delete ${profile.username}`}
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
          </svg>
        </button>
      </div>
    </div>
  );
};

export default ProfileCard;