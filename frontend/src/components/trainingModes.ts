export type TrainingMode = 'spec4' | 'lingvist' | 'chat';

export interface TrainingModeOption {
  id: TrainingMode;
  label: string;
  shortLabel: string;
  description: string;
  accent: string;
}

export const TRAINING_MODES: TrainingModeOption[] = [
  {
    id: 'spec4',
    label: 'Revisão guiada',
    shortLabel: 'Revisão',
    description: 'Recupere a palavra com contexto, áudio e repetição espaçada.',
    accent: 'from-primary-400 to-indigo-500',
  },
  {
    id: 'lingvist',
    label: 'Cloze adaptativo',
    shortLabel: 'Cloze',
    description: 'Digite no meio da frase e receba pistas progressivas.',
    accent: 'from-teal-300 to-cyan-500',
  },
  {
    id: 'chat',
    label: 'Chat Coach',
    shortLabel: 'Conversa',
    description: 'Pratique produção livre com orientação em tempo real.',
    accent: 'from-violet-400 to-fuchsia-500',
  },
];
