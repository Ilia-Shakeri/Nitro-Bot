import { useState, useEffect, useRef } from 'react';
import { ChevronRight, ChevronLeft } from 'lucide-react';

const MONTHS = ['January','February','March','April','May','June','July','August','September','October','November','December'];
const DAYS   = ['Su','Mo','Tu','We','Th','Fr','Sa'];

interface Props { onChange: (isoDate: string) => void; }

export const PersianDatePicker = ({ onChange }: Props) => {
  const now   = new Date();
  const [sel,   setSel]   = useState<Date | null>(null);
  const [viewY, setViewY] = useState(now.getFullYear());
  const [viewM, setViewM] = useState(now.getMonth()); // 0-indexed
  const [open,  setOpen]  = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const h = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener('mousedown', h);
    return () => document.removeEventListener('mousedown', h);
  }, []);

  const prevM = () => viewM === 0  ? (setViewY(y => y - 1), setViewM(11)) : setViewM(m => m - 1);
  const nextM = () => viewM === 11 ? (setViewY(y => y + 1), setViewM(0))  : setViewM(m => m + 1);

  const daysInMonth = new Date(viewY, viewM + 1, 0).getDate();
  const firstDay    = new Date(viewY, viewM, 1).getDay(); // 0=Sunday

  const cells: (number | null)[] = Array(firstDay).fill(null);
  for (let d = 1; d <= daysInMonth; d++) cells.push(d);
  while (cells.length % 7 !== 0) cells.push(null);

  const pick = (d: number) => {
    const date = new Date(viewY, viewM, d);
    setSel(date);
    onChange(`${viewY}-${String(viewM + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`);
    setOpen(false);
  };

  const todayY = now.getFullYear();
  const todayM = now.getMonth();
  const todayD = now.getDate();

  const displayLabel = sel
    ? `${sel.getFullYear()}/${String(sel.getMonth() + 1).padStart(2, '0')}/${String(sel.getDate()).padStart(2, '0')}`
    : 'Select release date';

  return (
    <div className="relative w-full" ref={ref} dir="ltr">
      <button
        type="button"
        onClick={() => setOpen(o => !o)}
        className="w-full text-start bg-transparent border-none outline-none"
      >
        <span className={`font-ui text-sm ${sel ? 'text-textPrimary' : 'text-textSecondary'}`}>
          {displayLabel}
        </span>
      </button>

      {open && (
        <div className="absolute top-full mt-2 z-50 rounded-2xl border border-gold/25 bg-card1 shadow-[0_12px_40px_rgba(0,0,0,0.7)] p-4 w-72">
          {/* Month navigation */}
          <div className="flex items-center justify-between mb-3">
            <button type="button" onClick={prevM} className="p-1 rounded-lg hover:bg-gold/20 transition">
              <ChevronLeft className="w-4 h-4 text-gold" />
            </button>
            <span className="font-ui text-gold text-sm">{MONTHS[viewM]} {viewY}</span>
            <button type="button" onClick={nextM} className="p-1 rounded-lg hover:bg-gold/20 transition">
              <ChevronRight className="w-4 h-4 text-gold" />
            </button>
          </div>

          {/* Weekday headers */}
          <div className="grid grid-cols-7 mb-1">
            {DAYS.map(w => (
              <div key={w} className="text-center text-xs font-ui text-gold/60 py-0.5">{w}</div>
            ))}
          </div>

          {/* Days grid */}
          <div className="grid grid-cols-7 gap-y-0.5">
            {cells.map((day, i) => {
              if (!day) return <div key={i} />;
              const isToday = viewY === todayY && viewM === todayM && day === todayD;
              const isSel   = sel && sel.getFullYear() === viewY && sel.getMonth() === viewM && sel.getDate() === day;
              return (
                <button
                  key={i}
                  type="button"
                  onClick={() => pick(day)}
                  className={[
                    'mx-auto w-8 h-8 rounded-full text-xs flex items-center justify-center transition',
                    isSel   ? 'bg-gold text-background font-title shadow-[0_0_8px_rgba(212,175,55,0.5)]' : '',
                    isToday && !isSel ? 'bg-gold/20 text-gold font-ui' : '',
                    !isSel && !isToday ? 'text-textPrimary font-light-ui hover:bg-gold/15' : '',
                  ].join(' ')}
                >
                  {day}
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};
