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
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-gray-950/75 p-4 backdrop-blur-sm" role="dialog" aria-modal="true" aria-labelledby="edit-profile-title">
      <div className="surface-panel max-h-[90vh] w-full max-w-lg overflow-y-auto p-6 sm:p-7">
        <p className="eyebrow">Configurações</p>
        <h3 id="edit-profile-title" className="mb-6 mt-1 text-xl font-semibold text-white">
          Editar perfil
        </h3>

        <div className="space-y-4">
          <div>
            <label className="mb-2 block text-sm font-medium text-gray-300">
              Nome do perfil
            </label>
            <input
              type="text"
              value={editUsername}
              onChange={(event) => onUsernameChange(event.target.value)}
              className="input w-full"
              disabled={editLoading}
            />
          </div>

          <div>
            <label className="mb-2 block text-sm font-medium text-gray-300">
              Idioma de estudo
            </label>
            <div className="grid grid-cols-2 gap-2">
              {TARGET_LANGUAGES.map((lang) => (
                <button
                  key={lang.code}
                  type="button"
                  onClick={() => onTargetLanguageChange(lang.code)}
                  className={`min-h-11 rounded-xl px-3 py-2 text-sm font-semibold transition ${
                    editTargetLanguage === lang.code
                      ? 'bg-primary-500 text-white shadow-glow'
                      : 'border border-white/[0.08] bg-white/[0.04] text-gray-300 hover:bg-white/[0.08]'
                  }`}
                >
                  <span className="mr-1 rounded bg-white/10 px-1.5 py-0.5 text-[10px]">{lang.flag}</span>
                  {lang.name}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="mb-2 block text-sm font-medium text-gray-300">
              Idioma nativo
            </label>
            <select
              value={editNativeLanguage}
              onChange={(event) => onNativeLanguageChange(event.target.value)}
              className="input w-full"
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
            <label className="mb-2 block text-sm font-medium text-gray-300">
              Meta de vocabulário
            </label>
            <div className="rounded-2xl border border-white/[0.07] bg-gray-950/35 p-3">
              <div className="grid grid-cols-3 gap-2">
                {VOCABULARY_GOALS.map((goal) => (
                  <button
                    key={goal.rank}
                    type="button"
                    onClick={() => onWordGoalRankChange(goal.rank)}
                    className={`min-h-10 rounded-xl px-2 py-2 text-sm font-semibold transition ${
                      editWordGoalRank === goal.rank
                        ? 'bg-primary-500 text-white shadow-glow'
                        : 'bg-white/[0.04] text-gray-400 hover:bg-white/[0.08]'
                    }`}
                    disabled={editLoading}
                  >
                    {goal.label}
                  </button>
                ))}
              </div>
              <div className="mt-3 text-center text-xs text-gray-400">
                {VOCABULARY_GOALS.find((goal) => goal.rank === editWordGoalRank)?.description}
              </div>
            </div>
          </div>
        </div>

        <div className="flex gap-3 mt-6">
          <button
            onClick={onSave}
            disabled={!editUsername.trim() || editLoading}
            className="btn btn-primary flex-1"
          >
            {editLoading ? 'Salvando...' : 'Salvar alterações'}
          </button>
          <button
            onClick={onCancel}
            disabled={editLoading}
            className="btn btn-secondary flex-1"
          >
            Cancelar
          </button>
        </div>
      </div>
    </div>
  );
};

export default UserProfileEditModal;
