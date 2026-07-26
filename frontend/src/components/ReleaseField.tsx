import type { ReactNode } from 'react';

interface Props {
  id?: string;
  label?: string;
  labelPrefix?: string;
  required?: boolean;
  icon: ReactNode;
  children: ReactNode;
  className?: string;
}

export const ReleaseField = ({
  id,
  label,
  labelPrefix,
  required,
  icon,
  children,
  className = '',
}: Props) => (
  <div className={className}>
    {label && (
      <label htmlFor={id} className="mb-2 block text-start text-sm font-ui text-gold">
        {labelPrefix ? `${labelPrefix} ` : ''}{label}{required ? ' *' : ''}
      </label>
    )}
    <div className="flex min-h-12 items-center rounded-lg border border-inputBorder bg-inputBg px-3 focus-within:border-gold/60 focus-within:ring-2 focus-within:ring-gold/15">
      <span aria-hidden="true" className="me-3 inline-flex h-5 w-5 flex-shrink-0 items-center justify-center text-textSecondary">
        {icon}
      </span>
      {children}
    </div>
  </div>
);
