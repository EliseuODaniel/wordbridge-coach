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
    <form onSubmit={onSubmit} className="space-y-5">
      <div>
        <label htmlFor="profile-name" className="mb-2 block text-sm font-medium text-gray-300">Como devemos chamar você?</label>
        <input
          id="profile-name"
          type="text"
          value={newUsername}
          onChange={(event) => onUsernameChange(event.target.value)}
          placeholder="Seu nome ou apelido"
          className="input w-full"
          disabled={loading}
          autoComplete="name"
          data-testid="profile-create-name"
        />
      </div>

      <div>
        <label className="mb-2 block text-sm font-medium text-gray-300">
          Idioma que quero aprender
        </label>
        <div className="grid grid-cols-2 gap-2 rounded-2xl border border-white/[0.07] bg-gray-950/35 p-1.5">
          {TARGET_LANGUAGES.map((lang) => (
            <button
              key={lang.code}
              type="button"
              onClick={() => onTargetLanguageChange(lang.code)}
              className={`
                min-h-11 rounded-xl px-3 py-2 font-semibold transition duration-200 text-sm
                ${targetLanguage === lang.code
                  ? 'bg-primary-500 text-white shadow-glow'
                  : 'text-gray-400 hover:bg-white/[0.06] hover:text-white'
                }
              `}
              data-testid={`profile-target-${lang.code}`}
            >
              <span className="mr-2 rounded-md bg-white/10 px-1.5 py-0.5 text-[10px] tracking-wider">{lang.flag}</span>
              {lang.name}
            </button>
          ))}
        </div>
      </div>

      <div>
        <label htmlFor="profile-native-language" className="mb-2 block text-sm font-medium text-gray-300">
          Meu idioma nativo
        </label>
        <select
          id="profile-native-language"
          value={nativeLanguage}
          onChange={(event) => onNativeLanguageChange(event.target.value)}
          className="input w-full appearance-none"
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
        <label className="mb-2 block text-sm font-medium text-gray-300">
          Meta inicial de vocabulário
        </label>
        <div className="rounded-2xl border border-white/[0.07] bg-gray-950/35 p-3" data-testid="profile-goal-options">
          <div className="grid grid-cols-3 gap-2">
            {VOCABULARY_GOALS.map((goal) => (
              <button
                key={goal.rank}
                type="button"
                onClick={() => onWordGoalRankChange(goal.rank)}
                className={`min-h-10 rounded-xl px-2 py-2 text-sm font-semibold transition ${
                  wordGoalRank === goal.rank
                    ? 'bg-primary-500 text-white shadow-glow'
                    : 'bg-white/[0.045] text-gray-400 hover:bg-white/[0.08] hover:text-gray-200'
                }`}
                disabled={loading}
                aria-pressed={wordGoalRank === goal.rank}
                data-testid={`profile-goal-${goal.rank}`}
              >
                {goal.label}
              </button>
            ))}
          </div>
          <div className="mt-3 min-h-5 text-center text-xs text-gray-400" data-testid="profile-goal-description">
            {VOCABULARY_GOALS.find((goal) => goal.rank === wordGoalRank)?.description}
          </div>
        </div>
      </div>

      <button
        type="submit"
        disabled={!newUsername.trim() || loading}
        className="btn btn-primary w-full"
        data-testid="profile-create-start"
      >
        {loading ? (
          <div className="flex items-center justify-center">
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
            Criando perfil...
          </div>
        ) : (
          'Criar perfil e começar'
        )}
      </button>
    </form>
  );
};

export default UserProfileCreateForm;
