import { useEffect, useId, useRef, useState } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { useTranslation } from 'react-i18next';

interface Props {
  value?: string;
  onChange: (isoDate: string) => void;
  minDate?: string;
  ariaLabel?: string;
}

const parseIsoDate = (value?: string) => {
  const match = value?.match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if (!match) return null;
  const year = Number(match[1]);
  const month = Number(match[2]) - 1;
  const day = Number(match[3]);
  const result = new Date(year, month, day);
  return result.getFullYear() === year
    && result.getMonth() === month
    && result.getDate() === day
    ? result
    : null;
};

const isoDate = (value: Date) =>
  `${value.getFullYear()}-${String(value.getMonth() + 1).padStart(2, '0')}-${String(value.getDate()).padStart(2, '0')}`;

export const PersianDatePicker = ({
  value,
  onChange,
  minDate,
  ariaLabel,
}: Props) => {
  const { t, i18n } = useTranslation();
  const buttonId = useId();
  const now = new Date();
  const initialDate = parseIsoDate(value);
  const minimum = parseIsoDate(minDate);
  const [selected, setSelected] = useState<Date | null>(initialDate);
  const [viewYear, setViewYear] = useState(initialDate?.getFullYear() ?? now.getFullYear());
  const [viewMonth, setViewMonth] = useState(initialDate?.getMonth() ?? now.getMonth());
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const close = (event: MouseEvent) => {
      if (ref.current && !ref.current.contains(event.target as Node)) setOpen(false);
    };
    document.addEventListener('mousedown', close);
    return () => document.removeEventListener('mousedown', close);
  }, []);

  const moveMonth = (offset: number) => {
    const next = new Date(viewYear, viewMonth + offset, 1);
    setViewYear(next.getFullYear());
    setViewMonth(next.getMonth());
  };
  const firstDay = new Date(viewYear, viewMonth, 1).getDay();
  const daysInMonth = new Date(viewYear, viewMonth + 1, 0).getDate();
  const cells: (number | null)[] = Array(firstDay).fill(null);
  for (let day = 1; day <= daysInMonth; day += 1) cells.push(day);
  while (cells.length % 7 !== 0) cells.push(null);

  const locale = i18n.language.startsWith('fa')
    ? 'fa-IR-u-ca-gregory'
    : i18n.language.startsWith('ar')
      ? 'ar-u-ca-gregory'
      : i18n.language.startsWith('ru')
        ? 'ru-RU'
        : 'en-US';
  const weekdays = Array.from({ length: 7 }, (_, index) =>
    new Intl.DateTimeFormat(locale, { weekday: 'narrow' }).format(
      new Date(2026, 0, 4 + index),
    ));
  const monthLabel = new Intl.DateTimeFormat(locale, {
    month: 'long',
    year: 'numeric',
  }).format(new Date(viewYear, viewMonth, 1));

  return (
    <div className="relative w-full" ref={ref} dir="ltr">
      <button
        id={buttonId}
        type="button"
        aria-label={ariaLabel ?? t('Select release date')}
        aria-haspopup="dialog"
        aria-expanded={open}
        onClick={() => setOpen(current => !current)}
        className="w-full rounded-sm bg-transparent text-start outline-none focus-visible:ring-2 focus-visible:ring-gold"
      >
        <span className={`font-ui text-sm ${selected ? 'text-textPrimary' : 'text-textSecondary'}`}>
          {selected ? isoDate(selected) : t('Select release date')}
        </span>
      </button>

      {open && (
        <div
          role="dialog"
          aria-label={ariaLabel ?? t('Select release date')}
          className="absolute start-0 top-full z-50 mt-2 w-72 rounded-2xl border border-gold/25 bg-card1 p-4 shadow-[0_12px_40px_rgba(0,0,0,0.7)]"
        >
          <div className="mb-3 flex items-center justify-between">
            <button
              type="button"
              onClick={() => moveMonth(-1)}
              aria-label={t('Previous month')}
              className="min-h-9 min-w-9 rounded-lg p-1 text-gold hover:bg-gold/20 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gold"
            >
              <ChevronLeft className="mx-auto h-4 w-4" />
            </button>
            <span className="text-sm font-ui text-gold">{monthLabel}</span>
            <button
              type="button"
              onClick={() => moveMonth(1)}
              aria-label={t('Next month')}
              className="min-h-9 min-w-9 rounded-lg p-1 text-gold hover:bg-gold/20 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gold"
            >
              <ChevronRight className="mx-auto h-4 w-4" />
            </button>
          </div>
          <div className="mb-1 grid grid-cols-7">
            {weekdays.map((weekday, index) => (
              <div key={`${weekday}-${index}`} className="py-0.5 text-center text-xs font-ui text-gold/60">
                {weekday}
              </div>
            ))}
          </div>
          <div className="grid grid-cols-7 gap-y-0.5">
            {cells.map((day, index) => {
              if (!day) return <div key={`empty-${index}`} />;
              const candidate = new Date(viewYear, viewMonth, day);
              const disabled = Boolean(minimum && candidate < minimum);
              const isToday = isoDate(candidate) === isoDate(now);
              const isSelected = Boolean(selected && isoDate(candidate) === isoDate(selected));
              return (
                <button
                  key={isoDate(candidate)}
                  type="button"
                  disabled={disabled}
                  aria-pressed={isSelected}
                  onClick={() => {
                    setSelected(candidate);
                    onChange(isoDate(candidate));
                    setOpen(false);
                  }}
                  className={[
                    'mx-auto flex h-8 w-8 items-center justify-center rounded-full text-xs transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gold',
                    isSelected ? 'bg-gold text-background font-title' : '',
                    isToday && !isSelected ? 'bg-gold/20 text-gold font-ui' : '',
                    !isSelected && !isToday ? 'text-textPrimary font-light-ui hover:bg-gold/15' : '',
                    disabled ? 'cursor-not-allowed opacity-25 hover:bg-transparent' : '',
                  ].join(' ')}
                >
                  {new Intl.NumberFormat(locale, { useGrouping: false }).format(day)}
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};
