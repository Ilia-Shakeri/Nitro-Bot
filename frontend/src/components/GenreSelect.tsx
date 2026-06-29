import { useTranslation } from 'react-i18next';
import { Tag, ChevronDown, ListTree } from 'lucide-react';

// Primary genres MUST match the DMB genre autocomplete labels exactly (the Kontor
// worker types the primary value into the DMB form). Subgenres are extra metadata
// sent as `sub_genre`; an empty subgenre list means the genre has no nesting.
export const GENRE_TREE: Record<string, string[]> = {
  'HipHop / Rap [Urban]': ['Trap', 'Drill', 'Boom Bap', 'Gangsta Rap', 'Conscious', 'Cloud Rap'],
  'Pop':                  ['Dance Pop', 'Synth Pop', 'Indie Pop', 'Electropop', 'K-Pop'],
  'Rock':                 ['Alternative', 'Indie Rock', 'Hard Rock', 'Punk', 'Post-Rock'],
  'Electronic / Dance':   ['House', 'Techno', 'Trance', 'Dubstep', 'Drum & Bass', 'EDM'],
  'R&B / Soul':           ['Contemporary R&B', 'Neo-Soul', 'Funk'],
  'Classical':            ['Orchestral', 'Piano', 'Opera', 'Chamber'],
  'Jazz':                 ['Smooth Jazz', 'Bebop', 'Fusion', 'Swing'],
  'Folk':                 ['Indie Folk', 'Singer-Songwriter', 'Americana'],
  'Country':              ['Modern Country', 'Bluegrass', 'Country Pop'],
  'Reggae':               ['Roots', 'Dancehall', 'Dub'],
  'Metal':                ['Heavy Metal', 'Death Metal', 'Black Metal', 'Metalcore'],
  'World':                ['Latin', 'Afrobeat', 'Persian', 'Arabic'],
};

interface Props {
  genre: string;
  subGenre: string;
  onGenreChange: (genre: string) => void;
  onSubGenreChange: (subGenre: string) => void;
}

const fieldClass =
  'bg-inputBg border border-inputBorder rounded-lg p-3 flex items-center transition-colors';
const selectClass =
  'bg-transparent border-none outline-none w-full text-textPrimary font-ui appearance-none';

export const GenreSelect = ({ genre, subGenre, onGenreChange, onSubGenreChange }: Props) => {
  const { t } = useTranslation();
  const subGenres = genre ? (GENRE_TREE[genre] ?? []) : [];
  const hasSub = subGenres.length > 0;

  return (
    <div className="space-y-3">
      {/* Primary genre */}
      <div className={fieldClass}>
        <Tag className="w-5 h-5 text-textSecondary me-3 flex-shrink-0" />
        <select
          value={genre}
          onChange={e => {
            onGenreChange(e.target.value);
            onSubGenreChange(''); // reset child when parent changes
          }}
          className={selectClass}
        >
          <option value="" disabled className="bg-inputBg text-textPrimary">
            {t('Select a genre')}
          </option>
          {Object.keys(GENRE_TREE).map(g => (
            <option key={g} value={g} className="bg-inputBg text-textPrimary">{g}</option>
          ))}
        </select>
        <ChevronDown className="w-4 h-4 text-textSecondary ms-2 flex-shrink-0" />
      </div>

      {/* Secondary genre — mounts only when the parent has subgenres */}
      {hasSub && (
        <div className={`${fieldClass} animate-genre-drop`}>
          <ListTree className="w-5 h-5 text-gold me-3 flex-shrink-0" />
          <select
            value={subGenre}
            onChange={e => onSubGenreChange(e.target.value)}
            className={selectClass}
          >
            <option value="" className="bg-inputBg text-textPrimary">
              {t('Select a subgenre')}
            </option>
            {subGenres.map(s => (
              <option key={s} value={s} className="bg-inputBg text-textPrimary">{s}</option>
            ))}
          </select>
          <ChevronDown className="w-4 h-4 text-textSecondary ms-2 flex-shrink-0" />
        </div>
      )}
    </div>
  );
};
