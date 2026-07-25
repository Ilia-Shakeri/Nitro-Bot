import { Calendar, Music } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { ArtistInput } from './ArtistInput';
import { FormToggle } from './FormToggle';
import { GenreSelect } from './GenreSelect';
import { MultiValueInput } from './MultiValueInput';
import { PersianDatePicker } from './PersianDatePicker';
import { ProducerTagInput } from './ProducerTagInput';
import type { ReleaseMetadata } from '../utils/releaseForm';
import { localTodayIso } from '../utils/releaseForm';

interface Props {
  value: ReleaseMetadata;
  onChange: (value: ReleaseMetadata) => void;
}

export const ReleaseMetadataFields = ({ value, onChange }: Props) => {
  const { t } = useTranslation();
  const update = <K extends keyof ReleaseMetadata>(key: K, next: ReleaseMetadata[K]) =>
    onChange({ ...value, [key]: next });
  const today = localTodayIso();

  return (
    <div className="space-y-4 mb-6">
      <div>
        <label htmlFor="song-name" className="block text-gold font-ui mb-2 text-sm">
          3. {t('Song Name')} *
        </label>
        <div className="flex items-center rounded-lg border border-inputBorder bg-inputBg p-3 focus-within:border-gold/60">
          <Music className="me-3 h-5 w-5 flex-shrink-0 text-textSecondary" />
          <input
            id="song-name"
            type="text"
            value={value.songName}
            dir="auto"
            onChange={event => update('songName', event.target.value)}
            className="w-full bg-transparent text-textPrimary font-ui outline-none"
            placeholder={t('song_placeholder')}
          />
        </div>
      </div>

      <ArtistInput
        labelPrefix="4."
        artists={value.artists}
        onChange={artists => update('artists', artists)}
      />
      <ProducerTagInput
        labelPrefix="5."
        producers={value.producers}
        onChange={producers => update('producers', producers)}
      />
      <MultiValueInput
        label={t('Legal Names')}
        placeholder={t('legal_name_placeholder')}
        values={value.legalNames}
        onChange={legalNames => update('legalNames', legalNames)}
        addLabel={t('Add legal name')}
        removeLabel={t('Remove legal name')}
        labelPrefix="6."
        required
      />

      <div className="rounded-xl border border-inputBorder bg-card1 p-3">
        <label htmlFor="is-rerelease" className="flex min-h-11 cursor-pointer items-center gap-3">
          <input
            id="is-rerelease"
            type="checkbox"
            checked={value.isRerelease}
            onChange={event => {
              const checked = event.target.checked;
              onChange({
                ...value,
                isRerelease: checked,
                originalReleaseDate: checked ? value.originalReleaseDate : '',
              });
            }}
            className="h-5 w-5 rounded border-inputBorder accent-[#D4AF37] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gold"
          />
          <span className="text-sm font-ui text-textPrimary">
            {t('This track is a re-release')}
          </span>
        </label>
        <p className="mt-1 text-xs text-textSecondary">
          {t('rerelease_description')}
        </p>
      </div>

      <div className="space-y-3">
        <div>
          <label className="block text-gold font-ui mb-2 text-sm">
            7. {t(value.isRerelease ? 'Re-release Date' : 'Scheduled Release Date')} *
          </label>
          <div className="flex items-center rounded-lg border border-inputBorder bg-inputBg p-3">
            <Calendar className="me-3 h-5 w-5 flex-shrink-0 text-textSecondary" />
            <PersianDatePicker
              value={value.releaseDate}
              minDate={today}
              ariaLabel={t(value.isRerelease ? 'Re-release Date' : 'Scheduled Release Date')}
              onChange={releaseDate => update('releaseDate', releaseDate)}
            />
          </div>
        </div>
        {value.isRerelease && (
          <div>
            <label className="block text-gold font-ui mb-2 text-sm">
              {t('Original Release Date')} *
            </label>
            <div className="flex items-center rounded-lg border border-inputBorder bg-inputBg p-3">
              <Calendar className="me-3 h-5 w-5 flex-shrink-0 text-textSecondary" />
              <PersianDatePicker
                value={value.originalReleaseDate}
                ariaLabel={t('Original Release Date')}
                onChange={originalReleaseDate => update('originalReleaseDate', originalReleaseDate)}
              />
            </div>
            <p className="mt-1 text-xs text-textSecondary">
              {t('original_release_date_description')}
            </p>
          </div>
        )}
      </div>

      <div className="relative z-40">
        <h3 className="text-gold font-ui mb-2 text-sm">8. {t('Genre')} *</h3>
        <GenreSelect
          genre={value.genre}
          subGenre={value.subGenre}
          onGenreChange={genre => update('genre', genre)}
          onSubGenreChange={subGenre => update('subGenre', subGenre)}
        />
      </div>

      <div className="rounded-xl border border-inputBorder bg-card1 p-4">
        <FormToggle
          id="copyrightRequested"
          checked={value.copyrightRequested}
          onChange={() => update('copyrightRequested', !value.copyrightRequested)}
          label={t('Add Copyright Protection')}
          tone="gold"
        />
      </div>
    </div>
  );
};
