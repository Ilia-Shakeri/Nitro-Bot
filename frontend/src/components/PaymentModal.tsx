import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { ChevronDown, Upload, X } from 'lucide-react';
import { getUsdtRate, submitReceipt } from '../api';
import { useToast } from '../context/ToastContext';
import { localizeNumber, toFaNum } from '../utils/faNum';
import { errorText } from '../utils/formMessages';
import { PaymentDetails } from './PaymentDetails';

const NITRO_PRICE_USD = 1;

export const PaymentModal = ({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) => {
  const { t, i18n } = useTranslation();
  const lang = i18n.language;
  const { toast } = useToast();
  const [amount, setAmount] = useState(10);
  const [method, setMethod] = useState('card');
  const [receipt, setReceipt] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [rate, setRate] = useState<number | null>(null);
  const [rateLoading, setRateLoading] = useState(false);
  const [rateError, setRateError] = useState(false);

  const isCrypto = method === 'usdt';
  const validAmount = Number.isFinite(amount) && amount > 0 ? amount : 0;
  const totalUsd = validAmount * NITRO_PRICE_USD;
  const totalToman = rate && rate > 0 ? totalUsd * rate : null;
  const cryptoAmount = isCrypto && rate && rate > 0 ? totalUsd : null;

  useEffect(() => {
    if (!isOpen) return;
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
  }, [isOpen]);

  if (!isOpen) return null;

  const fmtDecimal = (v: number) => {
    const s = v.toFixed(6).replace(/0+$/, '').replace(/\.$/, '');
    return lang.startsWith('fa') ? toFaNum(s) : s;
  };

  const handleUpload = async () => {
    if (!receipt || !Number.isFinite(amount) || amount <= 0) return;
    setLoading(true);
    try {
      await submitReceipt(receipt, amount, method);
      toast(t('Receipt submitted successfully. Awaiting admin approval.'), 'success');
      onClose();
    } catch (e: unknown) {
      toast(errorText(e, t), 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4">
      <div className="bg-card1 w-full max-w-sm rounded-2xl p-6 border border-gold/20 relative">
        <button onClick={onClose} className="absolute top-4 right-4 rtl:left-4 rtl:right-auto text-textSecondary hover:text-textPrimary">
          <X className="w-6 h-6" />
        </button>

        <h2 className="text-xl font-bold text-gold mb-4">{t('Refill Nitro')}</h2>

        <div className="space-y-4">
          <div>
            <label className="text-sm text-textSecondary block mb-1">{t('Nitro Amount')}</label>
            <input
              type="number"
              value={amount}
              onChange={e => setAmount(Number(e.target.value))}
              className="w-full bg-inputBg border border-inputBorder rounded-lg p-3 text-textPrimary outline-none"
              min="1"
            />
          </div>

          <div className="bg-inputBg/60 border border-inputBorder rounded-lg p-3 space-y-1">
            <div className="flex items-center justify-between text-xs text-textSecondary">
              <span>{t('Unit Price')}</span>
              <span dir="ltr">{localizeNumber(NITRO_PRICE_USD, lang)} USD</span>
            </div>
            <div className="flex items-center justify-between text-sm font-semibold text-textPrimary">
              <span>{t('Live USD Rate')}</span>
              {rateLoading ? (
                <span className="text-sm text-textSecondary">...</span>
              ) : rate ? (
                <span dir="ltr" className="text-sm font-bold text-gold">
                  {localizeNumber(rate, lang)} {t('Toman')} / USDT
                </span>
              ) : (
                <span className="text-sm text-red-400">{t('Rate unavailable')}</span>
              )}
            </div>
          </div>

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

          <div className="bg-inputBg/60 border border-inputBorder rounded-lg p-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-textSecondary">{t('Total')}</span>
              <span dir="ltr" className="text-sm font-bold text-gold">
                {totalToman !== null ? `${localizeNumber(totalToman, lang)} ${t('Toman')}` : t('Rate unavailable')}
              </span>
            </div>
            {rateError && <p className="text-[11px] text-red-400 mt-1">{t('Exchange fallback notice')}</p>}
          </div>

          <PaymentDetails method={method} />

          {isCrypto ? (
            <>
              <div className="bg-gold/5 border border-gold/25 rounded-xl p-3 space-y-1">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-textSecondary">{t('Amount to Pay')}</span>
                  {rateLoading ? (
                    <span className="text-sm text-textSecondary">...</span>
                  ) : cryptoAmount !== null ? (
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
                onClick={handleUpload}
                disabled={loading || !receipt}
                className="w-full bg-gold text-background font-bold py-3 rounded-xl shadow-lg hover:opacity-90 disabled:opacity-50 mt-4"
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
