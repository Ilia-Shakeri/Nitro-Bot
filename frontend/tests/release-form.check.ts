import { isRtlLanguage, TRANSLATIONS } from '../src/i18n';
import { DEFAULT_PRICING, nitroUsdCents, tomanCents } from '../src/pricingValues';
import {
  addArtist,
  addUniqueValue,
  dateFieldMode,
  emptyReleaseMetadata,
  removeArtist,
  removeValue,
  selectPrimaryArtist,
  validateReleaseMetadata,
} from '../src/utils/releaseForm';

const assert = (condition: unknown, message: string) => {
  if (!condition) throw new Error(message);
};

const same = (actual: unknown, expected: unknown, message: string) => {
  assert(JSON.stringify(actual) === JSON.stringify(expected), message);
};

const initial = emptyReleaseMetadata();
assert(!initial.copyrightRequested, 'copyright must start off');
assert(!initial.isRerelease, 're-release must start off');
same(dateFieldMode(initial), ['scheduled'], 'normal release must show one scheduled date');
same(
  dateFieldMode({ ...initial, isRerelease: true }),
  ['rerelease', 'original'],
  're-release must show two differentiated dates',
);

const first = addArtist([], ' First ').artists;
const second = addArtist(first, 'Second').artists;
same(second.map(artist => artist.role), ['primary', 'featured'], 'artist roles must be assigned');
const switched = selectPrimaryArtist(second, 1);
same(switched.map(artist => artist.role), ['featured', 'primary'], 'primary role must switch');
same(removeArtist(switched, 1), [{ name: 'First', role: 'primary' }], 'removing primary must promote remaining artist');
assert(addArtist(first, ' first ').error === 'artists_duplicate', 'duplicate artist must fail');

const legalOne = addUniqueValue([], 'Legal Name').values;
assert(addUniqueValue(legalOne, ' legal name ').error === 'value_duplicate', 'duplicate legal name must fail');
same(removeValue(addUniqueValue(legalOne, 'Second').values, 0), ['Second'], 'legal name remove must keep order');

const required = {
  ...initial,
  songName: 'Song',
  artists: [{ name: 'Artist', role: 'primary' as const }],
  legalNames: ['Legal'],
  genre: 'Pop',
  releaseDate: '2000-01-01',
};
assert(validateReleaseMetadata(required) === 'release_date_past', 'past scheduled date must fail');
assert(
  validateReleaseMetadata({
    ...required,
    isRerelease: true,
    releaseDate: '2999-01-01',
    originalReleaseDate: '2000-01-01',
  }) === null,
  'historical original release date must pass',
);

assert(DEFAULT_PRICING.original_release_price === 20, 'original release price must be 20');
assert(DEFAULT_PRICING.discounted_release_price === 8, 'discounted release price must be 8');
assert(DEFAULT_PRICING.discounted_release_price + DEFAULT_PRICING.copyright_price === 10, 'copyright total must be 10');
assert(nitroUsdCents(3, DEFAULT_PRICING) === 240, 'three Nitro must equal 240 cents');
assert(tomanCents(3, 100_000, DEFAULT_PRICING) === 24_000_000, 'Toman calculation must use integer cents');
assert(isRtlLanguage('fa') && isRtlLanguage('ar'), 'Persian and Arabic must be RTL');
assert(!isRtlLanguage('en') && !isRtlLanguage('ru'), 'English and Russian must be LTR');

const englishKeys = Object.keys(TRANSLATIONS.en).sort();
for (const language of ['fa', 'ar', 'ru'] as const) {
  same(
    Object.keys(TRANSLATIONS[language]).sort(),
    englishKeys,
    `${language} translations must contain every visible key`,
  );
}

console.log('release form checks passed');
