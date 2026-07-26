import { BadgePercent } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import type { Pricing } from '../types/api';
import { discountPercent, localeForLanguage, releaseTotal } from '../utils/releasePresentation';

interface Props {
  pricing: Pricing;
  isEdit?: boolean;
  copyrightRequested: boolean;
}

export const NitroCostSummary = ({
  pricing,
  isEdit = false,
  copyrightRequested,
}: Props) => {
  const { t, i18n } = useTranslation();
  const locale = localeForLanguage(i18n.language);
  const number = (value: number) => value.toLocaleString(locale);
  const base = isEdit ? pricing.edit_release_price : pricing.discounted_release_price;
  const total = releaseTotal(pricing, isEdit, copyrightRequested);
  const savings = isEdit ? 0 : pricing.original_release_price - pricing.discounted_release_price;
  const percentage = discountPercent(pricing);

  return (
    <section
      className="mt-4 rounded-2xl border border-gold/25 bg-gold/5 p-4"
      aria-label={t('Payment Summary')}
    >
      <div className="mb-4 flex items-center justify-between gap-3">
        <h2 className="text-sm font-ui text-textSecondary">{t('Payment Summary')}</h2>
        {!isEdit && percentage > 0 && (
          <span className="inline-flex items-center gap-1 rounded-full border border-gold/35 bg-gold/15 px-2.5 py-1 text-xs font-ui text-gold">
            <BadgePercent aria-hidden="true" className="h-4 w-4" />
            {t('discount_badge', { percent: number(percentage) })}
          </span>
        )}
      </div>

      {!isEdit && (
        <div className="mb-3 grid grid-cols-2 gap-2 rounded-xl border border-inputBorder bg-background/50 p-3">
          <div>
            <p className="text-xs text-textSecondary">{t('Original price')}</p>
            <p className="text-sm font-ui text-textSecondary line-through">
              {number(pricing.original_release_price)} {t('Nitro')}
            </p>
          </div>
          <div className="text-end">
            <p className="text-xs text-textSecondary">{t('Current price')}</p>
            <p className="text-xl font-title text-gold">
              {number(pricing.discounted_release_price)} {t('Nitro')}
            </p>
          </div>
          <p className="col-span-2 text-xs text-emerald-400">
            {t('You save', { amount: number(savings) })}
          </p>
        </div>
      )}

      <div className="space-y-2 text-sm">
        <div className="flex items-center justify-between gap-3">
          <span className="text-textSecondary">
            {t(isEdit ? 'Edit release cost' : 'Discounted release cost')}
          </span>
          <span className="font-ui text-textPrimary">
            {number(base)} {t('Nitro')}
          </span>
        </div>
        {copyrightRequested && (
          <div className="flex items-center justify-between gap-3">
            <span className="text-textSecondary">{t('Copyright protection cost')}</span>
            <span className="font-ui text-textPrimary">
              +{number(pricing.copyright_price)} {t('Nitro')}
            </span>
          </div>
        )}
        <div className="mt-3 flex items-center justify-between gap-3 border-t border-gold/20 pt-3">
          <span className="font-ui text-textPrimary">{t('Total payable')}</span>
          <span className="text-xl font-title text-gold">
            {number(total)} {t('Nitro')}
          </span>
        </div>
      </div>
      <p className="sr-only">
        {t('price_screen_reader', {
          original: number(isEdit ? base : pricing.original_release_price),
          current: number(base),
          total: number(total),
        })}
      </p>
    </section>
  );
};
