import type { ReleaseArtist } from '../types/api';

export interface ReleaseMetadata {
  songName: string;
  artists: ReleaseArtist[];
  producers: string[];
  legalNames: string[];
  releaseDate: string;
  isRerelease: boolean;
  originalReleaseDate: string;
  genre: string;
  subGenre: string;
  copyrightRequested: boolean;
}

export const emptyReleaseMetadata = (): ReleaseMetadata => ({
  songName: '',
  artists: [],
  producers: [],
  legalNames: [],
  releaseDate: '',
  isRerelease: false,
  originalReleaseDate: '',
  genre: '',
  subGenre: '',
  copyrightRequested: false,
});

export const localTodayIso = () => {
  const today = new Date();
  return `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;
};

export const addUniqueValue = (values: string[], raw: string) => {
  const value = raw.trim();
  if (!value) return { values, error: 'value_empty' };
  if (values.some(item => item.toLocaleLowerCase() === value.toLocaleLowerCase())) {
    return { values, error: 'value_duplicate' };
  }
  return { values: [...values, value], error: null };
};

export const removeValue = (values: string[], index: number) =>
  values.filter((_, itemIndex) => itemIndex !== index);

export const addArtist = (artists: ReleaseArtist[], raw: string) => {
  const name = raw.trim();
  if (!name) return { artists, error: 'artists_empty' };
  if (artists.some(artist => artist.name.toLocaleLowerCase() === name.toLocaleLowerCase())) {
    return { artists, error: 'artists_duplicate' };
  }
  return {
    artists: [
      ...artists,
      { name, role: artists.length === 0 ? 'primary' as const : 'featured' as const },
    ],
    error: null,
  };
};

export const removeArtist = (artists: ReleaseArtist[], index: number) => {
  const next = artists.filter((_, artistIndex) => artistIndex !== index);
  if (next.length > 0 && !next.some(artist => artist.role === 'primary')) {
    next[0] = { ...next[0], role: 'primary' };
  }
  return next;
};

export const selectPrimaryArtist = (artists: ReleaseArtist[], index: number) =>
  artists.map((artist, artistIndex) => ({
    ...artist,
    role: artistIndex === index ? 'primary' as const : 'featured' as const,
  }));

export const dateFieldMode = (metadata: ReleaseMetadata) =>
  metadata.isRerelease ? ['rerelease', 'original'] as const : ['scheduled'] as const;

export const validateReleaseMetadata = (
  data: ReleaseMetadata,
  unchangedHistoricalDate?: string,
): string | null => {
  if (!data.songName.trim() || !data.genre || !data.releaseDate) return 'required_fields_missing';
  if (data.artists.length === 0) return 'artists_required';
  if (data.legalNames.length === 0) return 'legal_names_required';
  if (new Set(data.artists.map(artist => artist.name.trim().toLocaleLowerCase())).size !== data.artists.length) {
    return 'artists_duplicate';
  }
  if (data.artists.filter(artist => artist.role === 'primary').length !== 1) {
    return 'artists_one_primary';
  }
  if (new Set(data.legalNames.map(name => name.trim().toLocaleLowerCase())).size !== data.legalNames.length) {
    return 'legal_names_duplicate';
  }
  if (
    data.releaseDate < localTodayIso()
    && data.releaseDate !== unchangedHistoricalDate
  ) {
    return data.isRerelease ? 'rerelease_date_past' : 'release_date_past';
  }
  if (data.isRerelease) {
    if (!data.originalReleaseDate) return 'original_release_date_required';
    if (data.originalReleaseDate >= data.releaseDate) {
      return 'original_release_date_not_before_rerelease';
    }
  }
  return null;
};

export const appendReleaseMetadata = (form: FormData, data: ReleaseMetadata) => {
  form.append('song_name', data.songName.trim());
  form.append('artists', JSON.stringify(data.artists));
  form.append('producers', JSON.stringify(data.producers));
  form.append('legal_names', JSON.stringify(data.legalNames));
  form.append('release_date', data.releaseDate);
  form.append('is_rerelease', String(data.isRerelease));
  if (data.isRerelease) {
    form.append('original_release_date', data.originalReleaseDate);
  }
  form.append('genre', data.genre);
  if (data.subGenre) form.append('sub_genre', data.subGenre);
  form.append('copyright_requested', String(data.copyrightRequested));
};
