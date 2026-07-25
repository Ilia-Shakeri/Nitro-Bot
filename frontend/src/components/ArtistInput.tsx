import { useId, useState } from 'react';
import { Plus, X } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import type { ReleaseArtist } from '../types/api';
import {
  addArtist as addArtistValue,
  removeArtist as removeArtistValue,
  selectPrimaryArtist,
} from '../utils/releaseForm';

interface Props {
  artists: ReleaseArtist[];
  onChange: (artists: ReleaseArtist[]) => void;
  labelPrefix?: string;
}

export const ArtistInput = ({ artists, onChange, labelPrefix }: Props) => {
  const { t } = useTranslation();
  const inputId = useId();
  const [value, setValue] = useState('');
  const [error, setError] = useState('');

  const addArtist = () => {
    const result = addArtistValue(artists, value);
    if (result.error) {
      setError(t(result.error));
      return;
    }
    onChange(result.artists);
    setValue('');
    setError('');
  };

  const removeArtist = (index: number) => {
    onChange(removeArtistValue(artists, index));
  };

  const setPrimary = (index: number) => {
    onChange(selectPrimaryArtist(artists, index));
  };

  return (
    <div>
      <label htmlFor={inputId} className="block text-gold font-ui mb-2 text-sm">
        {labelPrefix ? `${labelPrefix} ` : ''}{t('Artists')} *
      </label>
      <div className="rounded-lg border border-inputBorder bg-inputBg p-3 focus-within:border-gold/60">
        <div className="flex items-center gap-2">
          <input
            id={inputId}
            value={value}
            onChange={event => {
              setValue(event.target.value);
              setError('');
            }}
            onKeyDown={event => {
              if (event.key === 'Enter') {
                event.preventDefault();
                addArtist();
              }
            }}
            dir="auto"
            aria-invalid={Boolean(error)}
            aria-describedby={error ? `${inputId}-error` : undefined}
            className="min-w-0 flex-1 bg-transparent text-textPrimary font-ui outline-none"
            placeholder={t('artist_placeholder')}
          />
          <button
            type="button"
            onClick={addArtist}
            aria-label={t('Add artist')}
            className="inline-flex min-h-10 min-w-10 items-center justify-center rounded-lg border border-gold/40 text-gold hover:bg-gold/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gold"
          >
            <Plus className="h-4 w-4" />
          </button>
        </div>
        {error && <p id={`${inputId}-error`} role="alert" className="mt-2 text-xs text-red-400">{error}</p>}
        {artists.length > 0 && (
          <div className="mt-3 space-y-2" role="radiogroup" aria-label={t('Choose primary artist')}>
            {artists.map((artist, index) => (
              <div
                key={`${artist.name}-${index}`}
                className="flex min-w-0 items-center gap-2 rounded-xl border border-gold/25 bg-card2/60 p-2"
              >
                <button
                  type="button"
                  role="radio"
                  aria-checked={artist.role === 'primary'}
                  onClick={() => setPrimary(index)}
                  className={`min-h-9 rounded-lg border px-2 text-xs font-ui focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gold ${
                    artist.role === 'primary'
                      ? 'border-gold bg-gold text-background'
                      : 'border-inputBorder text-textSecondary'
                  }`}
                >
                  {t(artist.role === 'primary' ? 'Primary Artist' : 'Featured Artist')}
                </button>
                <span dir="auto" className="min-w-0 flex-1 truncate text-sm text-textPrimary">
                  {artist.name}
                </span>
                <button
                  type="button"
                  onClick={() => removeArtist(index)}
                  aria-label={`${t('Remove artist')}: ${artist.name}`}
                  className="inline-flex min-h-9 min-w-9 items-center justify-center rounded-full text-textSecondary hover:bg-gold/15 hover:text-gold focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gold"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
