import type { TFunction } from 'i18next';

const ERROR_MAP: Record<string, string> = {
  'Music file must be MP3 or WAV': 'Music file must be MP3 or WAV',
  'Cover image must be JPG, PNG, or WEBP': 'Cover image must be JPG, PNG, or WEBP',
  'Please fill all required fields': 'Please fill all required fields.',
  'Edited release id is required': 'Edited release id is required',
  'Source release not found': 'Source release not found',
  'Profile email is required.': 'Profile email is required.',
  'Release date must be YYYY-MM-DD format': 'Release date must be YYYY-MM-DD format',
  'Subject is required': 'Subject is required',
  'Message cannot be empty': 'Message cannot be empty',
  'User not found': 'User not found',
  'Amount must be greater than zero': 'Amount must be greater than zero',
  'Exchange rate unavailable': 'Exchange rate unavailable',
};

const PREFIX_ERROR_MAP: Record<string, string> = {
  'Not enough credits': 'Not enough credits',
  'Message too long': 'Message too long',
  'Invalid payment method': 'Invalid payment method',
};

export const errorText = (error: unknown, t: TFunction) => {
  const raw = error instanceof Error ? error.message : 'Unknown error';
  const prefixMatch = Object.entries(PREFIX_ERROR_MAP).find(([prefix]) => raw.startsWith(prefix));
  return t(ERROR_MAP[raw] ?? prefixMatch?.[1] ?? raw);
};

export const allowedMusicMessage = (t: TFunction) => t('Music file must be MP3 or WAV');
export const allowedCoverMessage = (t: TFunction) => t('Cover image must be JPG, PNG, or WEBP');
