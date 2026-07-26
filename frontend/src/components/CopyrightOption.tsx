import { ShieldCheck } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { localeForLanguage } from '../utils/releasePresentation';

interface Props {
  checked: boolean;
  price: number;
  onChange: (checked: boolean) => void;
}

export const CopyrightOption = ({ checked, price, onChange }: Props) => {
  const { t, i18n } = useTranslation();
  const localizedPrice = price.toLocaleString(localeForLanguage(i18n.language));

  return (
    <section className="mb-2 rounded-xl border border-gold/25 bg-card1 p-4">
      <button
        id="copyright-requested"
        type="button"
        role="switch"
        aria-checked={checked}
        onClick={() => onChange(!checked)}
        className="flex min-h-12 w-full items-center justify-between gap-3 rounded-xl focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gold"
      >
        <span className="flex min-w-0 items-center gap-3">
          <ShieldCheck aria-hidden="true" className="h-5 w-5 flex-shrink-0 text-gold" />
          <span className="text-start text-sm font-ui text-textPrimary">
            {t('copyright_option_label', {
              price: localizedPrice,
              unit: t('Nitro'),
            })}
          </span>
        </span>
        <span className={`relative h-7 w-12 flex-shrink-0 rounded-full transition-colors ${checked ? 'bg-gold' : 'bg-card3'}`}>
          <span className={`absolute start-1 top-1 h-5 w-5 rounded-full bg-white shadow transition-transform ${checked ? 'ltr:translate-x-5 rtl:-translate-x-5' : ''}`} />
        </span>
      </button>
    </section>
  );
};
