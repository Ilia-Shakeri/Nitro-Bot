import type { Pricing, Release } from '../types/api';

export const parseProducers = (raw: string | null): string[] => {
  if (!raw) return [];
  try {
    const parsed: unknown = JSON.parse(raw);
    return Array.isArray(parsed)
      ? parsed.filter((item): item is string => typeof item === 'string' && Boolean(item.trim()))
      : [];
  } catch {
    return [];
  }
};

export const localeForLanguage = (language: string) => {
  const code = language.split('-')[0];
  if (code === 'fa') return 'fa-IR-u-ca-gregory';
  if (code === 'ar') return 'ar-SA-u-ca-gregory';
  if (code === 'ru') return 'ru-RU';
  return 'en-US';
};

export const formatReleaseDate = (isoDate: string, language: string) => {
  const date = new Date(`${isoDate}T12:00:00`);
  if (Number.isNaN(date.getTime())) return isoDate;
  return new Intl.DateTimeFormat(localeForLanguage(language), {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  }).format(date);
};

export const releaseDateSentenceKey = (release: Pick<Release, 'is_rerelease'>) =>
  release.is_rerelease ? 'rerelease_scheduled_sentence' : 'scheduled_sentence';

export const discountPercent = (pricing: Pricing) => {
  if (pricing.original_release_price <= 0) return 0;
  return Math.round(
    ((pricing.original_release_price - pricing.discounted_release_price)
      / pricing.original_release_price) * 100,
  );
};

export const releaseTotal = (
  pricing: Pricing,
  isEdit: boolean,
  copyrightRequested: boolean,
) => (isEdit ? pricing.edit_release_price : pricing.discounted_release_price)
  + (copyrightRequested ? pricing.copyright_price : 0);

export const releaseStatusKey = (release: Pick<Release, 'status' | 'refunded_at'>) =>
  release.refunded_at ? 'rollback' : release.status;
