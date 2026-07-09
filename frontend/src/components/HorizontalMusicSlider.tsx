import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { Edit3, Eye } from 'lucide-react';
import { getReleases } from '../api';
import type { Release } from '../types/api';

export const HorizontalMusicSlider = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [releases, setReleases] = useState<Release[]>([]);

  useEffect(() => {
    getReleases().then(setReleases);
  }, []);

  return (
    <div className="w-full px-4 mb-8">
      <div className="flex items-center gap-2 mb-1">
        <h2 className="text-2xl font-title">{t('My Music')}</h2>
      </div>
      <p className="text-textSecondary text-sm font-ui mb-4">{t('Ordered by your most listened tracks')}</p>

      {releases.length === 0 ? (
        <p className="text-center font-light-ui text-sm text-textSecondary py-3">
          {t('No releases yet')}
        </p>
      ) : (
        <div className="flex space-x-4 overflow-x-auto pb-4 hide-scrollbar">
          {releases.map(r => (
            <div key={r.id} className="flex-shrink-0 w-32">
              <div className="w-32 h-32 rounded-xl mb-2 relative overflow-hidden bg-card2">
                {r.cover_url && (
                  <img src={r.cover_url} alt={r.song_name} className="w-full h-full object-cover" />
                )}
                <div
                  className={`absolute top-2 left-2 px-2 py-0.5 rounded-full text-xs font-ui flex items-center gap-1 ${
                    r.status === 'failed' ? 'bg-red-600 text-white' : 'bg-black/60'
                  }`}
                  title={r.status === 'failed' ? (r.failure_reason || t('Release failed. Credits refunded.')) : undefined}
                >
                  <Eye className="w-3 h-3" />
                  {t(r.status)}
                </div>
                <button
                  type="button"
                  aria-label={t('Edit')}
                  onClick={() => navigate(`/upload?edit=${r.id}`)}
                  className="absolute bottom-2 right-2 w-8 h-8 rounded-full bg-gold text-background flex items-center justify-center shadow-md hover:opacity-90"
                >
                  <Edit3 className="w-4 h-4" />
                </button>
              </div>
              <h3 className="text-sm font-ui truncate text-right rtl:text-right ltr:text-left">{r.song_name}</h3>
              <p className="text-xs font-light-ui text-textSecondary truncate text-right rtl:text-right ltr:text-left">{r.artist_name}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
