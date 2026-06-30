const FA_DIGITS = ['۰', '۱', '۲', '۳', '۴', '۵', '۶', '۷', '۸', '۹'];

/** Replace every ASCII digit in the input with its Persian (FaNum) glyph. */
export const toFaNum = (input: string | number): string =>
  String(input).replace(/\d/g, (d) => FA_DIGITS[Number(d)]);

/**
 * Format a number for display: Persian digits with grouping in fa, plain
 * grouped English otherwise. Keeps every numeric surface locale-correct.
 */
export const localizeNumber = (value: number, lang: string): string =>
  lang.startsWith('fa') ? value.toLocaleString('fa-IR') : value.toLocaleString();
