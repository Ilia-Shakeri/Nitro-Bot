import { useState, useRef, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Tag, ChevronDown, ListTree } from 'lucide-react';

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

interface DropdownProps {
  icon: React.ReactNode;
  value: string;
  placeholder: string;
  options: string[];
  onChange: (val: string) => void;
}

const CustomDropdown = ({ icon, value, placeholder, options, onChange }: DropdownProps) => {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const h = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener('mousedown', h);
    return () => document.removeEventListener('mousedown', h);
  }, []);

  return (
    <div className="relative" ref={ref}>
      <button
        type="button"
        onClick={() => setOpen(o => !o)}
        className={[
          'w-full bg-inputBg border rounded-lg p-3 flex items-center gap-3 transition-all duration-200',
          open ? 'border-gold/60 shadow-[0_0_0_2px_rgba(212,175,55,0.15)]' : 'border-inputBorder hover:border-gold/40',
        ].join(' ')}
      >
        {icon}
        <span className={`flex-1 text-start font-ui text-sm ${value ? 'text-textPrimary' : 'text-textSecondary'}`}>
          {value || placeholder}
        </span>
        <ChevronDown
          className={`w-4 h-4 text-textSecondary flex-shrink-0 transition-transform duration-200 ${open ? 'rotate-180 text-gold' : ''}`}
        />
      </button>

      {open && (
        <div className="absolute top-full mt-1.5 z-50 w-full rounded-xl border border-gold/20 bg-card1 shadow-[0_8px_32px_rgba(0,0,0,0.65)] overflow-hidden">
          <div className="max-h-52 overflow-y-auto hide-scrollbar py-1">
            {options.map(opt => (
              <button
                key={opt}
                type="button"
                onClick={() => { onChange(opt); setOpen(false); }}
                className={[
                  'w-full text-center px-4 py-2.5 text-sm font-ui transition-colors',
                  value === opt
                    ? 'text-gold bg-gold/10 font-ui'
                    : 'text-textPrimary hover:bg-gold/10 hover:text-gold',
                ].join(' ')}
              >
                {opt}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export const GenreSelect = ({ genre, subGenre, onGenreChange, onSubGenreChange }: Props) => {
  const { t } = useTranslation();
  const subGenres = genre ? (GENRE_TREE[genre] ?? []) : [];
  const hasSub = subGenres.length > 0;

  return (
    <div className="space-y-3">
      <CustomDropdown
        icon={<Tag className="w-5 h-5 text-textSecondary flex-shrink-0" />}
        value={genre}
        placeholder={t('Select a genre')}
        options={Object.keys(GENRE_TREE)}
        onChange={val => { onGenreChange(val); onSubGenreChange(''); }}
      />

      {hasSub && (
        <div className="animate-genre-drop">
          <CustomDropdown
            icon={<ListTree className="w-5 h-5 text-gold flex-shrink-0" />}
            value={subGenre}
            placeholder={t('Select a subgenre')}
            options={subGenres}
            onChange={onSubGenreChange}
          />
        </div>
      )}
    </div>
  );
};
