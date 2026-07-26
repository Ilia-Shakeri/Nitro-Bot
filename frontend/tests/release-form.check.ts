import { isRtlLanguage, TRANSLATIONS } from '../src/i18n';
import { DEFAULT_PRICING, nitroUsdCents, tomanCents } from '../src/pricingValues';
import { changeMainGenre, validSubGenre } from '../src/utils/genres';
import {
  effectivePaymentMethod,
  paymentMethodsForLanguage,
} from '../src/utils/paymentMethods';
import {
  discountPercent,
  formatReleaseDate,
  releaseDateSentenceKey,
  releaseHistoryDirection,
  releaseStatusKey,
  releaseTotal,
} from '../src/utils/releasePresentation';
import {
  addArtist,
  addUniqueValue,
  dateFieldMode,
  emptyReleaseMetadata,
  naturalInputDirection,
  removeArtist,
  removeValue,
  releaseStepAction,
  selectPrimaryArtist,
  validateMappingChoice,
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
assert(
  validateMappingChoice(false, '', '', '') === 'mapping_required',
  'existing profile mapping must require one platform link',
);
assert(
  validateMappingChoice(false, '', 'https://spotify.example/artist', '') === null,
  'one Spotify mapping link must pass',
);
assert(
  validateMappingChoice(true, '', '', '') === 'profile_email_required',
  'new profile mapping must require email',
);
assert(
  validateMappingChoice(true, 'artist@example.com', '', '') === null,
  'new profile mapping with email must pass',
);

const required = {
  ...initial,
  songName: 'Song',
  artists: [{ name: 'Artist', role: 'primary' as const }],
  producers: ['Producer'],
  legalNames: ['Legal'],
  genre: 'Pop',
  releaseDate: '2000-01-01',
};
assert(validateReleaseMetadata(required) === 'release_date_past', 'past scheduled date must fail');
assert(
  validateReleaseMetadata({ ...required, producers: [] }) === 'producers_required',
  'producer must be required before review',
);
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
assert(releaseTotal(DEFAULT_PRICING, false, false) === 8, 'release total must be 8 without copyright');
assert(releaseTotal(DEFAULT_PRICING, false, true) === 10, 'release total must be 10 with copyright');
assert(discountPercent(DEFAULT_PRICING) === 60, 'discount must derive to 60 percent');
assert(nitroUsdCents(3, DEFAULT_PRICING) === 240, 'three Nitro must equal 240 cents');
assert(tomanCents(3, 100_000, DEFAULT_PRICING) === 24_000_000, 'Toman calculation must use integer cents');
assert(isRtlLanguage('fa') && isRtlLanguage('ar'), 'Persian and Arabic must be RTL');
assert(!isRtlLanguage('en') && !isRtlLanguage('ru'), 'English and Russian must be LTR');
same(paymentMethodsForLanguage('fa'), ['card', 'usdt'], 'Persian must show card and USDT');
for (const language of ['en', 'ar', 'ru']) {
  same(paymentMethodsForLanguage(language), ['usdt'], `${language} must show USDT only`);
  assert(effectivePaymentMethod(language, 'card') === 'usdt', `${language} must force USDT`);
}
assert(releaseHistoryDirection('fa') === 'rtl', 'Persian release names must be RTL');
assert(releaseHistoryDirection('ar') === 'rtl', 'Arabic release names must be RTL');
assert(releaseHistoryDirection('en') === 'ltr', 'English release names must be LTR');
assert(releaseHistoryDirection('ru') === 'ltr', 'Russian release names must be LTR');
assert(releaseHistoryDirection('fa', true) === 'ltr', 'technical release values must stay LTR');
assert(naturalInputDirection('', true) === 'rtl', 'empty Persian and Arabic input must be RTL');
assert(naturalInputDirection('', false) === 'ltr', 'empty English and Russian input must be LTR');
assert(naturalInputDirection('نام Artist', true) === 'auto', 'filled mixed-script name must use automatic direction');
same(changeMainGenre('Rock'), { genre: 'Rock', subGenre: '' }, 'main genre change must clear subgenre');
assert(validSubGenre('Rock', 'Punk'), 'matching subgenre must pass');
assert(!validSubGenre('Pop', 'Punk'), 'stale subgenre must fail');
assert(releaseStepAction('form', true) === 'review', 'first valid action must only open review');
assert(releaseStepAction('review', true) === 'submit', 'review confirmation may submit');
assert(releaseStepAction('form', false) === 'stay', 'invalid form must stay');
assert(
  releaseDateSentenceKey({ is_rerelease: false }) === 'scheduled_sentence',
  'scheduled history sentence key must be selected',
);
assert(
  releaseDateSentenceKey({ is_rerelease: true }) === 'rerelease_scheduled_sentence',
  're-release history sentence key must be selected',
);
assert(formatReleaseDate('2026-08-12', 'en').includes('2026'), 'release date must be locale formatted');
assert(releaseStatusKey({ status: 'failed', refunded_at: '2026-01-01' }) === 'rollback', 'refunded release must show rollback');
for (const language of ['en', 'fa', 'ar', 'ru'] as const) {
  for (const status of ['pending', 'staging', 'manual_staging', 'processing', 'completed', 'failed', 'rollback']) {
    assert(Boolean(TRANSLATIONS[language][status as keyof typeof TRANSLATIONS[typeof language]]), `${language} status ${status} must translate`);
  }
}
assert(
  TRANSLATIONS.fa.copyright_option_label === 'افزودن کپی‌رایت ({{price}} {{unit}})',
  'Persian copyright text and price slot must match',
);
for (const language of ['en', 'fa', 'ar', 'ru'] as const) {
  assert(
    TRANSLATIONS[language].copyright_option_label.includes('{{price}}'),
    `${language} copyright label must show backend price`,
  );
}

const englishKeys = Object.keys(TRANSLATIONS.en).sort();
for (const language of ['fa', 'ar', 'ru'] as const) {
  same(
    Object.keys(TRANSLATIONS[language]).sort(),
    englishKeys,
    `${language} translations must contain every visible key`,
  );
}

console.log('release form checks passed');
