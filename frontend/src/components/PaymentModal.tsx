import WebApp from '@twa-dev/sdk';
import { ChevronDown, Upload, X } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  createStarsInvoice,
  getPaymentConfig,
  getPaymentQuote,
  getUsdtRate,
  submitReceipt,
} from '../api';
import { useToast } from '../context/ToastContext';
import { useUser } from '../context/UserContext';
import { isRtlLanguage } from '../i18n';
import { nitroUsdCents, tomanCents, usePricing } from '../pricing';
import type { CryptoQuote, PaymentConfig } from '../types/api';
import { localizeNumber, toFaNum } from '../utils/faNum';
import { errorText } from '../utils/formMessages';
import {
  isManualCrypto,
  isPersianPaymentLanguage,
  paymentMethodLabel,
  paymentMethodsForLanguage,
  type TopupPaymentMethod,
} from '../utils/paymentMethods';
import { PaymentDetails } from './PaymentDetails';

export const PaymentModal = ({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) => {
  const { t, i18n } = useTranslation();
  const { toast } = useToast();
  const { refreshUser } = useUser();
  const { pricing } = usePricing();
  const lang = i18n.language;
  const isPersian = isPersianPaymentLanguage(lang);
  const [amount, setAmount] = useState(pricing.minimum_topup_nitro);
  const [method, setMethod] = useState<TopupPaymentMethod>(isPersian ? 'card' : 'usdt');
  const [receipt, setReceipt] = useState<File | null>(null);
  const [submissionId, setSubmissionId] = useState(() => crypto.randomUUID());
  const [loading, setLoading] = useState(false);
  const [rate, setRate] = useState<number | null>(null);
  const [rateLoading, setRateLoading] = useState(isPersian);
  const [paymentConfig, setPaymentConfig] = useState<PaymentConfig | null>(null);
  const [configLoading, setConfigLoading] = useState(true);
  const [configError, setConfigError] = useState<string | null>(null);
  const [configAttempt, setConfigAttempt] = useState(0);
  const [quote, setQuote] = useState<CryptoQuote | null>(null);
  const [quoteError, setQuoteError] = useState('');
  const validAmount = Number.isInteger(amount) && amount >= pricing.minimum_topup_nitro ? amount : 0;
  const methods = useMemo(
    () => paymentMethodsForLanguage(lang, paymentConfig),
    [lang, paymentConfig],
  );
  const usdCents = nitroUsdCents(validAmount, pricing);
  const payableTomanCents = isPersian && rate ? tomanCents(validAmount, rate, pricing) : null;

  useEffect(() => {
    if (!isOpen) return;
    let cancelled = false;
    getPaymentConfig()
      .then(config => {
        if (cancelled) return;
        setPaymentConfig(config);
        setConfigError(null);
        const available = paymentMethodsForLanguage(lang, config);
        setMethod(current => available.includes(current) ? current : (available[0] ?? 'usdt'));
      })
      .catch((error: unknown) => {
        if (!cancelled) {
          setPaymentConfig(null);
          setConfigError(errorText(error, t));
        }
      })
      .finally(() => {
        if (!cancelled) setConfigLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [isOpen, lang, configAttempt, t]);

  useEffect(() => {
    if (!isOpen || method !== 'card') return;
    let cancelled = false;
    getUsdtRate()
      .then(response => {
        if (!cancelled) setRate(response.rate_toman);
      })
      .catch(() => {
        if (!cancelled) setRate(null);
      })
      .finally(() => {
        if (!cancelled) setRateLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [isOpen, method]);

  useEffect(() => {
    if (!isOpen || !validAmount || !isManualCrypto(method)) return;
    let cancelled = false;
    getPaymentQuote(validAmount, method)
      .then(response => {
        if (!cancelled) setQuote(response);
      })
      .catch((error: unknown) => {
        if (!cancelled) setQuoteError(errorText(error, t));
      })
    return () => {
      cancelled = true;
    };
  }, [isOpen, method, validAmount, t]);

  if (!isOpen) return null;

  const formatCents = (cents: number, keepDecimals = true) => {
    const whole = Math.floor(cents / 100);
    const fraction = String(cents % 100).padStart(2, '0');
    const value = keepDecimals || fraction !== '00' ? `${whole}.${fraction}` : String(whole);
    return isRtlLanguage(lang) ? toFaNum(value) : value;
  };

  const submitManual = async () => {
    if (!validAmount || !paymentConfig || method === 'telegram_stars' || !receipt) return;
    setLoading(true);
    try {
      await submitReceipt(
        receipt,
        amount,
        method,
        submissionId,
        quote?.transaction_id,
      );
      setSubmissionId(crypto.randomUUID());
      setReceipt(null);
      toast(t('Receipt submitted successfully. Awaiting admin approval.'), 'success');
      onClose();
    } catch (error: unknown) {
      toast(errorText(error, t), 'error');
    } finally {
      setLoading(false);
    }
  };

  const openStarsInvoice = async () => {
    if (!validAmount) return;
    setLoading(true);
    try {
      const invoice = await createStarsInvoice(validAmount);
      WebApp.openInvoice(invoice.invoice_url, status => {
        if (status === 'paid') {
          toast(t('invoice_paid'), 'success');
          globalThis.setTimeout(() => void refreshUser(), 700);
          onClose();
        } else if (status === 'cancelled') {
          toast(t('invoice_cancelled'), 'error');
        } else if (status === 'failed') {
          toast(t('invoice_failed'), 'error');
        }
      });
    } catch (error: unknown) {
      toast(errorText(error, t), 'error');
    } finally {
      setLoading(false);
    }
  };

  const selectedConfig = paymentConfig?.[method];
  const quoteLoading = isManualCrypto(method) && !quote && !quoteError;
  const submitDisabled = loading
    || !validAmount
    || !selectedConfig
    || (method !== 'telegram_stars' && !receipt)
    || (method === 'card' && payableTomanCents === null)
    || (isManualCrypto(method) && (!quote || quoteLoading));

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4" onClick={onClose} role="presentation">
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="payment-title"
        dir={isRtlLanguage(lang) ? 'rtl' : 'ltr'}
        className="relative max-h-[90vh] w-full max-w-sm overflow-y-auto rounded-2xl border border-gold/20 bg-card1/95 p-6 backdrop-blur-xl"
        onClick={event => event.stopPropagation()}
      >
        <button type="button" onClick={onClose} aria-label={t('Close')} className="absolute end-4 top-4 rounded-md text-textSecondary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gold">
          <X className="h-6 w-6" />
        </button>
        <h2 id="payment-title" className="mb-4 text-start text-xl font-bold text-gold">{t('Refill Nitro')}</h2>

        <div className="space-y-4">
          <div>
            <label htmlFor="nitro-amount" className="mb-1 block text-start text-sm text-textSecondary">{t('Nitro Amount')}</label>
            <div className="flex items-center gap-3 rounded-xl border border-inputBorder bg-inputBg p-2" dir="ltr">
              <button type="button" onClick={() => {
                setQuote(null);
                setQuoteError('');
                setAmount(current => Math.max(pricing.minimum_topup_nitro, current - 1));
              }} disabled={amount <= pricing.minimum_topup_nitro} aria-label={t('Decrease amount')} className="h-10 w-10 rounded-lg border border-gold/50 bg-card3 text-xl font-bold text-gold disabled:opacity-40">−</button>
              <input
                id="nitro-amount"
                type="number"
                min={pricing.minimum_topup_nitro}
                step="1"
                inputMode="numeric"
                value={amount}
                onChange={event => {
                  setQuote(null);
                  setQuoteError('');
                  setAmount(Number(event.target.value));
                }}
                onBlur={() => setAmount(current => Number.isFinite(current) ? Math.max(pricing.minimum_topup_nitro, Math.floor(current)) : pricing.minimum_topup_nitro)}
                className="min-w-0 flex-1 bg-transparent text-center font-title text-xl text-textPrimary outline-none"
              />
              <button type="button" onClick={() => {
                setQuote(null);
                setQuoteError('');
                setAmount(current => current + 1);
              }} aria-label={t('Increase amount')} className="h-10 w-10 rounded-lg border border-gold/50 bg-card3 text-xl font-bold text-gold">+</button>
            </div>
          </div>

          <div>
            <label htmlFor="payment-method" className="mb-1 block text-start text-sm text-textSecondary">{t('Payment Method')}</label>
            <span className="relative block">
              <select
                id="payment-method"
                value={method}
                onChange={event => {
                  const nextMethod = event.target.value as TopupPaymentMethod;
                  setMethod(nextMethod);
                  setReceipt(null);
                  setQuote(null);
                  setQuoteError('');
                  if (nextMethod === 'card') setRateLoading(true);
                }}
                disabled={configLoading || methods.length === 0}
                className="w-full appearance-none rounded-xl border border-inputBorder bg-inputBg p-3 pe-9 text-start text-textPrimary outline-none focus:border-gold/50 focus-visible:ring-2 focus-visible:ring-gold/20 disabled:opacity-50"
              >
                {methods.map(item => (
                  <option key={item} value={item} className="bg-card1 text-textPrimary">
                    {t(paymentMethodLabel(item))}
                  </option>
                ))}
              </select>
              <ChevronDown aria-hidden="true" className="pointer-events-none absolute end-3 top-1/2 h-4 w-4 -translate-y-1/2 text-textSecondary" />
            </span>
          </div>

          <div className="rounded-lg border border-inputBorder bg-inputBg/60 p-3">
            <div className="flex items-center justify-between text-xs text-textSecondary">
              <span>{t('Unit Price')}</span>
              <span dir="ltr">{formatCents(pricing.nitro_usd_price_cents)} USD</span>
            </div>
            <div className="mt-2 flex items-center justify-between text-sm font-semibold">
              <span>{t('Total')}</span>
              <span dir="ltr" className="text-gold">{formatCents(usdCents)} USD</span>
            </div>
            {method === 'card' && (
              <div className="mt-2 flex items-center justify-between text-sm">
                <span>{t('Live USD Rate')}</span>
                {rateLoading
                  ? <span className="text-xs text-textSecondary">{t('Fetching live rate...')}</span>
                  : rate
                    ? <span dir="ltr" className="text-gold">{localizeNumber(rate, lang)} {t('Toman')} / USDT</span>
                    : <span className="text-red-400">{t('Rate unavailable')}</span>}
              </div>
            )}
          </div>

          <PaymentDetails
            method={method}
            config={paymentConfig}
            loading={configLoading}
            error={configError}
            onRetry={() => {
              setPaymentConfig(null);
              setConfigError(null);
              setConfigLoading(true);
              setConfigAttempt(current => current + 1);
            }}
          />

          {method === 'card' && (
            <>
              <div className="rounded-xl border border-gold/25 bg-gold/5 p-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-textSecondary">{t('Amount to Pay')}</span>
                  <span dir="ltr" className="text-sm font-bold text-gold">
                    {payableTomanCents === null ? t('Rate unavailable') : `${formatCents(payableTomanCents, false)} ${t('Toman')}`}
                  </span>
                </div>
              </div>
              <p className="rounded-xl border border-card3 bg-card2/50 p-3 text-start text-xs leading-relaxed text-textSecondary">
                {t('Send the exact amount, then upload the transaction receipt below.')}
              </p>
            </>
          )}

          {isManualCrypto(method) && (
            <>
              <div className="rounded-xl border border-gold/25 bg-gold/5 p-3">
                <div className="flex items-center justify-between gap-3">
                  <span className="text-sm text-textSecondary">{t('Amount to Pay')}</span>
                  {quoteLoading
                    ? <span className="text-xs text-textSecondary">{t('Loading payment quote...')}</span>
                    : quote
                      ? <span dir="ltr" className="text-base font-bold text-gold">{quote.amount} {quote.asset}</span>
                      : <span className="text-end text-xs text-red-400">{quoteError || t('payment_quote_unavailable')}</span>}
                </div>
              </div>
              <p className="rounded-xl border border-card3 bg-card2/50 p-3 text-start text-xs leading-relaxed text-textSecondary">
                {t('crypto_processing_notice')}
              </p>
            </>
          )}

          {method !== 'telegram_stars' && (
            <>
              <input type="file" id="receiptUpload" accept=".jpg,.jpeg,.png,.webp,image/jpeg,image/png,image/webp" onChange={event => setReceipt(event.target.files?.[0] ?? null)} className="sr-only" />
              <label htmlFor="receiptUpload" className="flex min-h-24 cursor-pointer flex-col items-center justify-center rounded-xl border border-dashed border-card3 bg-card2/50 p-4">
                <Upload className="mb-2 h-8 w-8 text-gold" />
                <span dir="ltr" className="max-w-full truncate text-left text-sm font-semibold">{receipt?.name ?? t('Upload Receipt Screenshot')}</span>
              </label>
            </>
          )}

          {method === 'telegram_stars' && selectedConfig && (
            <div className="rounded-xl border border-gold/25 bg-gold/5 p-3">
              <div className="flex items-center justify-between gap-3">
                <span className="text-sm text-textSecondary">{t('Amount to Pay')}</span>
                <span dir="ltr" className="text-base font-bold text-gold">
                  {validAmount * (selectedConfig.stars_per_nitro ?? 0)} XTR
                </span>
              </div>
            </div>
          )}

          <button
            type="button"
            onClick={method === 'telegram_stars' ? openStarsInvoice : submitManual}
            disabled={submitDisabled}
            className="min-h-12 w-full rounded-xl bg-gold py-3 font-bold text-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white disabled:cursor-not-allowed disabled:opacity-50"
          >
            {loading
              ? t('Processing...')
              : method === 'card'
                ? t('Submit Receipt')
                : method === 'telegram_stars'
                  ? t('Pay with Telegram Stars')
                  : t('I Paid')}
          </button>
        </div>
      </div>
    </div>
  );
};
