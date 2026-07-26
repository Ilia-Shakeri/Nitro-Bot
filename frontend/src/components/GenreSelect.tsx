import { ListTree, Tag } from 'lucide-react';
import { useId } from 'react';
import { useTranslation } from 'react-i18next';
import { GENRE_TREE, changeMainGenre } from '../utils/genres';
import { ReleaseField } from './ReleaseField';

interface Props {
  genre: string;
  subGenre: string;
  onGenreChange: (genre: string) => void;
  onSubGenreChange: (subGenre: string) => void;
}

export const GenreSelect = ({
  genre,
  subGenre,
  onGenreChange,
  onSubGenreChange,
}: Props) => {
  const { t } = useTranslation();
  const genreId = useId();
  const subGenreId = useId();
  const subGenres = genre ? GENRE_TREE[genre] ?? [] : [];

  return (
    <div className="space-y-3">
      <ReleaseField id={genreId} label={t('Main Genre')} required icon={<Tag className="h-5 w-5" />}>
        <select
          id={genreId}
          value={genre}
          onChange={event => {
            const next = changeMainGenre(event.target.value);
            onGenreChange(next.genre);
            onSubGenreChange(next.subGenre);
          }}
          className="min-h-11 w-full appearance-auto bg-transparent text-start text-sm font-ui text-textPrimary outline-none"
        >
          <option value="" className="bg-card1 text-textPrimary">{t('Select a genre')}</option>
          {Object.keys(GENRE_TREE).map(option => (
            <option key={option} value={option} className="bg-card1 text-textPrimary">{t(option)}</option>
          ))}
        </select>
      </ReleaseField>

      {genre && subGenres.length > 0 && (
        <ReleaseField id={subGenreId} label={t('Subgenre')} icon={<ListTree className="h-5 w-5" />}>
          <select
            id={subGenreId}
            value={subGenre}
            onChange={event => onSubGenreChange(event.target.value)}
            className="min-h-11 w-full appearance-auto bg-transparent text-start text-sm font-ui text-textPrimary outline-none"
          >
            <option value="" className="bg-card1 text-textPrimary">{t('Select a subgenre')}</option>
            {subGenres.map(option => (
              <option key={option} value={option} className="bg-card1 text-textPrimary">{t(option)}</option>
            ))}
          </select>
        </ReleaseField>
      )}
    </div>
  );
};
