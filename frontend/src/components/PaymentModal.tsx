import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { ChevronDown, Upload, X } from 'lucide-react';
import { getUsdtRate, submitReceipt } from '../api';
import { useToast } from '../context/ToastContext';
import { localizeNumber, toFaNum } from '../utils/faNum';
import { errorText } from '../utils/formMessages';
import { PaymentDetails } from './PaymentDetails';
import { isRtlLanguage } from '../i18n';

const NITRO_PRICE_USD = 1;
const MIN_CHARGE_AMOUNT = 3;

export const PaymentModal = ({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) => {
  const { t, i18n } = useTranslation();
  const lang = i18n.language;
  const { toast } = useToast();
  const [amount, setAmount] = useState(MIN_CHARGE_AMOUNT);
  const [method, setMethod] = useState('card');
  const [receipt, setReceipt] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [rate, setRate] = useState<number | null>(null);
  const [rateLoading, setRateLoading] = useState(false);
  const [rateError, setRateError] = useState(false);

  const isPersian = lang.split('-')[0] === 'fa';
  const effectiveMethod = isPersian ? method : 'usdt';
  const isCrypto = effectiveMethod === 'usdt';
  const validAmount = Number.isInteger(amount) && amount >= MIN_CHARGE_AMOUNT ? amount : 0;
  const totalUsd = validAmount * NITRO_PRICE_USD;
  const totalToman = isPersian && rate && rate > 0 ? totalUsd * rate : null;
  const cryptoAmount = isCrypto ? totalUsd : null;

  useEffect(() => {
    if (!isOpen || !isPersian) return;
    let cancelled = false;
    const load = async () => {
      setRateLoading(true);
      setRateError(false);
      try {
        const r = await getUsdtRate();
        if (!cancelled) setRate(r.rate_toman);
      } catch {
        if (!cancelled) {
          setRate(null);
          setRateError(true);
        }
      } finally {
        if (!cancelled) setRateLoading(false);
      }
    };
    load();
    return () => { cancelled = true; };
  }, [isOpen, isPersian]);

  if (!isOpen) return null;

  const fmtDecimal = (v: number) => {
    const s = v.toFixed(6).replace(/0+$/, '').replace(/\.$/, '');
    return isRtlLanguage(lang) ? toFaNum(s) : s;
  };

  const handleSubmitPayment = async () => {
    if (!Number.isInteger(amount) || amount < MIN_CHARGE_AMOUNT) return;
    if (!isCrypto && !receipt) return;
    setLoading(true);
    try {
      await submitReceipt(isCrypto ? null : receipt, amount, effectiveMethod);
      toast(t('Receipt submitted successfully. Awaiting admin approval.'), 'success');
      onClose();
    } catch (e: unknown) {
      toast(errorText(e, t), 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4" onClick={onClose}>
      <div className="bg-card1/85 backdrop-blur-xl w-full max-w-sm max-h-[90vh] overflow-y-auto rounded-2xl p-6 border border-gold/20 relative" onClick={e => e.stopPropagation()}>
        <button onClick={onClose} className="absolute top-4 right-4 rtl:left-4 rtl:right-auto text-textSecondary hover:text-textPrimary">
          <X className="w-6 h-6" />
        </button>

        <h2 className="text-xl font-bold text-gold mb-4">{t('Refill Nitro')}</h2>

        <div className="space-y-4">
          <div>
            <label className="text-sm text-textSecondary block mb-1">{t('Nitro Amount')}</label>
            <div className="flex items-center gap-3 rounded-xl border border-inputBorder bg-inputBg p-2">
              <button
                type="button"
                onClick={() => setAmount(current => Math.max(MIN_CHARGE_AMOUNT, current - 1))}
                disabled={amount <= MIN_CHARGE_AMOUNT}
                aria-label={t('Decrease amount')}
                className="h-10 w-10 rounded-lg border border-gold/50 bg-card3 text-xl font-bold text-gold disabled:cursor-not-allowed disabled:opacity-40 active:scale-[0.98] transition-all duration-300"
              >
                −
              </button>
              <input
                type="number"
                min={MIN_CHARGE_AMOUNT}
                step="1"
                inputMode="numeric"
                value={amount}
                onChange={event => setAmount(Number(event.target.value))}
                onBlur={() => setAmount(current => Number.isFinite(current) ? Math.max(MIN_CHARGE_AMOUNT, Math.floor(current)) : MIN_CHARGE_AMOUNT)}
                className="min-w-0 flex-1 bg-transparent text-center font-title text-xl text-textPrimary outline-none"
              />
              <button
                type="button"
                onClick={() => setAmount(current => current + 1)}
                aria-label={t('Increase amount')}
                className="h-10 w-10 rounded-lg border border-gold/50 bg-card3 text-xl font-bold text-gold active:scale-[0.98] transition-all duration-300"
              >
                +
              </button>
            </div>
          </div>

          {isPersian && (
            <div className="bg-inputBg/60 border border-inputBorder rounded-lg p-3 space-y-1">
              <div className="flex items-center justify-between text-xs text-textSecondary">
                <span>{t('Unit Price')}</span>
                <span dir="ltr">{localizeNumber(NITRO_PRICE_USD, lang)} USD</span>
              </div>
              <div className="flex items-center justify-between text-sm font-semibold text-textPrimary">
                <span>{t('Live USD Rate')}</span>
                {rateLoading ? (
                  <span className="inline-flex items-center gap-2 text-xs text-textSecondary animate-pulse">
                    <svg className="h-4 w-4 animate-spin text-gold" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                      <circle className="opacity-25" cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="3" />
                      <path className="opacity-90" fill="currentColor" d="M21 12a9 9 0 0 0-9-9v3a6 6 0 0 1 6 6h3Z" />
                    </svg>
                    {isPersian ? 'در حال دریافت نرخ زنده...' : 'Fetching live rate...'}
                  </span>
                ) : rate ? (
                  <span dir="ltr" className="text-sm font-bold text-gold">
                    {localizeNumber(rate, lang)} {t('Toman')} / USDT
                  </span>
                ) : (
                  <span className="text-sm text-red-400">{t('Rate unavailable')}</span>
                )}
              </div>
            </div>
          )}

          {isPersian && (
            <div>
              <label className="text-sm text-textSecondary block mb-1">{t('Payment Method')}</label>
              <div className="relative">
                <select
                  value={method}
                  onChange={e => setMethod(e.target.value)}
                  className="w-full bg-inputBg border border-inputBorder rounded-lg p-3 pr-9 rtl:pr-3 rtl:pl-9 text-textPrimary text-center outline-none appearance-none cursor-pointer focus:border-gold/50 transition-colors"
                >
                  <option value="card">{t('Card to Card')}</option>
                  <option value="usdt">{t('USDT (TRC20)')}</option>
                </select>
                <ChevronDown className="pointer-events-none absolute top-1/2 -translate-y-1/2 right-3 rtl:right-auto rtl:left-3 w-4 h-4 text-textSecondary" />
              </div>
            </div>
          )}

          {isPersian && (
            <div className="bg-inputBg/60 border border-inputBorder rounded-lg p-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-textSecondary">{t('Total')}</span>
                <span dir="ltr" className="text-sm font-bold text-gold">
                  {totalToman !== null ? `${localizeNumber(totalToman, lang)} ${t('Toman')}` : t('Rate unavailable')}
                </span>
              </div>
              {rateError && <p className="text-[11px] text-red-400 mt-1">{t('Exchange fallback notice')}</p>}
            </div>
          )}

          <PaymentDetails method={effectiveMethod} />

          {isCrypto ? (
            <>
              <div className="bg-gold/5 border border-gold/25 rounded-xl p-3 space-y-1">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-textSecondary">{t('Amount to Pay')}</span>
                  {cryptoAmount !== null ? (
                    <span dir="ltr" className="text-base font-bold text-gold">
                      {fmtDecimal(cryptoAmount)} USDT
                    </span>
                  ) : (
                    <span className="text-sm text-red-400">{t('Rate unavailable')}</span>
                  )}
                </div>
              </div>

              <p className="text-xs text-textSecondary leading-relaxed bg-card2/50 border border-card3 rounded-xl p-3">
                {t('crypto_processing_notice')}
              </p>

              <button
                onClick={handleSubmitPayment}
                disabled={loading || validAmount < MIN_CHARGE_AMOUNT}
                className="w-full bg-gold text-background font-bold py-3 rounded-xl shadow-lg hover:opacity-90 disabled:opacity-50 active:scale-[0.98] transition-all duration-300"
              >
                {loading ? t('Processing...') : t('I Paid')}
              </button>
            </>
          ) : (
            <>
              <div className="pt-2">
                <input
                  type="file"
                  id="receiptUpload"
                  accept="image/*"
                  onChange={e => setReceipt(e.target.files?.[0] || null)}
                  className="hidden"
                />
                <label
                  htmlFor="receiptUpload"
                  className="border border-dashed border-card3 bg-card2/50 rounded-xl p-4 flex flex-col items-center justify-center cursor-pointer hover:bg-card3/20 transition"
                >
                  <Upload className="text-gold w-8 h-8 mb-2" />
                  <span className="text-sm font-semibold">
                    {receipt ? receipt.name : t('Upload Receipt Screenshot')}
                  </span>
                </label>
              </div>

              <button
                onClick={handleSubmitPayment}
                disabled={loading || !receipt || validAmount < MIN_CHARGE_AMOUNT}
                className="w-full bg-gold text-background font-bold py-3 rounded-xl shadow-lg hover:opacity-90 disabled:opacity-50 mt-4 active:scale-[0.98] transition-all duration-300"
              >
                {loading ? t('Processing...') : t('Submit Receipt')}
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
};
