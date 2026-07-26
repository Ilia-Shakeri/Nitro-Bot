export type TopupPaymentMethod = 'card' | 'usdt';

export const isPersianPaymentLanguage = (language: string): boolean =>
  language.split('-')[0] === 'fa';

export const paymentMethodsForLanguage = (language: string): TopupPaymentMethod[] =>
  isPersianPaymentLanguage(language) ? ['card', 'usdt'] : ['usdt'];

export const effectivePaymentMethod = (
  language: string,
  selected: TopupPaymentMethod,
): TopupPaymentMethod =>
  isPersianPaymentLanguage(language) ? selected : 'usdt';
