import genreTree from '../../../shared/release-genres.json';

export const GENRE_TREE: Readonly<Record<string, readonly string[]>> = genreTree;

export const changeMainGenre = (genre: string) => ({
  genre,
  subGenre: '',
});

export const validGenre = (genre: string) => Boolean(GENRE_TREE[genre]);

export const validSubGenre = (genre: string, subGenre: string) =>
  validGenre(genre) && (!subGenre || Boolean(GENRE_TREE[genre]?.includes(subGenre)));
