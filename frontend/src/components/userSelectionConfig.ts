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
  { rank: 100, label: '100 words', description: 'First high-frequency vocabulary target' },
  { rank: 500, label: '500 words', description: 'Broader high-frequency vocabulary target' },
  { rank: 1500, label: '1500 words', description: 'Everyday vocabulary expansion' },
  { rank: 3000, label: '3000 words', description: 'Wider vocabulary coverage' },
  { rank: 5000, label: '5000 words', description: 'Extended vocabulary target' },
  { rank: 10000, label: '10000 words', description: 'Long-term vocabulary target' },
];

export function buildProfileStats(
  stats: Awaited<ReturnType<typeof statsService.getBasicStats>>
): ProfileStats {
  return {
    mastered_words: stats.mature_count,
    accuracy: Math.round(stats.accuracy_today * 100),
  };
}
