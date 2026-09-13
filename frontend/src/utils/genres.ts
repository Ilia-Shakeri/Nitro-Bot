import genreTree from '../../../shared/release-genres.json';

export const GENRE_TREE: Readonly<Record<string, readonly string[]>> = genreTree;

export const changeMainGenre = (genre: string) => ({
  genre,
  subGenre: '',
});

export const validGenre = (genre: string) => Boolean(GENRE_TREE[genre]);

export const validSubGenre = (genre: string, subGenre: string) =>
  validGenre(genre) && (!subGenre || Boolean(GENRE_TREE[genre]?.includes(subGenre)));

const legacyGenre = (genre: string, subGenre: string): [string, string] | null => {
  if (genre === 'HipHop / Rap [Urban]') return ['Urban', 'HipHop / Rap'];
  if (genre === 'Pop') return ['Pop', ''];
  if (genre === 'Electronic / Dance') return ['Dance & Electronic', ''];
  if (genre === 'R&B / Soul') {
    return ['Urban', subGenre === 'Neo-Soul' ? 'Soul' : subGenre === 'Funk' ? 'Funk' : 'Rhythm and Blues'];
  }
  if (genre === 'Rock') {
    const subGenres: Record<string, string> = {
      Alternative: 'Alternative',
      'Indie Rock': 'International',
      'Hard Rock': "Metal (Hard 'n' Heavy)",
      Punk: 'Alternative',
      'Post-Rock': 'Progressive Rock',
    };
    return ['Rock / Rockpop', subGenres[subGenre] ?? ''];
  }
  if (genre === 'Folk') {
    if (subGenre === 'Singer-Songwriter') return ['Rock / Rockpop', 'Singer / Songwriter'];
    if (subGenre === 'Americana') return ['Country and Western', 'Americana'];
    return ['Worldmusic / Folklore / Folk Music', ''];
  }
  if (genre === 'Country') {
    return ['Country and Western', subGenre === 'Bluegrass' ? 'Bluegrass' : subGenre ? 'Mainstream' : ''];
  }
  if (genre === 'Reggae') return ['Urban', 'Reggae'];
  if (genre === 'Metal') return ['Rock / Rockpop', "Metal (Hard 'n' Heavy)"];
  if (genre === 'World') return ['Worldmusic / Folklore / Folk Music', ''];
  if (genre === 'Classical') {
    const subGenres: Record<string, string> = {
      Orchestral: 'Classical Music Instrumental',
      Piano: 'Classical Music Instrumental',
      Opera: 'Classic - Vocal',
      Chamber: 'Chamber Music',
    };
    return [genre, subGenres[subGenre] ?? subGenre];
  }
  if (genre === 'Jazz') return [genre, subGenre === 'Swing' ? 'Traditional / Swing' : subGenre ? 'Modern' : ''];
  return null;
};

export const normalizeGenreSelection = (genre: string, subGenre: string) => {
  if (validSubGenre(genre, subGenre)) return { genre, subGenre };
  const normalized = legacyGenre(genre, subGenre);
  return normalized
    ? { genre: normalized[0], subGenre: normalized[1] }
    : { genre: '', subGenre: '' };
};
