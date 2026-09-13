import { ArrowLeft, ArrowRight, Mail } from 'lucide-react';
import { useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import type { ArtistMapping, ReleaseArtist } from '../types/api';
import type { ArtistMappingValidationError } from '../utils/releaseForm';
import { FormToggle } from './FormToggle';
import { ReleaseField } from './ReleaseField';

interface Props {
  artists: ReleaseArtist[];
  mappings: ArtistMapping[];
  error?: ArtistMappingValidationError | null;
  onChange: (mappings: ArtistMapping[]) => void;
  onBack: () => void;
  onContinue: () => void;
}

const PlatformLogo = ({ src, alt }: { src: string; alt: string }) => (
  <img src={src} alt={alt} className="h-5 w-5 object-contain" width="20" height="20" />
);

export const ArtistMappingStep = ({
  artists,
  mappings,
  error,
  onChange,
  onBack,
  onContinue,
}: Props) => {
  const { t } = useTranslation();
  const headingRef = useRef<HTMLHeadingElement>(null);

  useEffect(() => {
    headingRef.current?.focus();
    window.scrollTo({ top: 0, behavior: 'auto' });
  }, []);

  const update = (index: number, patch: Partial<ArtistMapping>) => {
    onChange(mappings.map((mapping, itemIndex) => (
      itemIndex === index ? { ...mapping, ...patch } : mapping
    )));
  };

  return (
    <section>
      <h1
        ref={headingRef}
        tabIndex={-1}
        className="mb-2 text-start text-3xl font-title outline-none"
      >
        {t('Artist Mapping')} *
      </h1>
      <p className="mb-6 text-start text-sm leading-relaxed text-textSecondary">
        {t('Complete the mapping for every artist.')}
      </p>

      <div className="space-y-4">
        {artists.map((artist, index) => {
          const mapping = mappings[index];
          if (!mapping) return null;
          const prefix = `mapping-${index}`;
          return (
            <article
              key={artist.name.toLocaleLowerCase()}
              className="rounded-2xl border border-gold/25 bg-card1 p-4"
            >
              <p className="text-start text-xs text-textSecondary">
                {t('Artist {{current}} of {{total}}', {
                  current: index + 1,
                  total: artists.length,
                })}
              </p>
              <div className="mb-4 mt-1 flex flex-wrap items-center justify-between gap-2">
                <h2 dir="ltr" lang="en" className="min-w-0 text-left text-lg font-title text-gold">
                  {artist.name}
                </h2>
                <span className="rounded-full border border-gold/30 px-2.5 py-1 text-xs text-gold">
                  {t(artist.role === 'primary' ? 'Primary Artist' : 'Featured Artist')}
                </span>
              </div>

              <FormToggle
                id={`${prefix}-new-profile`}
                checked={mapping.requires_new_profile}
                onChange={() => update(index, {
                  requires_new_profile: !mapping.requires_new_profile,
                  profile_email: null,
                  spotify_url: null,
                  apple_music_url: null,
                })}
                label={t("I don't have a profile (Create one for me)")}
              />

              <div className="mt-3">
                <FormToggle
                  id={`${prefix}-dmb-account`}
                  checked={mapping.dmb_has_account}
                  onChange={() => update(index, {
                    dmb_has_account: !mapping.dmb_has_account,
                  })}
                  label={t('This artist already has a DMB contributor account')}
                />
              </div>

              {mapping.requires_new_profile ? (
                <div className="mt-3">
                  <ReleaseField
                    id={`${prefix}-email`}
                    label={t('Profile Email')}
                    required
                    icon={<Mail className="h-5 w-5" />}
                  >
                    <input
                      id={`${prefix}-email`}
                      type="email"
                      value={mapping.profile_email ?? ''}
                      onChange={event => update(index, { profile_email: event.target.value })}
                      dir="ltr"
                      inputMode="email"
                      autoComplete="email"
                      className="w-full bg-transparent text-left text-sm text-textPrimary outline-none"
                      placeholder="artist@example.com"
                    />
                  </ReleaseField>
                </div>
              ) : (
                <div className="mt-3 space-y-3">
                  <ReleaseField
                    id={`${prefix}-spotify`}
                    label={t('Spotify')}
                    icon={<PlatformLogo src="/Logo/Spotify.webp" alt={t('Spotify logo')} />}
                  >
                    <input
                      id={`${prefix}-spotify`}
                      type="url"
                      value={mapping.spotify_url ?? ''}
                      onChange={event => update(index, { spotify_url: event.target.value })}
                      dir="ltr"
                      inputMode="url"
                      className="w-full bg-transparent text-left text-sm text-textPrimary outline-none"
                      placeholder="https://open.spotify.com/artist/..."
                    />
                  </ReleaseField>
                  <ReleaseField
                    id={`${prefix}-apple`}
                    label={t('Apple Music')}
                    icon={<PlatformLogo src="/Logo/AppleMusic.webp" alt={t('Apple Music logo')} />}
                  >
                    <input
                      id={`${prefix}-apple`}
                      type="url"
                      value={mapping.apple_music_url ?? ''}
                      onChange={event => update(index, { apple_music_url: event.target.value })}
                      dir="ltr"
                      inputMode="url"
                      className="w-full bg-transparent text-left text-sm text-textPrimary outline-none"
                      placeholder="https://music.apple.com/artist/..."
                    />
                  </ReleaseField>
                  <p className="text-start text-xs text-textSecondary">
                    {t('mapping_required_description')}
                  </p>
                </div>
              )}
            </article>
          );
        })}
      </div>

      {error && (
        <p role="alert" className="mt-4 rounded-xl border border-red-400/30 bg-red-500/10 p-3 text-start text-sm text-red-300">
          {t(error.key, { artist: error.artist })}
        </p>
      )}

      <div className="mt-6 grid grid-cols-2 gap-3 pb-8">
        <button
          type="button"
          onClick={onBack}
          className="inline-flex min-h-14 items-center justify-center gap-2 rounded-xl border border-gold/40 px-3 font-ui text-gold focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gold"
        >
          <ArrowLeft aria-hidden="true" className="h-4 w-4 rtl:rotate-180" />
          {t('Back to Release Details')}
        </button>
        <button
          type="button"
          onClick={onContinue}
          className="inline-flex min-h-14 items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-gold to-[#B8860B] px-3 font-title text-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gold"
        >
          {t('Continue to Review')}
          <ArrowRight aria-hidden="true" className="h-4 w-4 rtl:rotate-180" />
        </button>
      </div>
    </section>
  );
};
