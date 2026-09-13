import type { ArtistMapping, ReleaseArtist } from '../types/api';
import { validGenre, validSubGenre } from './genres';

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
  explicitContent: boolean;
  pendingArtist: string;
  pendingProducer: string;
  pendingLegalName: string;
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
  explicitContent: false,
  pendingArtist: '',
  pendingProducer: '',
  pendingLegalName: '',
});

export type ReleaseStep = 'details' | 'mapping' | 'review';
export const MAX_ARTISTS = 6;
export const MAX_PRIMARY_ARTISTS = 3;
export const MAX_RELEASE_TEXT_LENGTH = 200;
export const MAX_RELEASE_NAMES = 20;
const ENGLISH_RELEASE_TEXT = /^[A-Za-z0-9 .,'&()[\]\-_/+!?:#]+$/;
const ENGLISH_ALNUM = /[A-Za-z0-9]/;

export const normalizeEnglishReleaseText = (raw: string) => {
  const value = raw.trim().replace(/\s+/g, ' ');
  if (!value || !ENGLISH_RELEASE_TEXT.test(value) || !ENGLISH_ALNUM.test(value)) {
    return { value, error: 'english_only_input' };
  }
  if (value.length > MAX_RELEASE_TEXT_LENGTH) {
    return { value, error: 'text_too_long' };
  }
  return { value, error: null };
};

export const localTodayIso = () => {
  const today = new Date();
  return `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;
};

export const addUniqueValue = (values: string[], raw: string) => {
  const normalized = normalizeEnglishReleaseText(raw);
  const value = normalized.value;
  if (!raw.trim()) return { values, error: 'value_empty' };
  if (normalized.error) return { values, error: normalized.error };
  if (values.some(item => item.toLocaleLowerCase() === value.toLocaleLowerCase())) {
    return { values, error: 'value_duplicate' };
  }
  return { values: [...values, value], error: null };
};

export const removeValue = (values: string[], index: number) =>
  values.filter((_, itemIndex) => itemIndex !== index);

export const addArtist = (artists: ReleaseArtist[], raw: string) => {
  const normalized = normalizeEnglishReleaseText(raw);
  const name = normalized.value;
  if (!name) return { artists, error: 'artists_empty' };
  if (normalized.error) return { artists, error: normalized.error };
  if (artists.length >= MAX_ARTISTS) return { artists, error: 'artists_max' };
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

export const toggleArtistRole = (artists: ReleaseArtist[], index: number) => {
  const target = artists[index];
  if (!target) return { artists, error: 'artists_invalid' };
  const primaryCount = artists.filter(artist => artist.role === 'primary').length;
  if (target.role === 'primary' && primaryCount === 1) {
    return { artists, error: 'artists_primary_required' };
  }
  if (target.role === 'featured' && primaryCount >= MAX_PRIMARY_ARTISTS) {
    return { artists, error: 'artists_primary_max' };
  }
  return {
    artists: artists.map((artist, artistIndex) => (
      artistIndex === index
        ? { ...artist, role: artist.role === 'primary' ? 'featured' : 'primary' }
        : artist
    )) as ReleaseArtist[],
    error: null,
  };
};

export const dateFieldMode = (metadata: ReleaseMetadata) =>
  metadata.isRerelease ? ['rerelease', 'original'] as const : ['scheduled'] as const;

export const releaseStepAction = (
  step: ReleaseStep,
  valid: boolean,
): 'stay' | 'mapping' | 'review' | 'submit' => {
  if (!valid) return 'stay';
  if (step === 'details') return 'mapping';
  if (step === 'mapping') return 'review';
  return 'submit';
};

export const validateReleaseMetadata = (
  data: ReleaseMetadata,
  unchangedHistoricalDate?: string,
): string | null => {
  if (!data.songName.trim() || !data.genre || !data.releaseDate) return 'required_fields_missing';
  if (!validGenre(data.genre)) return 'genre_invalid';
  const songError = normalizeEnglishReleaseText(data.songName).error;
  if (songError === 'text_too_long') return 'song_name_too_long';
  if (songError) return 'english_only_input';
  if (data.artists.length === 0) return 'artists_required';
  if (data.artists.length > MAX_ARTISTS) return 'artists_max';
  if (data.producers.length === 0) return 'producers_required';
  if (data.legalNames.length === 0) return 'legal_names_required';
  if (data.producers.length > MAX_RELEASE_NAMES) return 'producers_max';
  if (data.legalNames.length > MAX_RELEASE_NAMES) return 'legal_names_max';
  if (data.producers.some(name => !name.trim())) return 'producers_empty';
  if (new Set(data.artists.map(artist => artist.name.trim().toLocaleLowerCase())).size !== data.artists.length) {
    return 'artists_duplicate';
  }
  if (data.artists.some(artist => normalizeEnglishReleaseText(artist.name).error === 'text_too_long')) return 'artists_too_long';
  if (data.producers.some(name => normalizeEnglishReleaseText(name).error === 'text_too_long')) return 'producers_too_long';
  if (data.legalNames.some(name => normalizeEnglishReleaseText(name).error === 'text_too_long')) return 'legal_names_too_long';
  if (data.artists.some(artist => normalizeEnglishReleaseText(artist.name).error)) return 'english_only_input';
  if (data.producers.some(name => normalizeEnglishReleaseText(name).error)) return 'english_only_input';
  if (data.legalNames.some(name => normalizeEnglishReleaseText(name).error)) return 'english_only_input';
  const primaryCount = data.artists.filter(artist => artist.role === 'primary').length;
  if (primaryCount === 0) return 'artists_primary_required';
  if (primaryCount > MAX_PRIMARY_ARTISTS) return 'artists_primary_max';
  if (new Set(data.legalNames.map(name => name.trim().toLocaleLowerCase())).size !== data.legalNames.length) {
    return 'legal_names_duplicate';
  }
  if (new Set(data.producers.map(name => name.trim().toLocaleLowerCase())).size !== data.producers.length) {
    return 'producers_duplicate';
  }
  if (!validSubGenre(data.genre, data.subGenre)) return 'sub_genre_invalid';
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

export const metadataErrorField = (
  data: ReleaseMetadata,
  error: string,
): 'song' | 'artists' | 'producers' | 'legal_names' | null => {
  if (error.startsWith('song_')) return 'song';
  if (error.startsWith('artists_')) return 'artists';
  if (error.startsWith('producers_')) return 'producers';
  if (error.startsWith('legal_names_')) return 'legal_names';
  if (error !== 'english_only_input') return null;
  if (normalizeEnglishReleaseText(data.songName).error) return 'song';
  if (data.artists.some(artist => normalizeEnglishReleaseText(artist.name).error)) return 'artists';
  if (data.producers.some(name => normalizeEnglishReleaseText(name).error)) return 'producers';
  if (data.legalNames.some(name => normalizeEnglishReleaseText(name).error)) return 'legal_names';
  return null;
};

export interface PendingCommitResult {
  metadata: ReleaseMetadata;
  error: string | null;
  field: 'song' | 'artists' | 'producers' | 'legal_names' | null;
}

export const commitPendingMetadata = (data: ReleaseMetadata): PendingCommitResult => {
  let metadata = { ...data };
  if (metadata.songName.trim()) {
    const song = normalizeEnglishReleaseText(metadata.songName);
    if (song.error) return { metadata, error: song.error, field: 'song' };
    metadata = { ...metadata, songName: song.value };
  }
  if (metadata.pendingArtist.trim()) {
    const result = addArtist(metadata.artists, metadata.pendingArtist);
    if (result.error) return { metadata, error: result.error, field: 'artists' };
    metadata = { ...metadata, artists: result.artists, pendingArtist: '' };
  }
  if (metadata.pendingProducer.trim()) {
    const result = addUniqueValue(metadata.producers, metadata.pendingProducer);
    if (result.error) return { metadata, error: result.error, field: 'producers' };
    metadata = { ...metadata, producers: result.values, pendingProducer: '' };
  }
  if (metadata.pendingLegalName.trim()) {
    const result = addUniqueValue(metadata.legalNames, metadata.pendingLegalName);
    if (result.error) return { metadata, error: result.error, field: 'legal_names' };
    metadata = { ...metadata, legalNames: result.values, pendingLegalName: '' };
  }
  return { metadata, error: null, field: null };
};

export const blankArtistMapping = (artistName: string): ArtistMapping => ({
  artist_name: artistName,
  requires_new_profile: false,
  dmb_has_account: false,
  profile_email: null,
  spotify_url: null,
  apple_music_url: null,
});

export const reconcileArtistMappings = (
  artists: ReleaseArtist[],
  mappings: ArtistMapping[],
) => {
  const existing = new Map(
    mappings.map(mapping => [mapping.artist_name.trim().toLocaleLowerCase(), mapping]),
  );
  return artists.map(artist => {
    const mapping = existing.get(artist.name.trim().toLocaleLowerCase());
    return mapping ? { ...mapping, artist_name: artist.name } : blankArtistMapping(artist.name);
  });
};

const ASCII_EMAIL = /^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+$/;
const isAscii = (value: string) =>
  Array.from(value).every(character => character.charCodeAt(0) <= 127);
const isValidArtistUrl = (value: string, platform: 'spotify' | 'apple') => {
  if (!isAscii(value)) return false;
  try {
    const url = new URL(value);
    if (
      value.length > 2048
      || url.protocol !== 'https:'
      || url.username
      || url.password
      || url.port
      || url.hash
    ) return false;
    const parts = url.pathname.split('/').filter(Boolean);
    if (platform === 'spotify') {
      return url.hostname === 'open.spotify.com' && parts.length === 2 && parts[0] === 'artist';
    }
    const artistIndex = parts[0] === 'artist' ? 0 : 1;
    return url.hostname === 'music.apple.com'
      && parts.length >= artistIndex + 3
      && parts[artistIndex] === 'artist'
      && /^\d+$/.test(parts.at(-1) ?? '');
  } catch {
    return false;
  }
};
export interface ArtistMappingValidationError {
  key: string;
  artist?: string;
}

export const validateArtistMappings = (
  artists: ReleaseArtist[],
  mappings: ArtistMapping[],
): ArtistMappingValidationError | null => {
  const reconciled = reconcileArtistMappings(artists, mappings);
  if (reconciled.length !== artists.length || mappings.length !== artists.length) {
    return { key: 'artist_mappings_incomplete' };
  }
  for (const mapping of reconciled) {
    if (mapping.requires_new_profile) {
      const email = mapping.profile_email?.trim() ?? '';
      if (email.length > 254 || !ASCII_EMAIL.test(email) || !isAscii(email)) {
        return {
          key: 'artist_mapping_email_required_for_artist',
          artist: mapping.artist_name,
        };
      }
    } else {
      const spotify = mapping.spotify_url?.trim() ?? '';
      const apple = mapping.apple_music_url?.trim() ?? '';
      if (!spotify && !apple) {
        return {
          key: 'artist_mapping_link_required_for_artist',
          artist: mapping.artist_name,
        };
      }
      if (
        (spotify && !isValidArtistUrl(spotify, 'spotify'))
        || (apple && !isValidArtistUrl(apple, 'apple'))
      ) {
        return {
          key: 'artist_mapping_url_invalid_for_artist',
          artist: mapping.artist_name,
        };
      }
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
  form.append('explicit_content', String(data.explicitContent));
};
