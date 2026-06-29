import { useState, useEffect, useRef } from 'react';
import { ChevronRight, ChevronLeft } from 'lucide-react';

// ── Gregorian → Jalali ───────────────────────────────────────────────────────
function g2j(gy: number, gm: number, gd: number): [number, number, number] {
  const G = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334];
  const J = [31, 31, 31, 31, 31, 31, 30, 30, 30, 30, 30, 29];
  const gLeap = (y: number) => y % 4 === 0 && (y % 100 !== 0 || y % 400 === 0);

  let dn = 365 * (gy - 1) + Math.floor((gy - 1) / 4) - Math.floor((gy - 1) / 100) + Math.floor((gy - 1) / 400);
  dn += G[gm - 1] + gd;
  if (gLeap(gy) && gm > 2) dn++;

  let jdn = dn - 79;
  const np = Math.floor(jdn / 12053);
  jdn %= 12053;
  let jy = 979 + 33 * np + 4 * Math.floor(jdn / 1461);
  jdn %= 1461;
  if (jdn >= 366) { jy += Math.floor((jdn - 1) / 365); jdn = (jdn - 1) % 365; }
  let jm = 0;
  while (jm < 11 && jdn >= J[jm]) { jdn -= J[jm]; jm++; }
  return [jy, jm + 1, jdn + 1];
}

// ── Jalali → Gregorian ───────────────────────────────────────────────────────
function j2g(jy: number, jm: number, jd: number): [number, number, number] {
  const J = [31, 31, 31, 31, 31, 31, 30, 30, 30, 30, 30, 29];
  let jdn = 365 * (jy - 979) + Math.floor((jy - 979) / 33) * 8 + Math.floor(((jy - 979) % 33 + 3) / 4);
  for (let i = 0; i < jm - 1; i++) jdn += J[i];
  jdn += jd - 1;

  let gdn = jdn + 79;
  let gy = 1600 + 400 * Math.floor(gdn / 146097);
  gdn %= 146097;
  let leap = true;
  if (gdn >= 36525) {
    gdn--;
    gy += 100 * Math.floor(gdn / 36524);
    gdn %= 36524;
    if (gdn >= 365) gdn++;
    else leap = false;
  }
  gy += 4 * Math.floor(gdn / 1461);
  gdn %= 1461;
  if (gdn >= 366) { leap = false; gdn--; gy += Math.floor(gdn / 365); gdn %= 365; }
  const GM = [31, leap ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
  let gm = 0;
  while (gm < 11 && gdn >= GM[gm]) { gdn -= GM[gm]; gm++; }
  return [gy, gm + 1, gdn + 1];
}

// ── Jalali month length ──────────────────────────────────────────────────────
function jMonthLen(jy: number, jm: number): number {
  if (jm <= 6) return 31;
  if (jm <= 11) return 30;
  const breaks = [1, 5, 9, 13, 17, 22, 26, 30];
  const mod = ((jy - (jy > 0 ? 474 : 473)) % 2820 + 474 + 38) % 2820 % 128;
  return breaks.indexOf(mod) !== -1 ? 30 : 29;
}

const fa = (n: number | string) => String(n).replace(/\d/g, d => '۰۱۲۳۴۵۶۷۸۹'[+d]);
const MONTHS = ['فروردین','اردیبهشت','خرداد','تیر','مرداد','شهریور','مهر','آبان','آذر','دی','بهمن','اسفند'];
const DAYS   = ['ش','ی','د','س','چ','پ','ج']; // Sat … Fri

// ── Component ────────────────────────────────────────────────────────────────
interface Props { onChange: (isoDate: string) => void; }

export const PersianDatePicker = ({ onChange }: Props) => {
  const now   = new Date();
  const [ty, tm, td] = g2j(now.getFullYear(), now.getMonth() + 1, now.getDate());

  const [sel,   setSel]   = useState<[number, number, number] | null>(null);
  const [viewY, setViewY] = useState(ty);
  const [viewM, setViewM] = useState(tm);
  const [open,  setOpen]  = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const h = (e: MouseEvent) => { if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false); };
    document.addEventListener('mousedown', h);
    return () => document.removeEventListener('mousedown', h);
  }, []);

  const prevM = () => viewM === 1  ? (setViewY(y => y - 1), setViewM(12)) : setViewM(m => m - 1);
  const nextM = () => viewM === 12 ? (setViewY(y => y + 1), setViewM(1))  : setViewM(m => m + 1);

  const pick = (d: number) => {
    setSel([viewY, viewM, d]);
    const [gy, gm, gd] = j2g(viewY, viewM, d);
    onChange(`${gy}-${String(gm).padStart(2, '0')}-${String(gd).padStart(2, '0')}`);
    setOpen(false);
  };

  // First weekday of current view (0=Sat … 6=Fri in Persian week)
  const [fg, fgm, fgd] = j2g(viewY, viewM, 1);
  const startOffset = (new Date(fg, fgm - 1, fgd).getDay() + 1) % 7;

  const total = jMonthLen(viewY, viewM);
  const cells: (number | null)[] = Array(startOffset).fill(null);
  for (let d = 1; d <= total; d++) cells.push(d);
  while (cells.length % 7 !== 0) cells.push(null);

  const displayLabel = sel
    ? `${fa(sel[0])}/${fa(String(sel[1]).padStart(2,'0'))}/${fa(String(sel[2]).padStart(2,'0'))}`
    : 'تاریخ انتشار را انتخاب کنید';

  return (
    <div className="relative w-full" ref={ref} dir="rtl">
      <button type="button" onClick={() => setOpen(o => !o)} className="w-full text-start bg-transparent border-none outline-none">
        <span className={`font-ui text-sm ${sel ? 'text-textPrimary' : 'text-textSecondary'}`}>{displayLabel}</span>
      </button>

      {open && (
        <div className="absolute top-full mt-2 z-50 rounded-2xl border border-gold/25 bg-card1 shadow-[0_12px_40px_rgba(0,0,0,0.7)] p-4 w-72">
          {/* Month navigation */}
          <div className="flex items-center justify-between mb-3">
            <button type="button" onClick={nextM} className="p-1 rounded-lg hover:bg-gold/20 transition">
              <ChevronRight className="w-4 h-4 text-gold" />
            </button>
            <span className="font-ui text-gold text-sm">{MONTHS[viewM - 1]} {fa(viewY)}</span>
            <button type="button" onClick={prevM} className="p-1 rounded-lg hover:bg-gold/20 transition">
              <ChevronLeft className="w-4 h-4 text-gold" />
            </button>
          </div>

          {/* Weekday headers */}
          <div className="grid grid-cols-7 mb-1">
            {DAYS.map(w => <div key={w} className="text-center text-xs font-ui text-gold/60 py-0.5">{w}</div>)}
          </div>

          {/* Days grid */}
          <div className="grid grid-cols-7 gap-y-0.5">
            {cells.map((day, i) => {
              if (!day) return <div key={i} />;
              const isToday = viewY === ty && viewM === tm && day === td;
              const isSel   = sel && sel[0] === viewY && sel[1] === viewM && sel[2] === day;
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
                  {fa(day)}
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};
