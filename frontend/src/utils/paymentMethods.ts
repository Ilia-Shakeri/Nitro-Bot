import type { PaymentConfig } from '../types/api';

export type TopupPaymentMethod =
  | 'card'
  | 'usdt'
  | 'btc'
  | 'bnb'
  | 'usdt_bnb'
  | 'telegram_stars';

export const MANUAL_CRYPTO_METHODS: TopupPaymentMethod[] = [
  'usdt',
  'btc',
  'bnb',
  'usdt_bnb',
];

export const isPersianPaymentLanguage = (language: string): boolean =>
  language.split('-')[0] === 'fa';

export const paymentMethodsForLanguage = (
  language: string,
  config?: PaymentConfig | null,
): TopupPaymentMethod[] => {
  const methods: TopupPaymentMethod[] = isPersianPaymentLanguage(language)
    ? ['card', ...MANUAL_CRYPTO_METHODS, 'telegram_stars']
    : [...MANUAL_CRYPTO_METHODS, 'telegram_stars'];
  return config ? methods.filter(method => Boolean(config[method])) : methods;
};

export const isManualCrypto = (method: TopupPaymentMethod) =>
  MANUAL_CRYPTO_METHODS.includes(method);

export const paymentMethodLabel = (method: TopupPaymentMethod) => ({
  card: 'Card to Card',
  usdt: 'USDT (TRC20)',
  btc: 'Bitcoin (BTC)',
  bnb: 'BNB (BEP20)',
  usdt_bnb: 'USDT (BNB Smart Chain/BEP20)',
  telegram_stars: 'Telegram Stars',
}[method]);
