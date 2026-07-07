import { useState } from 'react';
import { X } from 'lucide-react';
import { useTranslation } from 'react-i18next';

interface Props {
  producers: string[];
  onChange: (producers: string[]) => void;
  labelPrefix?: string;
}

export const ProducerTagInput = ({ producers, onChange, labelPrefix }: Props) => {
  const { t } = useTranslation();
  const [value, setValue] = useState('');

  const addProducer = () => {
    const next = value.trim();
    if (!next || producers.some(item => item.toLowerCase() === next.toLowerCase())) return;
    onChange([...producers, next]);
    setValue('');
  };

  const removeProducer = (name: string) => {
    onChange(producers.filter(item => item !== name));
  };

  return (
    <div>
      <h3 className="text-gold font-ui mb-2 text-sm">
        {labelPrefix ? `${labelPrefix} ` : ''}{t('Producers')}
      </h3>
      <div className="bg-inputBg border border-inputBorder rounded-lg p-3">
        <input
          type="text"
          value={value}
          onChange={e => setValue(e.target.value)}
          onKeyDown={e => {
            if (e.key === 'Enter') {
              e.preventDefault();
              addProducer();
            }
          }}
          onBlur={addProducer}
          dir="ltr"
          className="bg-transparent border-none outline-none w-full text-textPrimary font-ui"
          placeholder="Producer name"
        />
        {producers.length > 0 && (
          <div className="flex flex-wrap gap-2 mt-3">
            {producers.map(name => (
              <span
                key={name}
                className="inline-flex items-center gap-1 rounded-full bg-gold/10 border border-gold/30 px-3 py-1 text-xs font-ui text-gold"
              >
                {name}
                <button
                  type="button"
                  onClick={() => removeProducer(name)}
                  className="w-4 h-4 rounded-full bg-gold/20 flex items-center justify-center hover:bg-gold/30"
                  aria-label={t('Remove producer')}
                >
                  <X className="w-3 h-3" />
                </button>
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
