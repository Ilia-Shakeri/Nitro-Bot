export const LANGUAGE_OPTIONS = [
  { code: 'en', label: 'English', flag: '🇺🇸' },
  { code: 'fa', label: 'Persian', flag: '🇮🇷' },
  { code: 'ar', label: 'Arabic', flag: '🇸🇦' },
  { code: 'ru', label: 'Russian', flag: '🇷🇺' },
] as const;

export type LanguageCode = (typeof LANGUAGE_OPTIONS)[number]['code'];

const STORAGE_KEY = 'nitro_language_selected';

export const hasSavedLanguageChoice = () =>
  typeof window !== 'undefined' && window.localStorage.getItem(STORAGE_KEY) === '1';

export const markLanguageChoiceSaved = () => {
  if (typeof window !== 'undefined') window.localStorage.setItem(STORAGE_KEY, '1');
};

export const isSupportedLanguage = (code: string | undefined): code is LanguageCode =>
  !!code && LANGUAGE_OPTIONS.some(item => item.code === code);

export const languageLabel = (code: string) => {
  const option = LANGUAGE_OPTIONS.find(item => item.code === code);
  return option ? `${option.flag} ${option.label}` : code.toUpperCase();
};
