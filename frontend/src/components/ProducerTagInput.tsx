import { useTranslation } from 'react-i18next';
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
    />
  );
};
