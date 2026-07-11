import { isRtlLanguage } from '../i18n';

const FA_DIGITS = ['\u06F0', '\u06F1', '\u06F2', '\u06F3', '\u06F4', '\u06F5', '\u06F6', '\u06F7', '\u06F8', '\u06F9'];

/** Replace every ASCII digit in the input with Persian digit glyphs. */
export const toFaNum = (input: string | number): string =>
  String(input).replace(/\d/g, (d) => FA_DIGITS[Number(d)]);

/** Format numbers for the active writing direction. */
export const localizeNumber = (value: number, lang: string): string => {
  if (lang.startsWith('fa')) return value.toLocaleString('fa-IR');
  if (lang.startsWith('ar')) return value.toLocaleString('ar-SA');
  if (isRtlLanguage(lang)) return value.toLocaleString();
  return value.toLocaleString();
};
