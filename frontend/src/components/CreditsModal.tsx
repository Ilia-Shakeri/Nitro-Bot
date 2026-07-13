import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Clock3, TrendingUp, X } from 'lucide-react';
import { getLedger } from '../api';
import { localizeNumber } from '../utils/faNum';
import type { LedgerEntry } from '../types/api';
import { isRtlLanguage } from '../i18n';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  balance: number;
  onBuyNitro: () => void;
  onAllTransactions: () => void;
}

export const CreditsModal = ({ isOpen, onClose, balance, onBuyNitro, onAllTransactions }: Props) => {
  const { t, i18n } = useTranslation();
  const isRTL = isRtlLanguage(i18n.language);
  const dateLocale = i18n.language.startsWith('ar') ? 'ar-SA' : isRTL ? 'fa-IR' : 'en-US';
  const [ledger, setLedger] = useState<LedgerEntry[]>([]);

  useEffect(() => {
    if (isOpen) getLedger().then(setLedger);
  }, [isOpen]);

  const walletCharges = ledger.filter(item => item.direction === 'credit' && item.id.startsWith('tx-'));

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/60 backdrop-blur-sm" onClick={onClose}>
      <div
        className="bg-card1/85 backdrop-blur-xl w-full max-w-md max-h-[90vh] overflow-y-auto rounded-t-3xl pb-10 border-t border-gold/20 shadow-2xl"
        dir={isRTL ? 'rtl' : 'ltr'}
        onClick={e => e.stopPropagation()}
      >
        {/* Drag handle */}
        <div className="flex justify-center pt-3 pb-1">
          <div className="w-10 h-1 rounded-full bg-card3/60" />
        </div>

        {/* Header */}
        <div className="flex justify-between items-center px-5 py-2 mb-2">
          <div className="flex items-center gap-2">
            <img src="/Logo/Nitro.webp" alt="Nitro" className="w-6 h-6 object-contain aspect-square select-none pointer-events-none" />
            <h2 className="text-lg font-title text-gold">{t('Nitro')}</h2>
          </div>
          <button onClick={onClose} className="text-textSecondary hover:text-textPrimary transition p-1">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="px-5 space-y-4">
          {/* Balance card */}
          <div className="bg-background rounded-2xl p-5 border border-gold/20 text-center">
            <p className="text-sm font-ui text-textSecondary mb-1">{t('Your Balance')}</p>
            <p className="text-4xl font-title text-gold">{localizeNumber(balance, i18n.language)}</p>
            <p className="text-xs font-light-ui text-textSecondary mt-1">{t('Nitro Credits')}</p>
          </div>

          {/* Transactions */}
          <div>
            <p className="text-sm font-ui text-textSecondary mb-2">{t('Recent Transactions')}</p>
            {walletCharges.length === 0 ? (
              <p className="text-center font-light-ui text-sm text-textSecondary py-3">
                {t('No transactions yet')}
              </p>
            ) : (
              <div className="space-y-1.5 max-h-44 overflow-y-auto hide-scrollbar">
                {walletCharges.slice(0, 12).map(item => {
                  const addsCredit = item.status === 'approved' || item.status === 'pending';
                  return (
                    <div key={item.id} className="flex items-center gap-3 bg-background rounded-xl px-4 py-2">
                      {addsCredit
                        ? <TrendingUp className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                        : <Clock3 className="w-4 h-4 text-textSecondary flex-shrink-0" />
                      }
                      <div className="flex-1 min-w-0">
                        <p className="font-ui text-sm text-textPrimary truncate">{item.title}</p>
                        <p className="font-light-ui text-xs text-textSecondary">
                          {new Date(item.created_at).toLocaleDateString(dateLocale, { year: 'numeric', month: 'short', day: 'numeric' })}
                        </p>
                      </div>
                      <div className="text-end">
                        <p className={`font-ui text-sm ${addsCredit ? 'text-emerald-400' : 'text-textSecondary'}`}>
                          {addsCredit ? '+ ' : ''}{localizeNumber(item.amount, i18n.language)}
                        </p>
                        <p className={`font-light-ui text-xs ${item.status === 'approved' || item.status === 'completed' ? 'text-emerald-400' : 'text-amber-400'}`}>
                          {t(item.status)}
                        </p>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
            <button
              type="button"
              onClick={onAllTransactions}
              className="mt-3 w-full rounded-xl border border-gold/30 bg-gold/5 py-2.5 text-sm font-ui text-gold hover:bg-gold/10 active:scale-[0.98] transition-all duration-300"
            >
              {t('All Transactions')}
            </button>
          </div>

          {/* Buy button */}
          <button
            onClick={() => { onClose(); onBuyNitro(); }}
            className="w-full bg-gradient-to-r from-gold to-[#B8860B] text-background font-title py-3 rounded-2xl flex justify-center items-center gap-2 shadow-md hover:opacity-90 active:scale-[0.98] transition-all duration-300"
          >
            <img src="/Logo/Nitro.webp" alt="" className="w-5 h-5 object-contain select-none pointer-events-none brightness-0" />
            <span>{t('Refill Nitro')}</span>
          </button>
        </div>
      </div>
    </div>
  );
};
