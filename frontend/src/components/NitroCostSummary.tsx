import { useTranslation } from 'react-i18next';
import { isRtlLanguage } from '../i18n';

interface Item {
  label: string;
  amount: number;
  originalAmount?: number;
}

interface Props {
  items: Item[];
}

export const NitroCostSummary = ({ items }: Props) => {
  const { t, i18n } = useTranslation();
  const total = items.reduce((sum, item) => sum + item.amount, 0);
  const locale = i18n.language.startsWith('ar') ? 'ar-SA' : isRtlLanguage(i18n.language) ? 'fa-IR' : 'en-US';

  return (
    <div className="mt-4 rounded-2xl border border-gold/25 bg-gold/5 p-4">
      <div className="flex items-center justify-between mb-3">
        <span className="text-sm font-ui text-textSecondary">{t('Payment Summary')}</span>
        <span className="text-lg font-title text-gold">
          {total.toLocaleString(locale)} {t('Nitro')}
        </span>
      </div>
      <div className="space-y-2">
        {items.map(item => (
          <div key={item.label} className="flex items-center justify-between text-sm">
            <span className="text-textSecondary">{item.label}</span>
            <span className="inline-flex items-center gap-2 font-ui text-textPrimary" dir="ltr">
              {item.originalAmount !== undefined && (
                <span className="text-textSecondary line-through" aria-label={t('Original price')}>
                  {item.originalAmount.toLocaleString(locale)} {t('Nitro')}
                </span>
              )}
              <span className="text-gold">
                {item.amount.toLocaleString(locale)} {t('Nitro')}
              </span>
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};
