import { useEffect, useState } from 'react';
import { ChevronDown, Upload, X } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { getPaymentConfig, getUsdtRate, submitReceipt } from '../api';
import { useToast } from '../context/ToastContext';
import { isRtlLanguage } from '../i18n';
import { nitroUsdCents, tomanCents, usePricing } from '../pricing';
import type { PaymentConfig } from '../types/api';
import { errorText } from '../utils/formMessages';
import { localizeNumber, toFaNum } from '../utils/faNum';
import { PaymentDetails } from './PaymentDetails';

export const PaymentModal = ({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) => {
  const { t, i18n } = useTranslation();
  const { toast } = useToast();
  const { pricing } = usePricing();
  const lang = i18n.language;
  const isPersian = lang.split('-')[0] === 'fa';
  const [amount, setAmount] = useState(pricing.minimum_topup_nitro);
  const [method, setMethod] = useState('card');
  const [receipt, setReceipt] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [rate, setRate] = useState<number | null>(null);
  const [rateLoading, setRateLoading] = useState(true);
  const [rateError, setRateError] = useState(false);
  const [paymentConfig, setPaymentConfig] = useState<PaymentConfig | null>(null);
  const effectiveMethod = isPersian ? method : 'usdt';
  const isCrypto = effectiveMethod === 'usdt';
  const validAmount = Number.isInteger(amount) && amount >= pricing.minimum_topup_nitro ? amount : 0;
  const usdCents = nitroUsdCents(validAmount, pricing);
  const payableTomanCents = isPersian && rate ? tomanCents(validAmount, rate, pricing) : null;

  useEffect(() => {
    if (!isOpen) return;
    let cancelled = false;
    getPaymentConfig()
      .then(config => {
        if (!cancelled) setPaymentConfig(config);
      })
      .catch(() => {
        if (!cancelled) setPaymentConfig(null);
      });
    return () => {
      cancelled = true;
    };
  }, [isOpen]);

  useEffect(() => {
    if (!isOpen || !isPersian) return;
    let cancelled = false;
    getUsdtRate()
      .then(response => {
        if (!cancelled) setRate(response.rate_toman);
      })
      .catch(() => {
        if (!cancelled) {
          setRate(null);
          setRateError(true);
        }
      })
      .finally(() => {
        if (!cancelled) setRateLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [isOpen, isPersian]);

  if (!isOpen) return null;

  const formatCents = (cents: number, keepDecimals = true) => {
    const whole = Math.floor(cents / 100);
    const fraction = String(cents % 100).padStart(2, '0');
    const value = keepDecimals || fraction !== '00' ? `${whole}.${fraction}` : String(whole);
    return isRtlLanguage(lang) ? toFaNum(value) : value;
  };

  const handleSubmitPayment = async () => {
    if (!validAmount || !paymentConfig || (!isCrypto && !receipt)) return;
    setLoading(true);
    try {
      await submitReceipt(isCrypto ? null : receipt, amount, effectiveMethod);
      toast(t('Receipt submitted successfully. Awaiting admin approval.'), 'success');
      onClose();
    } catch (error: unknown) {
      toast(errorText(error, t), 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4"
      onClick={onClose}
      role="presentation"
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="payment-title"
        dir={isRtlLanguage(lang) ? 'rtl' : 'ltr'}
        className="relative max-h-[90vh] w-full max-w-sm overflow-y-auto rounded-2xl border border-gold/20 bg-card1/90 p-6 backdrop-blur-xl"
        onClick={event => event.stopPropagation()}
      >
        <button
          type="button"
          onClick={onClose}
          aria-label={t('Close')}
          className="absolute end-4 top-4 text-textSecondary hover:text-textPrimary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gold"
        >
          <X className="h-6 w-6" />
        </button>
        <h2 id="payment-title" className="mb-4 text-xl font-bold text-gold">{t('Refill Nitro')}</h2>

        <div className="space-y-4">
          <div>
            <label htmlFor="nitro-amount" className="mb-1 block text-sm text-textSecondary">{t('Nitro Amount')}</label>
            <div className="flex items-center gap-3 rounded-xl border border-inputBorder bg-inputBg p-2" dir="ltr">
              <button
                type="button"
                onClick={() => setAmount(current => Math.max(pricing.minimum_topup_nitro, current - 1))}
                disabled={amount <= pricing.minimum_topup_nitro}
                aria-label={t('Decrease amount')}
                className="h-10 w-10 rounded-lg border border-gold/50 bg-card3 text-xl font-bold text-gold disabled:opacity-40"
              >
                −
              </button>
              <input
                id="nitro-amount"
                type="number"
                min={pricing.minimum_topup_nitro}
                step="1"
                inputMode="numeric"
                value={amount}
                onChange={event => setAmount(Number(event.target.value))}
                onBlur={() => setAmount(current =>
                  Number.isFinite(current)
                    ? Math.max(pricing.minimum_topup_nitro, Math.floor(current))
                    : pricing.minimum_topup_nitro)}
                className="min-w-0 flex-1 bg-transparent text-center font-title text-xl text-textPrimary outline-none"
              />
              <button
                type="button"
                onClick={() => setAmount(current => current + 1)}
                aria-label={t('Increase amount')}
                className="h-10 w-10 rounded-lg border border-gold/50 bg-card3 text-xl font-bold text-gold"
              >
                +
              </button>
            </div>
          </div>

          <div className="rounded-lg border border-inputBorder bg-inputBg/60 p-3">
            <div className="flex items-center justify-between text-xs text-textSecondary">
              <span>{t('Unit Price')}</span>
              <span dir="ltr">{formatCents(pricing.nitro_usd_price_cents)} USD</span>
            </div>
            {isPersian && (
              <div className="mt-2 flex items-center justify-between text-sm font-semibold">
                <span>{t('Live USD Rate')}</span>
                {rateLoading
                  ? <span className="text-xs text-textSecondary">{t('Fetching live rate...')}</span>
                  : rate
                    ? <span dir="ltr" className="text-gold">{localizeNumber(rate, lang)} {t('Toman')} / USDT</span>
                    : <span className="text-red-400">{t('Rate unavailable')}</span>}
              </div>
            )}
          </div>

          {isPersian && (
            <label className="block text-sm text-textSecondary">
              {t('Payment Method')}
              <span className="relative mt-1 block">
                <select
                  value={method}
                  onChange={event => setMethod(event.target.value)}
                  className="w-full appearance-none rounded-lg border border-inputBorder bg-inputBg p-3 pe-9 text-center text-textPrimary outline-none focus:border-gold/50"
                >
                  <option value="card">{t('Card to Card')}</option>
                  <option value="usdt">{t('USDT (TRC20)')}</option>
                </select>
                <ChevronDown className="pointer-events-none absolute end-3 top-1/2 h-4 w-4 -translate-y-1/2 text-textSecondary" />
              </span>
            </label>
          )}

          {isPersian && (
            <div className="rounded-lg border border-inputBorder bg-inputBg/60 p-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-textSecondary">{t('Total')}</span>
                <span dir="ltr" className="text-sm font-bold text-gold">
                  {payableTomanCents !== null
                    ? `${formatCents(payableTomanCents, false)} ${t('Toman')}`
                    : t('Rate unavailable')}
                </span>
              </div>
              {rateError && <p className="mt-1 text-[11px] text-red-400">{t('Exchange fallback notice')}</p>}
            </div>
          )}

          <PaymentDetails method={effectiveMethod} config={paymentConfig} />

          {isCrypto ? (
            <>
              <div className="rounded-xl border border-gold/25 bg-gold/5 p-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-textSecondary">{t('Amount to Pay')}</span>
                  <span dir="ltr" className="text-base font-bold text-gold">{formatCents(usdCents)} USDT</span>
                </div>
              </div>
              <p className="rounded-xl border border-card3 bg-card2/50 p-3 text-xs leading-relaxed text-textSecondary">
                {t('crypto_processing_notice')}
              </p>
              <button
                type="button"
                onClick={handleSubmitPayment}
                disabled={loading || !validAmount || !paymentConfig?.usdt}
                className="min-h-12 w-full rounded-xl bg-gold py-3 font-bold text-background disabled:opacity-50"
              >
                {loading ? t('Processing...') : t('I Paid')}
              </button>
            </>
          ) : (
            <>
              <input
                type="file"
                id="receiptUpload"
                accept=".jpg,.jpeg,.png,.webp,image/jpeg,image/png,image/webp"
                onChange={event => setReceipt(event.target.files?.[0] ?? null)}
                className="sr-only"
              />
              <label
                htmlFor="receiptUpload"
                className="flex min-h-24 cursor-pointer flex-col items-center justify-center rounded-xl border border-dashed border-card3 bg-card2/50 p-4"
              >
                <Upload className="mb-2 h-8 w-8 text-gold" />
                <span dir="auto" className="max-w-full truncate text-sm font-semibold">
                  {receipt?.name ?? t('Upload Receipt Screenshot')}
                </span>
              </label>
              <button
                type="button"
                onClick={handleSubmitPayment}
                disabled={loading || !receipt || !validAmount || !paymentConfig?.card}
                className="min-h-12 w-full rounded-xl bg-gold py-3 font-bold text-background disabled:opacity-50"
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
