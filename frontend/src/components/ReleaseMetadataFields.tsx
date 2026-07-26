import { BadgeCheck, Calendar, Music } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { ArtistInput } from './ArtistInput';
import { FormToggle } from './FormToggle';
import { GenreSelect } from './GenreSelect';
import { MultiValueInput } from './MultiValueInput';
import { PersianDatePicker } from './PersianDatePicker';
import { ProducerTagInput } from './ProducerTagInput';
import { ReleaseField } from './ReleaseField';
import { isRtlLanguage } from '../i18n';
import type { ReleaseMetadata } from '../utils/releaseForm';
import { localTodayIso, naturalInputDirection } from '../utils/releaseForm';

interface Props {
  value: ReleaseMetadata;
  onChange: (value: ReleaseMetadata) => void;
}

export const ReleaseMetadataFields = ({ value, onChange }: Props) => {
  const { t, i18n } = useTranslation();
  const update = <K extends keyof ReleaseMetadata>(key: K, next: ReleaseMetadata[K]) =>
    onChange({ ...value, [key]: next });
  const today = localTodayIso();

  return (
    <div className="mb-6 space-y-4">
      <ReleaseField
        id="song-name"
        label={t('Song Name')}
        labelPrefix="3."
        required
        icon={<Music className="h-5 w-5" />}
      >
        <input
          id="song-name"
          type="text"
          value={value.songName}
          dir={naturalInputDirection(value.songName, isRtlLanguage(i18n.language))}
          onChange={event => update('songName', event.target.value)}
          className="w-full bg-transparent text-start font-ui text-textPrimary outline-none"
          placeholder={t('song_placeholder')}
        />
      </ReleaseField>

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
        icon={<BadgeCheck className="h-5 w-5" />}
      />

      <div className="space-y-3">
        <ReleaseField
          id="scheduled-release-date"
          label={t(value.isRerelease ? 'Re-release Date' : 'Scheduled Release Date')}
          labelPrefix="7."
          required
          icon={<Calendar className="h-5 w-5" />}
        >
          <PersianDatePicker
            id="scheduled-release-date"
            value={value.releaseDate}
            minDate={today}
            ariaLabel={t(value.isRerelease ? 'Re-release Date' : 'Scheduled Release Date')}
            onChange={releaseDate => update('releaseDate', releaseDate)}
          />
        </ReleaseField>

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
              className="h-5 w-5 flex-shrink-0 rounded border-inputBorder accent-[#D4AF37] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gold"
            />
            <span className="text-start text-sm font-ui text-textPrimary">
              {t('This track is a re-release')}
            </span>
          </label>
          <p className="mt-1 text-start text-xs leading-relaxed text-textSecondary">
            {t('rerelease_description')}
          </p>
        </div>

        {value.isRerelease && (
          <div className="space-y-1">
            <ReleaseField
              id="original-release-date"
              label={t('Original Release Date')}
              required
              icon={<Calendar className="h-5 w-5" />}
            >
              <PersianDatePicker
                id="original-release-date"
                value={value.originalReleaseDate}
                ariaLabel={t('Original Release Date')}
                onChange={originalReleaseDate => update('originalReleaseDate', originalReleaseDate)}
              />
            </ReleaseField>
            <p className="text-start text-xs leading-relaxed text-textSecondary">
              {t('original_release_date_description')}
            </p>
          </div>
        )}
      </div>

      <div>
        <h3 className="mb-2 text-start text-sm font-ui text-gold">8. {t('Genre')} *</h3>
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
