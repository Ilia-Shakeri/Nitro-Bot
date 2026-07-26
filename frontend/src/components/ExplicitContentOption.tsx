import { useTranslation } from 'react-i18next';
import { FormToggle } from './FormToggle';

interface Props {
  checked: boolean;
  onChange: (checked: boolean) => void;
}

export const ExplicitContentOption = ({ checked, onChange }: Props) => {
  const { t } = useTranslation();

  return (
    <section className="mb-2 rounded-xl border border-gold/25 bg-card1 p-3">
      <FormToggle
        id="explicit-content"
        checked={checked}
        label={t('explicit_content_label')}
        onChange={() => onChange(!checked)}
      />
      <p className="mt-2 px-1 text-start text-xs leading-relaxed text-textSecondary">
        {t('explicit_content_description')}
      </p>
    </section>
  );
};
