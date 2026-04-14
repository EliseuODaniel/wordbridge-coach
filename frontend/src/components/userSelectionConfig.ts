import { statsService } from '../services/stats';
import type { ProfileStats } from './ProfileCard';

export const TARGET_LANGUAGES = [
  { code: 'en', name: 'English', flag: '🇺🇸' },
  { code: 'fr', name: 'French', flag: '🇫🇷' },
];

export const NATIVE_LANGUAGES = [
  { code: 'pt', name: 'Português', flag: '🇧🇷' },
  { code: 'es', name: 'Español', flag: '🇪🇸' },
  { code: 'fr', name: 'Français', flag: '🇫🇷' },
  { code: 'en', name: 'English', flag: '🇺🇸' },
];

export const VOCABULARY_GOALS = [
  { rank: 100, label: '100 words', description: 'Basic conversations' },
  { rank: 500, label: '500 words', description: 'Elementary level' },
  { rank: 1500, label: '1500 words', description: 'Intermediate level' },
  { rank: 3000, label: '3000 words', description: 'Advanced level' },
  { rank: 5000, label: '5000 words', description: 'Fluent conversations' },
  { rank: 10000, label: '10000 words', description: 'Near-native vocabulary' },
];

export function buildProfileStats(
  stats: Awaited<ReturnType<typeof statsService.getBasicStats>>
): ProfileStats {
  return {
    mastered_words: stats.mature_count,
    accuracy: Math.round(stats.accuracy_today * 100),
  };
}
