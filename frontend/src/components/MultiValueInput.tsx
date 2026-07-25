import { useId, useState } from 'react';
import { Plus, X } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { addUniqueValue, removeValue } from '../utils/releaseForm';

interface Props {
  label: string;
  placeholder: string;
  values: string[];
  onChange: (values: string[]) => void;
  addLabel: string;
  removeLabel: string;
  labelPrefix?: string;
  required?: boolean;
}

export const MultiValueInput = ({
  label,
  placeholder,
  values,
  onChange,
  addLabel,
  removeLabel,
  labelPrefix,
  required = false,
}: Props) => {
  const { t } = useTranslation();
  const inputId = useId();
  const [value, setValue] = useState('');
  const [error, setError] = useState('');

  const addValue = () => {
    const result = addUniqueValue(values, value);
    if (result.error) {
      setError(t(result.error));
      return;
    }
    onChange(result.values);
    setValue('');
    setError('');
  };

  return (
    <div>
      <label htmlFor={inputId} className="block text-gold font-ui mb-2 text-sm">
        {labelPrefix ? `${labelPrefix} ` : ''}{label}{required ? ' *' : ''}
      </label>
      <div className="rounded-lg border border-inputBorder bg-inputBg p-3 focus-within:border-gold/60">
        <div className="flex items-center gap-2">
          <input
            id={inputId}
            type="text"
            value={value}
            onChange={event => {
              setValue(event.target.value);
              setError('');
            }}
            onKeyDown={event => {
              if (event.key === 'Enter') {
                event.preventDefault();
                addValue();
              }
            }}
            dir="auto"
            aria-invalid={Boolean(error)}
            aria-describedby={error ? `${inputId}-error` : undefined}
            className="min-w-0 flex-1 bg-transparent text-textPrimary font-ui outline-none"
            placeholder={placeholder}
          />
          <button
            type="button"
            onClick={addValue}
            aria-label={addLabel}
            className="inline-flex min-h-10 min-w-10 items-center justify-center rounded-lg border border-gold/40 text-gold hover:bg-gold/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gold"
          >
            <Plus className="h-4 w-4" />
          </button>
        </div>
        {error && (
          <p id={`${inputId}-error`} role="alert" className="mt-2 text-xs text-red-400">
            {error}
          </p>
        )}
        {values.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-2" aria-live="polite">
            {values.map((name, index) => (
              <span
                key={`${name}-${index}`}
                dir="auto"
                className="inline-flex max-w-full items-center gap-1 rounded-full border border-gold/30 bg-gold/10 px-3 py-1 text-xs font-ui text-gold"
              >
                <span className="truncate">{name}</span>
                <button
                  type="button"
                  onClick={() => onChange(removeValue(values, index))}
                  className="inline-flex min-h-6 min-w-6 items-center justify-center rounded-full bg-gold/15 hover:bg-gold/30 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gold"
                  aria-label={`${removeLabel}: ${name}`}
                >
                  <X className="h-3 w-3" />
                </button>
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
