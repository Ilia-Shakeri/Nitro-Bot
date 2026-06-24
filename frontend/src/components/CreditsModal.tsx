import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { X } from 'lucide-react';
import { fetchTransactions } from '../api';

interface Tx { id: number; amount: number; status: string; created_at: string; }

interface Props {
  isOpen: boolean;
  onClose: () => void;
  balance: number;
  onBuyNitro: () => void;
}

export const CreditsModal = ({ isOpen, onClose, balance, onBuyNitro }: Props) => {
  const { t, i18n } = useTranslation();
  const isRTL = i18n.language === 'fa';
  const [txs, setTxs] = useState<Tx[]>([]);

  useEffect(() => {
    if (isOpen) fetchTransactions().then(setTxs);
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
            <img src="/Logo/Nitro.png" alt="Nitro" className="w-6 h-6 object-contain" />
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
            <p className="text-4xl font-title text-gold">{balance.toLocaleString()}</p>
            <p className="text-xs font-light-ui text-textSecondary mt-1">{t('Nitro Credits')}</p>
          </div>

          {/* Transactions */}
          <div>
            <p className="text-sm font-ui text-textSecondary mb-2">{t('Recent Transactions')}</p>
            {txs.length === 0 ? (
              <p className="text-center font-light-ui text-sm text-textSecondary py-3">
                {t('No transactions yet')}
              </p>
            ) : (
              <div className="space-y-1.5 max-h-44 overflow-y-auto hide-scrollbar">
                {txs.slice(0, 10).map(tx => (
                  <div key={tx.id} className="flex justify-between items-center bg-background rounded-xl px-4 py-2">
                    <span className="font-light-ui text-xs text-textSecondary">
                      {new Date(tx.created_at).toLocaleDateString(isRTL ? 'fa-IR' : 'en-US')}
                    </span>
                    <span className={`font-ui text-sm ${tx.amount >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                      {tx.amount >= 0 ? '+' : ''}{tx.amount}
                    </span>
                    <span className={`font-light-ui text-xs ${tx.status === 'approved' ? 'text-emerald-400' : 'text-amber-400'}`}>
                      {tx.status}
                    </span>
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
            <img src="/Logo/Nitro.png" alt="" className="w-5 h-5 object-contain" />
            <span>{t('Refill Nitro')}</span>
          </button>
        </div>
      </div>
    </div>
  );
};
