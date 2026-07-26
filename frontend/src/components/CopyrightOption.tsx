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
      <label
        htmlFor="copyright-requested"
        className="flex min-h-12 cursor-pointer items-center gap-3"
      >
        <input
          id="copyright-requested"
          type="checkbox"
          checked={checked}
          onChange={event => onChange(event.target.checked)}
          className="h-5 w-5 flex-shrink-0 rounded border-inputBorder accent-[#D4AF37] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gold"
        />
        <ShieldCheck aria-hidden="true" className="h-5 w-5 flex-shrink-0 text-gold" />
        <span className="text-start text-sm font-ui text-textPrimary">
          {t('copyright_option_label', {
            price: localizedPrice,
            unit: t('Nitro'),
          })}
        </span>
      </label>
    </section>
  );
};
