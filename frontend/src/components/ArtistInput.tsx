import { useId, useState } from 'react';
import { Plus, Users, X } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import type { ReleaseArtist } from '../types/api';
import {
  addArtist as addArtistValue,
  removeArtist as removeArtistValue,
  toggleArtistRole,
} from '../utils/releaseForm';

interface Props {
  artists: ReleaseArtist[];
  onChange: (artists: ReleaseArtist[]) => void;
  onCommit: (artists: ReleaseArtist[]) => void;
  pendingValue: string;
  onPendingChange: (value: string) => void;
  externalError?: string;
  labelPrefix?: string;
}

export const ArtistInput = ({
  artists,
  onChange,
  onCommit,
  pendingValue,
  onPendingChange,
  externalError,
  labelPrefix,
}: Props) => {
  const { t } = useTranslation();
  const inputId = useId();
  const [error, setError] = useState('');

  const addArtist = () => {
    const result = addArtistValue(artists, pendingValue);
    if (result.error) {
      setError(t(result.error));
      return;
    }
    onCommit(result.artists);
    setError('');
  };

  const removeArtist = (index: number) => {
    onChange(removeArtistValue(artists, index));
  };

  const toggleRole = (index: number) => {
    const result = toggleArtistRole(artists, index);
    if (result.error) {
      setError(t(result.error));
      return;
    }
    onChange(result.artists);
    setError('');
  };
  const shownError = externalError ? t(externalError) : error;

  return (
    <div>
      <label htmlFor={inputId} className="block text-gold font-ui mb-2 text-sm">
        {labelPrefix ? `${labelPrefix} ` : ''}{t('Artists')} *
      </label>
      <div className="rounded-lg border border-inputBorder bg-inputBg p-3 focus-within:border-gold/60">
        <form
          className="flex items-center gap-2"
          onSubmit={event => {
            event.preventDefault();
            addArtist();
          }}
        >
          <Users aria-hidden="true" className="h-5 w-5 flex-shrink-0 text-textSecondary" />
          <input
            id={inputId}
            value={pendingValue}
            onChange={event => {
              onPendingChange(event.target.value);
              setError('');
            }}
            dir="ltr"
            lang="en"
            enterKeyHint="next"
            aria-invalid={Boolean(shownError)}
            aria-describedby={shownError ? `${inputId}-error` : undefined}
            className="min-w-0 flex-1 bg-transparent text-left text-textPrimary font-ui outline-none"
            placeholder={t('artist_placeholder')}
          />
          <button
            type="submit"
            aria-label={t('Add artist')}
            className="inline-flex min-h-10 min-w-10 items-center justify-center rounded-lg border border-gold/40 text-gold hover:bg-gold/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gold"
          >
            <Plus aria-hidden="true" className="h-4 w-4" />
          </button>
        </form>
        {shownError && <p id={`${inputId}-error`} role="alert" className="mt-2 text-start text-xs text-red-400">{shownError}</p>}
        {artists.length > 0 && (
          <div className="mt-3 space-y-2">
            <p className="text-start text-xs text-textSecondary">
              {t('primary_artist_count', {
                count: artists.filter(artist => artist.role === 'primary').length,
                max: 3,
              })}
            </p>
            {artists.map((artist, index) => (
              <div
                key={`${artist.name}-${index}`}
                className="flex min-w-0 items-center gap-2 rounded-xl border border-gold/25 bg-card2/60 p-2"
              >
                <button
                  type="button"
                  role="switch"
                  aria-checked={artist.role === 'primary'}
                  onClick={() => toggleRole(index)}
                  className={`min-h-9 rounded-lg border px-2 text-xs font-ui focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gold ${
                    artist.role === 'primary'
                      ? 'border-gold bg-gold text-background'
                      : 'border-inputBorder text-textSecondary'
                  }`}
                >
                  {t(artist.role === 'primary' ? 'Primary Artist' : 'Featured Artist')}
                </button>
                <span dir="ltr" lang="en" className="min-w-0 flex-1 truncate text-left text-sm text-textPrimary">
                  {artist.name}
                </span>
                <button
                  type="button"
                  onClick={() => removeArtist(index)}
                  aria-label={`${t('Remove artist')}: ${artist.name}`}
                  className="inline-flex min-h-9 min-w-9 items-center justify-center rounded-full text-textSecondary hover:bg-gold/15 hover:text-gold focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gold"
                >
                  <X aria-hidden="true" className="h-4 w-4" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
