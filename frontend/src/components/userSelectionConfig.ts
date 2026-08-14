import { statsService } from '../services/stats';
import type { ProfileStats } from './ProfileCard';

export const TARGET_LANGUAGES = [
  { code: 'en', name: 'English', flag: 'EN' },
  { code: 'fr', name: 'Français', flag: 'FR' },
];

export const NATIVE_LANGUAGES = [
  { code: 'pt', name: 'Português', flag: 'PT' },
  { code: 'es', name: 'Español', flag: 'ES' },
  { code: 'fr', name: 'Français', flag: 'FR' },
  { code: 'en', name: 'English', flag: 'EN' },
];

export const VOCABULARY_GOALS = [
  { rank: 100, label: '100', description: 'Primeiro marco com palavras de alta frequência' },
  { rank: 500, label: '500', description: 'Base prática para situações cotidianas' },
  { rank: 1500, label: '1.500', description: 'Expansão do vocabulário de uso diário' },
  { rank: 3000, label: '3.000', description: 'Cobertura ampla para leitura e conversação' },
  { rank: 5000, label: '5.000', description: 'Vocabulário avançado e mais expressivo' },
  { rank: 10000, label: '10.000', description: 'Meta de longo prazo para alta cobertura lexical' },
];

export function buildProfileStats(
  stats: Awaited<ReturnType<typeof statsService.getBasicStats>>
): ProfileStats {
  return {
    mastered_words: stats.mature_count,
    accuracy: Math.round(stats.accuracy_today * 100),
  };
}
