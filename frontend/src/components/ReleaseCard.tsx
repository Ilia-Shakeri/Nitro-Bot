import { Edit3, ExternalLink } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import type { Release } from '../types/api';
import { DMB_EDIT_ENABLED } from '../featureFlags';
import {
  formatReleaseDate,
  parseProducers,
  releaseDateSentenceKey,
  releaseHistoryDirection,
} from '../utils/releasePresentation';
import { preloadEdit } from '../utils/routePreload';
import { ReleaseStatusBadge } from './ReleaseStatusBadge';

const Detail = ({ label, value, direction }: {
  label: string;
  value: string;
  direction: 'rtl' | 'ltr';
}) => (
  <div>
    <dt className="text-[11px] text-textSecondary">{label}</dt>
    <dd dir={direction} className="mt-0.5 break-words text-start text-sm text-textPrimary">
      {value}
    </dd>
  </div>
);

export const ReleaseCard = ({ release }: { release: Release }) => {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const primaryArtists = release.artists?.filter(artist => artist.role === 'primary') ?? [];
  const primary = primaryArtists.length
    ? primaryArtists.map(artist => artist.name).join(', ')
    : release.artist_name;
  const featured = release.artists?.filter(artist => artist.role === 'featured') ?? [];
  const producers = parseProducers(release.producers);
  const empty = t('Not provided');
  const date = formatReleaseDate(release.release_date, i18n.language);
  const humanDirection = releaseHistoryDirection(i18n.language);

  return (
    <article className="overflow-hidden rounded-2xl border border-inputBorder bg-card1 shadow-sm">
      <div className="flex gap-3 p-3">
        <div className="h-24 w-24 flex-shrink-0 overflow-hidden rounded-xl bg-card2">
          {release.cover_url && (
            <img
              src={release.cover_url}
              alt={release.song_name}
              width="96"
              height="96"
              loading="lazy"
              className="h-full w-full object-cover"
            />
          )}
        </div>
        <div className="min-w-0 flex-1">
          <div className="mb-1 flex items-start justify-between gap-2">
            <h2 dir="ltr" lang="en" className="min-w-0 truncate text-left text-lg font-title">
              {release.song_name}
            </h2>
            <ReleaseStatusBadge release={release} />
          </div>
          <p dir="ltr" lang="en" className="truncate text-left text-sm font-ui text-textPrimary">{primary}</p>
          <p className="mt-1 truncate text-start text-xs text-textSecondary">
            {t(releaseDateSentenceKey(release), { date })}
          </p>
          {DMB_EDIT_ENABLED && <button
            type="button"
            onPointerEnter={preloadEdit}
            onFocus={preloadEdit}
            onClick={() => navigate(`/edit/${release.id}`)}
            className="mt-2 inline-flex min-h-9 items-center gap-1 rounded-lg border border-gold/35 px-2.5 text-xs font-ui text-gold focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gold"
          >
            <Edit3 aria-hidden="true" className="h-3.5 w-3.5" />
            {t('Edit')}
          </button>}
        </div>
      </div>

      <dl className="grid grid-cols-2 gap-x-3 gap-y-4 border-t border-inputBorder p-4">
        <Detail direction="ltr" label={t('Featured Artists')} value={featured.map(artist => artist.name).join(', ') || empty} />
        <Detail direction="ltr" label={t('Producers')} value={producers.join(', ') || empty} />
        <Detail direction="ltr" label={t('Legal Names')} value={release.legal_names?.join(', ') || release.legal_name || empty} />
        <Detail direction={humanDirection} label={t('Main Genre')} value={release.genre ? t(release.genre) : empty} />
        <Detail direction={humanDirection} label={t('Subgenre')} value={release.sub_genre ? t(release.sub_genre) : empty} />
        <Detail direction={humanDirection} label={t('Original Release Date')} value={release.original_release_date ? formatReleaseDate(release.original_release_date, i18n.language) : empty} />
        <Detail direction={humanDirection} label={t('This track is a re-release')} value={t(release.is_rerelease ? 'Yes' : 'No')} />
        <Detail direction={humanDirection} label={t('Copyright')} value={t(release.copyright_requested ? 'Enabled' : 'Disabled')} />
        <Detail direction={humanDirection} label={t('Explicit Content')} value={t(release.explicit_content ? 'Yes' : 'No')} />
        <Detail direction={humanDirection} label={t('Charged amount')} value={`${release.charged_cost} ${t('Nitro')}`} />
        <Detail direction={humanDirection} label={t('Submitted on')} value={new Intl.DateTimeFormat(i18n.language, { dateStyle: 'medium' }).format(new Date(release.created_at))} />
      </dl>
      {(release.status === 'failed' || release.refunded_at) && (
        <p className="border-t border-inputBorder px-4 py-3 text-start text-xs leading-relaxed text-red-400">
          {t('Release failed tooltip')}
        </p>
      )}

      {(release.artist_mappings?.length > 0 || release.mapping_spotify || release.mapping_apple) && (
        <div className="space-y-3 border-t border-inputBorder p-4">
          {(release.artist_mappings?.length
            ? release.artist_mappings
            : [{
              artist_name: primary,
              requires_new_profile: release.requires_new_profile,
              dmb_has_account: false,
              profile_email: release.profile_email,
              spotify_url: release.mapping_spotify,
              apple_music_url: release.mapping_apple,
            }]
          ).map(mapping => (
            <div key={mapping.artist_name.toLocaleLowerCase()} className="rounded-xl border border-inputBorder/70 p-3">
              <p dir="ltr" lang="en" className="mb-2 text-left text-xs font-title text-gold">
                {mapping.artist_name}
              </p>
              <p className="mb-2 text-start text-xs text-textSecondary">
                {t('New Profile')}: {t(mapping.requires_new_profile ? 'Yes' : 'No')}
              </p>
              {mapping.requires_new_profile && mapping.profile_email && (
                <p dir="ltr" className="mb-2 break-all text-left text-xs text-textSecondary">
                  {mapping.profile_email}
                </p>
              )}
              <div className="flex flex-wrap gap-2">
                {mapping.spotify_url && (
                  <a
                    href={mapping.spotify_url}
                    target="_blank"
                    rel="noreferrer"
                    dir="ltr"
                    className="inline-flex min-h-10 items-center gap-2 rounded-xl border border-inputBorder px-3 text-xs font-ui text-textPrimary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gold"
                  >
                    <img src="/Logo/Spotify.webp" alt="" width="18" height="18" className="h-[18px] w-[18px] object-contain" />
                    {t('Open Spotify')}
                    <ExternalLink aria-hidden="true" className="h-3 w-3" />
                  </a>
                )}
                {mapping.apple_music_url && (
                  <a
                    href={mapping.apple_music_url}
                    target="_blank"
                    rel="noreferrer"
                    dir="ltr"
                    className="inline-flex min-h-10 items-center gap-2 rounded-xl border border-inputBorder px-3 text-xs font-ui text-textPrimary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gold"
                  >
                    <img src="/Logo/AppleMusic.webp" alt="" width="18" height="18" className="h-[18px] w-[18px] object-contain" />
                    {t('Open Apple Music')}
                    <ExternalLink aria-hidden="true" className="h-3 w-3" />
                  </a>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </article>
  );
};
