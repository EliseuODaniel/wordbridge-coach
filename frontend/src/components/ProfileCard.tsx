/** Profile Card Component */

import React from 'react';
import ModeGlyph from './ModeGlyph';
import type { TrainingMode } from './trainingModes';

export interface ProfileStats {
  mastered_words?: number;
  accuracy?: number;
}

export interface Profile {
  id: string;
  username: string;
  language_preference: string;
  target_language: string;
  word_goal_rank: number;
  created_at: string;
  stats?: ProfileStats;
}

interface ProfileCardProps {
  profile: Profile;
  onStart: (profileId: string, mode: TrainingMode) => void;
  onEdit: (profileId: string) => void;
  onDelete: (profileId: string) => void;
  isFocused?: boolean;
  selectedMode?: TrainingMode;
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
    const languages: { [key: string]: { name: string; short: string } } = {
      en: { name: 'English', short: 'EN' },
      fr: { name: 'Français', short: 'FR' },
      pt: { name: 'Português', short: 'PT' },
      es: { name: 'Español', short: 'ES' }
    };
    return languages[code] || { name: code.toUpperCase(), short: code.toUpperCase() };
  };

  const nativeLang = getLanguageName(profile.language_preference);
  const targetLang = getLanguageName(profile.target_language);

  const handleEditClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    onEdit(profile.id);
  };

  const handleDeleteClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    onDelete(profile.id);
  };

  const handleStart = (e: React.MouseEvent, mode: TrainingMode) => {
    e.stopPropagation();
    onStart(profile.id, mode);
  };

  const modes: Array<{ id: TrainingMode; label: string }> = [
    { id: 'spec4', label: 'Revisão' },
    { id: 'lingvist', label: 'Cloze' },
    { id: 'chat', label: 'Conversa' },
  ];

  return (
    <article
      className={`group relative rounded-2xl border p-4 transition duration-200 hover:-translate-y-0.5 hover:bg-white/[0.055] ${isFocused ? 'border-primary-400 bg-primary-500/10 shadow-glow' : 'border-white/[0.08] bg-white/[0.03]'}`}
      data-testid="profile-card"
      data-profile-id={profile.id}
    >
      <div className="flex items-start gap-3">
        <div className="flex size-11 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-primary-400/90 to-teal-400/80 text-sm font-bold text-white shadow-lg">
          {profile.username.slice(0, 2).toUpperCase()}
        </div>
        <div className="min-w-0 flex-1 pr-24">
          <h3 className="truncate text-base font-semibold text-white">{profile.username}</h3>
          <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-gray-400">
            <span className="status-pill min-h-6 px-2 py-0.5"><strong className="text-gray-200">{targetLang.short}</strong> {targetLang.name}</span>
            <span aria-hidden="true">←</span>
            <span>{nativeLang.short} nativo</span>
          </div>
          {profile.stats && (
            <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-gray-500">
              <span><strong className="font-semibold text-gray-300">{profile.stats.mastered_words || 0}</strong> dominadas</span>
              <span><strong className="font-semibold text-gray-300">{profile.stats.accuracy || 0}%</strong> de precisão</span>
            </div>
          )}
        </div>
      </div>

      <div className="mt-4 grid grid-cols-3 gap-2">
        {modes.map((mode) => (
          <button
            key={mode.id}
            type="button"
            onClick={(event) => handleStart(event, mode.id)}
            className={`inline-flex min-h-10 items-center justify-center gap-1.5 rounded-xl px-2 text-xs font-semibold transition ${selectedMode === mode.id ? 'bg-primary-500 text-white shadow-glow' : 'border border-white/[0.07] bg-white/[0.035] text-gray-300 hover:border-white/20 hover:bg-white/[0.07]'}`}
            aria-label={`Abrir ${mode.label} para ${profile.username}`}
          >
            <ModeGlyph mode={mode.id} className="size-4" />
            <span className="hidden sm:inline">{mode.label}</span>
          </button>
        ))}
      </div>

      <div className="absolute right-3 top-3 flex gap-1">
        <button
          onClick={handleEditClick}
          className="icon-button rounded-lg"
          aria-label={`Editar ${profile.username}`}
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
          </svg>
        </button>

        <button
          onClick={handleDeleteClick}
          className="icon-button rounded-lg hover:border-red-400/30 hover:bg-red-500/10 hover:text-red-300"
          aria-label={`Excluir ${profile.username}`}
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
          </svg>
        </button>
      </div>
    </article>
  );
};

export default ProfileCard;
