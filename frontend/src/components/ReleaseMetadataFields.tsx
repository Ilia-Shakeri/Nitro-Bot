import { BadgeCheck, Calendar, Music } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { ArtistInput } from './ArtistInput';
import { GenreSelect } from './GenreSelect';
import { MultiValueInput } from './MultiValueInput';
import { PersianDatePicker } from './PersianDatePicker';
import { ProducerTagInput } from './ProducerTagInput';
import { ReleaseField } from './ReleaseField';
import { FormToggle } from './FormToggle';
import type { ReleaseMetadata } from '../utils/releaseForm';
import { localTodayIso } from '../utils/releaseForm';
import { changeMainGenre } from '../utils/genres';

interface Props {
  value: ReleaseMetadata;
  onChange: (value: ReleaseMetadata) => void;
  fieldErrors?: Partial<Record<'song' | 'artists' | 'producers' | 'legal_names', string>>;
}

export const ReleaseMetadataFields = ({ value, onChange, fieldErrors = {} }: Props) => {
  const { t } = useTranslation();
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
          dir="ltr"
          lang="en"
          onChange={event => update('songName', event.target.value)}
          className="w-full bg-transparent text-left font-ui text-textPrimary outline-none"
          placeholder={t('song_placeholder')}
          aria-invalid={Boolean(fieldErrors.song)}
        />
        {fieldErrors.song && (
          <p role="alert" className="mt-2 text-start text-xs text-red-400">
            {t(fieldErrors.song)}
          </p>
        )}
      </ReleaseField>

      <ArtistInput
        labelPrefix="4."
        artists={value.artists}
        onChange={artists => update('artists', artists)}
        onCommit={artists => onChange({ ...value, artists, pendingArtist: '' })}
        pendingValue={value.pendingArtist}
        onPendingChange={pendingArtist => update('pendingArtist', pendingArtist)}
        externalError={fieldErrors.artists}
      />
      <ProducerTagInput
        labelPrefix="5."
        producers={value.producers}
        onChange={producers => update('producers', producers)}
        onCommit={producers => onChange({ ...value, producers, pendingProducer: '' })}
        pendingValue={value.pendingProducer}
        onPendingChange={pendingProducer => update('pendingProducer', pendingProducer)}
        externalError={fieldErrors.producers}
      />
      <MultiValueInput
        label={t('Legal Names')}
        placeholder={t('legal_name_placeholder')}
        values={value.legalNames}
        onChange={legalNames => update('legalNames', legalNames)}
        onCommit={legalNames => onChange({ ...value, legalNames, pendingLegalName: '' })}
        pendingValue={value.pendingLegalName}
        onPendingChange={pendingLegalName => update('pendingLegalName', pendingLegalName)}
        externalError={fieldErrors.legal_names}
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
          <FormToggle
            id="is-rerelease"
            checked={value.isRerelease}
            label={t('This track is a re-release')}
            onChange={() => {
                const checked = !value.isRerelease;
                onChange({
                  ...value,
                  isRerelease: checked,
                  originalReleaseDate: checked ? value.originalReleaseDate : '',
                });
            }}
          />
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
          onGenreChange={genre => onChange({ ...value, ...changeMainGenre(genre) })}
          onSubGenreChange={subGenre => update('subGenre', subGenre)}
        />
      </div>
    </div>
  );
};
