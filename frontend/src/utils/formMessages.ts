import type { TFunction } from 'i18next';

const ERROR_MAP: Record<string, string> = {
  'Music file must be MP3 or WAV': 'Music file must be MP3 or WAV',
  'Cover image must be JPG, PNG, or WEBP': 'Cover image must be JPG, PNG, or WEBP',
  'Please fill all required fields': 'Please fill all required fields.',
  'Edited release id is required': 'Edited release id is required',
  'Source release not found': 'Source release not found',
};

export const errorText = (error: unknown, t: TFunction) => {
  const raw = error instanceof Error ? error.message : 'Unknown error';
  return t(ERROR_MAP[raw] ?? raw);
};

export const allowedMusicMessage = (t: TFunction) => t('Music file must be MP3 or WAV');
export const allowedCoverMessage = (t: TFunction) => t('Cover image must be JPG, PNG, or WEBP');
