import { ArrowLeft, CheckCircle2, Image as ImageIcon, Music } from 'lucide-react';
import { useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import type { ArtistMapping, Pricing, Release } from '../types/api';
import type { ReleaseMetadata } from '../utils/releaseForm';
import { formatReleaseDate, localeForLanguage, releaseTotal } from '../utils/releasePresentation';
import { NitroCostSummary } from './NitroCostSummary';

interface Props {
  metadata: ReleaseMetadata;
  artistMappings: ArtistMapping[];
  pricing: Pricing;
  balance: number;
  audioFile: File | null;
  coverFile: File | null;
  coverPreview?: string | null;
  source?: Release | null;
  submitting: boolean;
  policyAccepted: boolean;
  policyError?: string;
  onPolicyAcceptedChange: (accepted: boolean) => void;
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
    <dd
      dir={technical ? 'ltr' : undefined}
      className={`min-w-0 break-words text-sm font-ui text-textPrimary ${technical ? 'text-left' : 'text-end'}`}
    >
      {children}
    </dd>
  </div>
);

export const ReleaseReview = ({
  metadata,
  artistMappings,
  pricing,
  balance,
  audioFile,
  coverFile,
  coverPreview,
  source,
  submitting,
  policyAccepted,
  policyError,
  onPolicyAcceptedChange,
  onBack,
  onConfirm,
}: Props) => {
  const { t, i18n } = useTranslation();
  const headingRef = useRef<HTMLHeadingElement>(null);
  const isEdit = Boolean(source);
  const total = releaseTotal(pricing, isEdit, metadata.copyrightRequested);
  const number = (value: number) => value.toLocaleString(localeForLanguage(i18n.language));
  const empty = t('Not provided');

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
          {t('Back to Artist Mapping')}
        </button>
        <h1 ref={headingRef} tabIndex={-1} className="text-start text-3xl font-title outline-none">
          {t('Review & Submit')}
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
              <p className="text-start text-xs text-textSecondary">{t('Audio file')}</p>
              <p dir="ltr" className="truncate text-left text-sm font-ui text-textPrimary">
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
          <h2 className="mb-2 text-start text-lg font-title text-gold">{t('Release Details')}</h2>
          <dl>
            <SummaryRow label={t('Song Name')} technical>{metadata.songName}</SummaryRow>
            <SummaryRow label={t('Artists')}>
              <span className="space-y-1">
                {metadata.artists.map(artist => (
                  <span key={artist.name} dir="ltr" lang="en" className="block text-left">
                    {artist.name} · {t(artist.role === 'primary' ? 'Primary Artist' : 'Featured Artist')}
                  </span>
                ))}
              </span>
            </SummaryRow>
            <SummaryRow label={t('Producers')} technical>{metadata.producers.join(', ') || empty}</SummaryRow>
            <SummaryRow label={t('Legal Names')} technical>{metadata.legalNames.join(', ') || empty}</SummaryRow>
            <SummaryRow label={t(metadata.isRerelease ? 'Re-release Date' : 'Scheduled Release Date')} technical>
              {formatReleaseDate(metadata.releaseDate, i18n.language)}
            </SummaryRow>
            <SummaryRow label={t('This track is a re-release')}>
              {t(metadata.isRerelease ? 'Yes' : 'No')}
            </SummaryRow>
            {metadata.isRerelease && (
              <SummaryRow label={t('Original Release Date')} technical>
                {formatReleaseDate(metadata.originalReleaseDate, i18n.language)}
              </SummaryRow>
            )}
            <SummaryRow label={t('Main Genre')}>{t(metadata.genre)}</SummaryRow>
            <SummaryRow label={t('Subgenre')}>{metadata.subGenre ? t(metadata.subGenre) : empty}</SummaryRow>
            <SummaryRow label={t('Copyright')}>
              {t(metadata.copyrightRequested ? 'Enabled' : 'Disabled')}
            </SummaryRow>
            <SummaryRow label={t('Explicit Content')}>
              {t(metadata.explicitContent ? 'Yes' : 'No')}
            </SummaryRow>
          </dl>
        </section>

        <section className="mt-4 rounded-2xl border border-inputBorder bg-card1 p-4">
          <h2 className="mb-3 text-start text-lg font-title text-gold">{t('Artist Mapping')}</h2>
          <div className="space-y-3">
            {artistMappings.map((mapping, index) => (
              <div key={mapping.artist_name.toLocaleLowerCase()} className="rounded-xl border border-inputBorder/70 bg-card2/50 p-3">
                <p dir="ltr" lang="en" className="text-left text-sm font-title text-textPrimary">
                  {index + 1}. {mapping.artist_name}
                </p>
                <p className="mt-1 text-start text-xs text-textSecondary">
                  {t('New Profile')}: {t(mapping.requires_new_profile ? 'Yes' : 'No')}
                </p>
                {mapping.requires_new_profile ? (
                  <p dir="ltr" className="mt-1 break-all text-left text-xs text-gold">
                    {mapping.profile_email}
                  </p>
                ) : (
                  <>
                    <p dir="ltr" className="mt-1 break-all text-left text-xs text-textSecondary">
                      {t('Spotify')}: {mapping.spotify_url || empty}
                    </p>
                    <p dir="ltr" className="mt-1 break-all text-left text-xs text-textSecondary">
                      {t('Apple Music')}: {mapping.apple_music_url || empty}
                    </p>
                  </>
                )}
              </div>
            ))}
          </div>
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

        <section className="mt-4 rounded-xl border border-gold/25 bg-card1 p-4">
          <label className="flex cursor-pointer items-start gap-3">
            <input
              type="checkbox"
              checked={policyAccepted}
              onChange={event => onPolicyAcceptedChange(event.target.checked)}
              className="mt-0.5 h-5 w-5 flex-shrink-0 rounded border-inputBorder accent-[#D4AF37] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gold"
            />
            <span className="text-start text-sm leading-relaxed text-textPrimary">
              {t('I have read and accept the')}{' '}
              <a href="/policy#terms" target="_blank" rel="noopener noreferrer" className="text-gold underline underline-offset-2">
                {t('Terms and Conditions')}
              </a>{' '}
              {t('and')}{' '}
              <a href="/policy#privacy" target="_blank" rel="noopener noreferrer" className="text-gold underline underline-offset-2">
                {t('Privacy Policy')}
              </a>.
            </span>
          </label>
          {policyError && (
            <p role="alert" className="mt-2 text-start text-xs text-red-400">{t(policyError)}</p>
          )}
        </section>

        <div className="mt-5 grid grid-cols-2 gap-3">
          <button
            type="button"
            onClick={onBack}
            disabled={submitting}
            className="min-h-14 rounded-xl border border-gold/40 px-3 font-ui text-gold focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gold disabled:opacity-50"
          >
            {t('Back to Artist Mapping')}
          </button>
          <button
            type="button"
            onClick={onConfirm}
            disabled={submitting || !policyAccepted}
            className="inline-flex min-h-14 items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-gold to-[#B8860B] px-3 font-title text-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gold disabled:cursor-not-allowed disabled:opacity-50"
          >
            <CheckCircle2 aria-hidden="true" className="h-5 w-5" />
            {submitting ? t('Processing...') : t('Final submission')}
          </button>
        </div>
      </div>
    </main>
  );
};
