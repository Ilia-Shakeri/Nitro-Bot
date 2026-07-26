import { readFileSync } from 'node:fs';
import { isRtlLanguage, TRANSLATIONS } from '../src/i18n';
import { DEFAULT_PRICING, nitroUsdCents, tomanCents } from '../src/pricingValues';
import { parseApiResponse } from '../src/utils/apiResponse';
import { changeMainGenre, validSubGenre } from '../src/utils/genres';
import { paymentMethodsForLanguage } from '../src/utils/paymentMethods';
import {
  discountPercent,
  releaseTotal,
} from '../src/utils/releasePresentation';
import {
  addArtist,
  addUniqueValue,
  blankArtistMapping,
  commitPendingMetadata,
  dateFieldMode,
  emptyReleaseMetadata,
  normalizeEnglishReleaseText,
  reconcileArtistMappings,
  releaseStepAction,
  removeArtist,
  removeValue,
  toggleArtistRole,
  validateArtistMappings,
  validateReleaseMetadata,
} from '../src/utils/releaseForm';

const assert = (condition: unknown, message: string) => {
  if (!condition) throw new Error(message);
};
const same = (actual: unknown, expected: unknown, message: string) => {
  assert(JSON.stringify(actual) === JSON.stringify(expected), message);
};

const proxyConfig = readFileSync('nginx.conf', 'utf8');
for (const route of ['users', 'releases', 'transactions', 'support', 'pricing']) {
  assert(proxyConfig.includes(route), `Nginx must proxy ${route}`);
}
assert(proxyConfig.includes('proxy_pass http://backend:8000'), 'Nginx must reach backend');

let invalidResponseError = '';
try {
  await parseApiResponse(new Response('<!doctype html>', {
    status: 200,
    headers: { 'content-type': 'text/html' },
  }));
} catch (error) {
  invalidResponseError = error instanceof Error ? error.message : '';
}
assert(invalidResponseError === 'api_response_invalid', 'HTML response must not enter JSON parser');

const initial = emptyReleaseMetadata();
assert(!initial.copyrightRequested, 'copyright must start off');
assert(!initial.isRerelease, 're-release must start off');
same(dateFieldMode(initial), ['scheduled'], 'normal release must show scheduled date');
same(dateFieldMode({ ...initial, isRerelease: true }), ['rerelease', 'original'], 're-release must show two dates');

const first = addArtist([], ' First ').artists;
const second = addArtist(first, 'Second').artists;
same(second.map(artist => artist.role), ['primary', 'featured'], 'first artist must be primary');
const twoPrimary = toggleArtistRole(second, 1).artists;
same(twoPrimary.map(artist => artist.role), ['primary', 'primary'], 'multiple primary artists must work');
same(removeArtist(twoPrimary, 0), [{ name: 'Second', role: 'primary' }], 'removal must preserve primary');
assert(addArtist(first, ' first ').error === 'artists_duplicate', 'duplicate artist must fail');
let sixArtists = first;
for (const name of ['Two', 'Three', 'Four', 'Five', 'Six']) {
  sixArtists = addArtist(sixArtists, name).artists;
}
assert(addArtist(sixArtists, 'Seven').error === 'artists_max', 'seventh artist must fail');
let primaryLimitArtists = addArtist(twoPrimary, 'Third').artists;
primaryLimitArtists = toggleArtistRole(primaryLimitArtists, 2).artists;
primaryLimitArtists = addArtist(primaryLimitArtists, 'Fourth').artists;
assert(toggleArtistRole(primaryLimitArtists, 3).error === 'artists_primary_max', 'fourth primary must fail');
assert(toggleArtistRole([{ name: 'Only', role: 'primary' }], 0).error === 'artists_primary_required', 'last primary cannot turn off');

const legalOne = addUniqueValue([], 'Legal Name').values;
assert(addUniqueValue(legalOne, ' legal name ').error === 'value_duplicate', 'duplicate legal name must fail');
same(removeValue(addUniqueValue(legalOne, 'Second').values, 0), ['Second'], 'legal removal must preserve order');
assert(addUniqueValue([], 'نام').error === 'english_only_input', 'RTL script must fail');
assert(normalizeEnglishReleaseText(' Song   Name ').value === 'Song Name', 'whitespace must normalize');
assert(normalizeEnglishReleaseText('Песня').error === 'english_only_input', 'Cyrillic must fail');
assert(normalizeEnglishReleaseText('🎵').error === 'english_only_input', 'emoji must fail');

const pending = commitPendingMetadata({
  ...initial,
  pendingArtist: 'Artist',
  pendingProducer: 'Producer',
  pendingLegalName: 'Legal Name',
});
assert(!pending.error, 'page Continue must commit pending names');
same(pending.metadata.artists.map(item => item.name), ['Artist'], 'pending artist must commit once');
same(pending.metadata.producers, ['Producer'], 'pending producer must commit');
same(pending.metadata.legalNames, ['Legal Name'], 'pending legal name must commit');
assert(commitPendingMetadata({ ...pending.metadata, pendingArtist: 'artist' }).error === 'artists_duplicate', 'invalid pending artist must block');

const required = {
  ...initial,
  songName: 'Song',
  artists: [{ name: 'Artist', role: 'primary' as const }],
  producers: ['Producer'],
  legalNames: ['Legal'],
  genre: 'Pop',
  releaseDate: '2000-01-01',
};
assert(validateReleaseMetadata(required) === 'release_date_past', 'past date must fail');
assert(validateReleaseMetadata({ ...required, producers: [] }) === 'producers_required', 'producer must be required');
assert(validateReleaseMetadata({
  ...required,
  isRerelease: true,
  releaseDate: '2999-01-01',
  originalReleaseDate: '2000-01-01',
}) === null, 'historical original date must pass');

const artists = ['One', 'Two', 'Three', 'Four'].map((name, index) => ({
  name,
  role: index === 0 ? 'primary' as const : 'featured' as const,
}));
const mappings = reconcileArtistMappings(artists, []);
assert(mappings.length === 4, 'four artists must produce four mappings');
const completedMappings = mappings.map(mapping => ({
  ...mapping,
  spotify_url: `https://open.spotify.com/artist/${mapping.artist_name}`,
}));
assert(validateArtistMappings(artists, completedMappings) === null, 'complete mappings must pass');
assert(validateArtistMappings(artists, completedMappings.slice(0, 3)) !== null, 'missing mapping must fail');
same(
  reconcileArtistMappings(
    [{ name: 'one', role: 'primary' }],
    [{ ...blankArtistMapping('One'), spotify_url: 'https://open.spotify.com/artist/one' }],
  )[0].spotify_url,
  'https://open.spotify.com/artist/one',
  'mapping must survive case-only artist change',
);

assert(releaseStepAction('details', true) === 'mapping', 'details must lead to mapping');
assert(releaseStepAction('mapping', true) === 'review', 'mapping must lead to review');
assert(releaseStepAction('review', true) === 'submit', 'review must lead to submit');
assert(releaseStepAction('details', false) === 'stay', 'invalid details must stay');

assert(DEFAULT_PRICING.original_release_price === 20, 'original release price must be 20');
assert(DEFAULT_PRICING.discounted_release_price === 8, 'discounted release price must be 8');
assert(DEFAULT_PRICING.copyright_price === 2, 'copyright price must be 2');
assert(releaseTotal(DEFAULT_PRICING, false, false) === 8, 'release must cost 8');
assert(releaseTotal(DEFAULT_PRICING, false, true) === 10, 'copyright release must cost 10');
assert(discountPercent(DEFAULT_PRICING) === 60, 'discount must be 60 percent');
assert(nitroUsdCents(3, DEFAULT_PRICING) === 240, 'three Nitro must equal 240 cents');
assert(tomanCents(3, 100_000, DEFAULT_PRICING) === 24_000_000, 'Toman math must use integer cents');

assert(isRtlLanguage('fa') && isRtlLanguage('ar'), 'Persian and Arabic must be RTL');
assert(!isRtlLanguage('en') && !isRtlLanguage('ru'), 'English and Russian must be LTR');
same(paymentMethodsForLanguage('fa'), ['card', 'usdt', 'btc', 'bnb', 'usdt_bnb', 'telegram_stars'], 'Persian methods must include card');
for (const language of ['en', 'ar', 'ru']) {
  same(paymentMethodsForLanguage(language), ['usdt', 'btc', 'bnb', 'usdt_bnb', 'telegram_stars'], `${language} methods must exclude card`);
}
same(changeMainGenre('Rock'), { genre: 'Rock', subGenre: '' }, 'genre change must clear subgenre');
assert(validSubGenre('Rock', 'Punk'), 'valid subgenre must pass');
assert(!validSubGenre('Pop', 'Punk'), 'stale subgenre must fail');

for (const language of ['en', 'fa', 'ar', 'ru'] as const) {
  assert(TRANSLATIONS[language].song_placeholder === 'e.g., My Latest Release', `${language} song prompt must be English`);
  assert(TRANSLATIONS[language].artist_placeholder === 'e.g., Artist Name', `${language} artist prompt must be English`);
  assert(TRANSLATIONS[language]['Select a genre'] === 'Select a genre', `${language} genre prompt must be English`);
  assert(TRANSLATIONS[language].copyright_option_label.includes('{{price}}'), `${language} copyright label must show price`);
}
const englishKeys = Object.keys(TRANSLATIONS.en).sort();
for (const language of ['fa', 'ar', 'ru'] as const) {
  same(Object.keys(TRANSLATIONS[language]).sort(), englishKeys, `${language} translation keys must match`);
}

console.log('release form checks passed');
