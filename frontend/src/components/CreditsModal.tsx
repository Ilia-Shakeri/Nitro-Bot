import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { TrendingDown, TrendingUp, X } from 'lucide-react';
import { getLedger } from '../api';
import { localizeNumber } from '../utils/faNum';
import type { LedgerEntry } from '../types/api';
import { isRtlLanguage } from '../i18n';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  balance: number;
  onBuyNitro: () => void;
}

export const CreditsModal = ({ isOpen, onClose, balance, onBuyNitro }: Props) => {
  const { t, i18n } = useTranslation();
  const isRTL = isRtlLanguage(i18n.language);
  const dateLocale = i18n.language.startsWith('ar') ? 'ar-SA' : isRTL ? 'fa-IR' : 'en-US';
  const [ledger, setLedger] = useState<LedgerEntry[]>([]);

  useEffect(() => {
    if (isOpen) getLedger().then(setLedger);
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/60 backdrop-blur-sm" onClick={onClose}>
      <div
        className="bg-card1 w-full max-w-md rounded-t-3xl pb-10 border-t border-gold/20 shadow-2xl"
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
            {ledger.length === 0 ? (
              <p className="text-center font-light-ui text-sm text-textSecondary py-3">
                {t('No transactions yet')}
              </p>
            ) : (
              <div className="space-y-1.5 max-h-44 overflow-y-auto hide-scrollbar">
                {ledger.slice(0, 12).map(item => (
                  <div key={item.id} className="flex items-center gap-3 bg-background rounded-xl px-4 py-2">
                    {item.direction === 'credit'
                      ? <TrendingUp className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                      : <TrendingDown className="w-4 h-4 text-red-400 flex-shrink-0" />
                    }
                    <div className="flex-1 min-w-0">
                      <p className="font-ui text-sm text-textPrimary truncate">{item.title}</p>
                      <p className="font-light-ui text-xs text-textSecondary">
                        {new Date(item.created_at).toLocaleDateString(dateLocale, { year: 'numeric', month: 'short', day: 'numeric' })}
                      </p>
                    </div>
                    <div className="text-end">
                      <p className={`font-ui text-sm ${item.direction === 'credit' ? 'text-emerald-400' : 'text-red-400'}`}>
                        {item.direction === 'credit' ? '+' : '-'}{localizeNumber(item.amount, i18n.language)}
                      </p>
                      <p className={`font-light-ui text-xs ${item.status === 'approved' || item.status === 'completed' ? 'text-emerald-400' : 'text-amber-400'}`}>
                        {t(item.status)}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Buy button */}
          <button
            onClick={() => { onClose(); onBuyNitro(); }}
            className="w-full bg-gradient-to-r from-gold to-[#B8860B] text-background font-title py-3 rounded-2xl flex justify-center items-center gap-2 shadow-md hover:opacity-90 transition-opacity"
          >
            <img src="/Logo/Nitro.webp" alt="" className="w-5 h-5 object-contain select-none pointer-events-none brightness-0" />
            <span>{t('Refill Nitro')}</span>
          </button>
        </div>
      </div>
    </div>
  );
};
