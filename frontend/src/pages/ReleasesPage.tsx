import { ArrowLeft, Disc3 } from 'lucide-react';
import { useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { ReleaseCard } from '../components/ReleaseCard';
import { useReleases } from '../context/ReleaseContext';
import { useToast } from '../context/ToastContext';
import { isRtlLanguage } from '../i18n';
import { errorText } from '../utils/formMessages';

export const ReleasesPage = () => {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const { releases, loading, loadReleases } = useReleases();
  const { toast } = useToast();

  useEffect(() => {
    if (!releases) {
      void loadReleases().catch(error => toast(errorText(error, t), 'error'));
    }
  }, [loadReleases, releases, t, toast]);

  return (
    <div
      className="min-h-[var(--tg-viewport-stable-height,100vh)] bg-background"
      dir={isRtlLanguage(i18n.language) ? 'rtl' : 'ltr'}
    >
      <main className="mx-auto max-w-md px-4 pb-8 pt-5">
        <button
          type="button"
          onClick={() => navigate('/')}
          className="mb-5 inline-flex min-h-11 items-center gap-2 rounded-xl px-2 text-sm font-ui text-gold focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gold"
        >
          <ArrowLeft aria-hidden="true" className="h-4 w-4 rtl:rotate-180" />
          {t('Back')}
        </button>
        <h1 className="text-start text-3xl font-title">{t('All releases')}</h1>
        <p className="mb-5 mt-1 text-start text-sm text-textSecondary">{t('All releases description')}</p>

        {loading && !releases ? (
          <div aria-label={t('Loading...')} className="space-y-4">
            {[0, 1, 2].map(item => (
              <div key={item} className="h-48 animate-pulse rounded-2xl border border-inputBorder bg-card1" />
            ))}
          </div>
        ) : releases?.length ? (
          <div className="space-y-4">
            {releases.map(release => <ReleaseCard key={release.id} release={release} />)}
          </div>
        ) : (
          <div className="rounded-2xl border border-dashed border-inputBorder bg-card1 p-8 text-center">
            <Disc3 aria-hidden="true" className="mx-auto mb-3 h-10 w-10 text-gold" />
            <p className="font-ui text-textPrimary">{t('No releases yet')}</p>
            <p className="mt-1 text-xs text-textSecondary">{t('No releases description')}</p>
          </div>
        )}
      </main>
    </div>
  );
};
