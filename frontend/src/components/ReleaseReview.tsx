import { ArrowLeft, CheckCircle2, Image as ImageIcon, Music } from 'lucide-react';
import { useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import type { Pricing, Release } from '../types/api';
import type { ReleaseMetadata } from '../utils/releaseForm';
import { formatReleaseDate, localeForLanguage, releaseTotal } from '../utils/releasePresentation';
import { NitroCostSummary } from './NitroCostSummary';

interface Props {
  metadata: ReleaseMetadata;
  pricing: Pricing;
  balance: number;
  audioFile: File | null;
  coverFile: File | null;
  coverPreview?: string | null;
  needsNewProfile: boolean;
  profileEmail: string;
  spotifyUrl: string;
  appleUrl: string;
  source?: Release | null;
  submitting: boolean;
  onBack: () => void;
  onConfirm: () => void;
}

const SummaryRow = ({
  label,
  children,
  technical = false,
}: {
  label: string;
  children: React.ReactNode;
  technical?: boolean;
}) => (
  <div className="grid grid-cols-[minmax(0,0.42fr)_minmax(0,0.58fr)] gap-3 border-b border-inputBorder/60 py-2.5 last:border-0">
    <dt className="text-start text-xs text-textSecondary">{label}</dt>
    <dd dir={technical ? 'ltr' : 'auto'} className="min-w-0 break-words text-end text-sm font-ui text-textPrimary">
      {children}
    </dd>
  </div>
);

export const ReleaseReview = ({
  metadata,
  pricing,
  balance,
  audioFile,
  coverFile,
  coverPreview,
  needsNewProfile,
  profileEmail,
  spotifyUrl,
  appleUrl,
  source,
  submitting,
  onBack,
  onConfirm,
}: Props) => {
  const { t, i18n } = useTranslation();
  const headingRef = useRef<HTMLHeadingElement>(null);
  const isEdit = Boolean(source);
  const total = releaseTotal(pricing, isEdit, metadata.copyrightRequested);
  const number = (value: number) => value.toLocaleString(localeForLanguage(i18n.language));
  const empty = t('Not provided');
  const effectiveSpotify = needsNewProfile ? source?.mapping_spotify ?? '' : spotifyUrl;
  const effectiveApple = needsNewProfile ? source?.mapping_apple ?? '' : appleUrl;

  useEffect(() => {
    headingRef.current?.focus();
    window.scrollTo({ top: 0, behavior: 'auto' });
  }, []);

  return (
    <main className="min-h-[var(--tg-viewport-stable-height,100vh)] bg-background px-4 pb-8 pt-5">
      <div className="mx-auto max-w-md">
        <button
          type="button"
          onClick={onBack}
          disabled={submitting}
          className="mb-5 inline-flex min-h-11 items-center gap-2 rounded-xl px-2 text-sm font-ui text-gold focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gold disabled:opacity-50"
        >
          <ArrowLeft aria-hidden="true" className="h-4 w-4 rtl:rotate-180" />
          {t('Back to editing')}
        </button>
        <h1
          ref={headingRef}
          tabIndex={-1}
          className="text-start text-3xl font-title text-textPrimary outline-none"
        >
          {t(isEdit ? 'Review edit' : 'Review release')}
        </h1>
        <p className="mb-5 mt-1 text-start text-sm text-textSecondary">{t('Release summary')}</p>

        <section className="mb-4 overflow-hidden rounded-2xl border border-inputBorder bg-card1">
          <div className="aspect-square w-full bg-card2">
            {coverPreview ? (
              <img
                src={coverPreview}
                alt={t('Cover art')}
                width="448"
                height="448"
                className="h-full w-full object-cover"
              />
            ) : (
              <div className="flex h-full items-center justify-center text-textSecondary">
                <ImageIcon aria-hidden="true" className="h-12 w-12" />
              </div>
            )}
          </div>
          <div className="flex min-h-14 items-center gap-3 p-4">
            <Music aria-hidden="true" className="h-5 w-5 flex-shrink-0 text-gold" />
            <div className="min-w-0">
              <p className="text-xs text-textSecondary">{t('Audio file')}</p>
              <p dir="auto" className="truncate text-sm font-ui text-textPrimary">
                {audioFile?.name ?? (source ? t('Current file retained') : empty)}
              </p>
            </div>
          </div>
        </section>

        {isEdit && (
          <div className="mb-4 rounded-xl border border-gold/25 bg-gold/5 p-3 text-start text-sm text-gold">
            {t('Editing release', { name: source?.song_name ?? '' })}
            <p className="mt-1 text-xs text-textSecondary">
              {audioFile ? t('Replacement audio selected') : t('Current audio retained')}
              {' · '}
              {coverFile ? t('Replacement cover selected') : t('Current cover retained')}
            </p>
          </div>
        )}

        <section className="rounded-2xl border border-inputBorder bg-card1 p-4">
          <h2 className="mb-2 text-start text-lg font-title text-gold">{t('Release summary')}</h2>
          <dl>
            <SummaryRow label={t('Song Name')}>{metadata.songName}</SummaryRow>
            <SummaryRow label={t('Artists')}>
              <span className="space-y-1">
                {metadata.artists.map(artist => (
                  <span key={artist.name} className="block">
                    {artist.name} · {t(artist.role === 'primary' ? 'Primary Artist' : 'Featured Artist')}
                  </span>
                ))}
              </span>
            </SummaryRow>
            <SummaryRow label={t('Producers')}>{metadata.producers.join('، ') || empty}</SummaryRow>
            <SummaryRow label={t('Legal Names')}>{metadata.legalNames.join('، ') || empty}</SummaryRow>
            <SummaryRow label={t(metadata.isRerelease ? 'Re-release Date' : 'Scheduled Release Date')}>
              {formatReleaseDate(metadata.releaseDate, i18n.language)}
            </SummaryRow>
            <SummaryRow label={t('This track is a re-release')}>
              {t(metadata.isRerelease ? 'Yes' : 'No')}
            </SummaryRow>
            {metadata.isRerelease && (
              <SummaryRow label={t('Original Release Date')}>
                {formatReleaseDate(metadata.originalReleaseDate, i18n.language)}
              </SummaryRow>
            )}
            <SummaryRow label={t('Main Genre')}>{t(metadata.genre)}</SummaryRow>
            <SummaryRow label={t('Subgenre')}>{metadata.subGenre ? t(metadata.subGenre) : empty}</SummaryRow>
            <SummaryRow label={t('Spotify')} technical={Boolean(effectiveSpotify)}>
              {effectiveSpotify || empty}
            </SummaryRow>
            <SummaryRow label={t('Apple Music')} technical={Boolean(effectiveApple)}>
              {effectiveApple || empty}
            </SummaryRow>
            <SummaryRow label={t('New Profile')}>
              {t(needsNewProfile ? 'Yes' : 'No')}
            </SummaryRow>
            {needsNewProfile && (
              <SummaryRow label={t('Profile Email')} technical={Boolean(profileEmail)}>
                {profileEmail || empty}
              </SummaryRow>
            )}
            <SummaryRow label={t('Copyright')}>
              {t(metadata.copyrightRequested ? 'Enabled' : 'Disabled')}
            </SummaryRow>
          </dl>
        </section>

        <NitroCostSummary
          pricing={pricing}
          isEdit={isEdit}
          copyrightRequested={metadata.copyrightRequested}
        />

        <section className="mt-4 rounded-xl border border-inputBorder bg-card1 p-4">
          <div className="flex justify-between gap-3 text-sm">
            <span className="text-textSecondary">{t('Current balance')}</span>
            <span className="font-ui">{number(balance)} {t('Nitro')}</span>
          </div>
          <div className="mt-2 flex justify-between gap-3 text-sm">
            <span className="text-textSecondary">{t('Balance after submission')}</span>
            <span className="font-title text-gold">{number(balance - total)} {t('Nitro')}</span>
          </div>
        </section>

        <div className="mt-5 grid grid-cols-2 gap-3">
          <button
            type="button"
            onClick={onBack}
            disabled={submitting}
            className="min-h-14 rounded-xl border border-gold/40 px-3 font-ui text-gold focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gold disabled:opacity-50"
          >
            {t('Back to editing')}
          </button>
          <button
            type="button"
            onClick={onConfirm}
            disabled={submitting}
            className="inline-flex min-h-14 items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-gold to-[#B8860B] px-3 font-title text-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gold disabled:opacity-50"
          >
            <CheckCircle2 aria-hidden="true" className="h-5 w-5" />
            {submitting ? t('Processing...') : t('Final submission')}
          </button>
        </div>
      </div>
    </main>
  );
};
