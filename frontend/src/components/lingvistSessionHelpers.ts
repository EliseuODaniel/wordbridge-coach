export const normalizeLingvistText = (text: string): string => {
  return text.toLowerCase().trim().replace(/\s+/g, ' ');
};

export const isTranslationAvailable = (translation: string | null | undefined): boolean => {
  return translation != null && typeof translation === 'string' && translation.trim().length > 0;
};
