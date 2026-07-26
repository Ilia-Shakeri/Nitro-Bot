import { ArrowRight, Edit3 } from 'lucide-react';
import { useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { useReleases } from '../context/ReleaseContext';
import { useToast } from '../context/ToastContext';
import { errorText } from '../utils/formMessages';
import {
  formatReleaseDate,
  releaseDateSentenceKey,
} from '../utils/releasePresentation';
import { preloadEdit, preloadReleases } from '../utils/routePreload';
import { ReleaseStatusBadge } from './ReleaseStatusBadge';

export const HorizontalMusicSlider = () => {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const { toast } = useToast();
  const { releases, loading, loadReleases } = useReleases();

  useEffect(() => {
    if (!releases) {
      void loadReleases().catch(error => toast(errorText(error, t), 'error'));
    }
  }, [loadReleases, releases, t, toast]);

  return (
    <section className="mb-8 w-full px-4">
      <div className="mb-1 flex items-center justify-between gap-3">
        <h2 className="text-2xl font-title">{t('My Music')}</h2>
        <button
          type="button"
          onPointerEnter={preloadReleases}
          onPointerDown={preloadReleases}
          onFocus={preloadReleases}
          onClick={() => navigate('/releases')}
          className="inline-flex min-h-10 items-center gap-1 rounded-lg px-2 text-xs font-ui text-gold focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gold"
        >
          {t('View all')}
          <ArrowRight aria-hidden="true" className="h-3.5 w-3.5 rtl:rotate-180" />
        </button>
      </div>
      <p className="mb-4 text-sm font-ui text-textSecondary">{t('Ordered by your most listened tracks')}</p>

      {loading && !releases ? (
        <div aria-label={t('Loading...')} className="flex gap-4 overflow-hidden pb-4">
          {[0, 1, 2].map(item => (
            <div key={item} className="w-32 flex-shrink-0">
              <div className="h-32 w-32 animate-pulse rounded-xl bg-card2" />
              <div className="mt-2 h-4 w-24 animate-pulse rounded bg-card2" />
            </div>
          ))}
        </div>
      ) : !releases?.length ? (
        <p className="py-3 text-center text-sm font-light-ui text-textSecondary">
          {t('No releases yet')}
        </p>
      ) : (
        <div className="flex snap-x gap-4 overflow-x-auto pb-4 hide-scrollbar">
          {releases.slice(0, 8).map(release => {
            const primary = release.artists?.find(artist => artist.role === 'primary')?.name
              ?? release.artist_name;
            const date = formatReleaseDate(release.release_date, i18n.language);
            return (
              <article key={release.id} className="w-32 flex-shrink-0 snap-start">
                <div className="relative mb-2 h-32 w-32 overflow-hidden rounded-xl bg-card2">
                  {release.cover_url && (
                    <img
                      src={release.cover_url}
                      alt={release.song_name}
                      width="128"
                      height="128"
                      loading="lazy"
                      className="h-full w-full object-cover"
                    />
                  )}
                  <div className="absolute start-2 top-2">
                    <ReleaseStatusBadge release={release} />
                  </div>
                  <button
                    type="button"
                    aria-label={t('Edit')}
                    onPointerEnter={preloadEdit}
                    onPointerDown={preloadEdit}
                    onFocus={preloadEdit}
                    onClick={() => navigate(`/edit/${release.id}`)}
                    className="absolute bottom-2 end-2 flex h-9 w-9 items-center justify-center rounded-full bg-gold text-background shadow-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white"
                  >
                    <Edit3 aria-hidden="true" className="h-4 w-4" />
                  </button>
                </div>
                <h3 dir="auto" className="truncate text-start text-sm font-ui">{release.song_name}</h3>
                <p dir="auto" className="truncate text-start text-xs font-light-ui text-textSecondary">
                  {primary}
                </p>
                <p className="mt-1 truncate text-start text-[10px] leading-4 text-textSecondary">
                  {t(releaseDateSentenceKey(release), { date })}
                </p>
              </article>
            );
          })}
        </div>
      )}
    </section>
  );
};
