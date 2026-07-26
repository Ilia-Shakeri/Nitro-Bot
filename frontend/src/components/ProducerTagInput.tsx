import { useTranslation } from 'react-i18next';
import { SlidersHorizontal } from 'lucide-react';
import { MultiValueInput } from './MultiValueInput';

interface Props {
  producers: string[];
  onChange: (producers: string[]) => void;
  labelPrefix?: string;
}

export const ProducerTagInput = ({ producers, onChange, labelPrefix }: Props) => {
  const { t } = useTranslation();
  return (
    <MultiValueInput
      label={t('Producers')}
      placeholder={t('producer_placeholder')}
      values={producers}
      onChange={onChange}
      addLabel={t('Add producer')}
      removeLabel={t('Remove producer')}
      labelPrefix={labelPrefix}
      required
      icon={<SlidersHorizontal className="h-5 w-5" />}
      emptyErrorKey="producers_empty"
      duplicateErrorKey="producers_duplicate"
    />
  );
};
