import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { X, Moon, Sun, LifeBuoy, TrendingUp, TrendingDown } from 'lucide-react';
import { useTheme } from '../context/ThemeContext';
import WebApp from '@twa-dev/sdk';
import { getTransactions, getReleases } from '../api';
import type { Transaction, Release } from '../types/api';

interface Props { isOpen: boolean; onClose: () => void; }

export const ProfileModal = ({ isOpen, onClose }: Props) => {
  const { t, i18n } = useTranslation();
  const { theme, toggle } = useTheme();
  const isRTL = i18n.language === 'fa';
  const user = WebApp.initDataUnsafe?.user;
  const name = user ? [user.first_name, user.last_name].filter(Boolean).join(' ') : 'User';
  const handle = user?.username ? `@${user.username}` : `ID: ${user?.id ?? '---'}`;

  const [tab, setTab] = useState<'settings' | 'transactions'>('settings');
  const [txs, setTxs] = useState<Transaction[]>([]);
  const [releases, setReleases] = useState<Release[]>([]);

  const openSupport = () => {
    try { WebApp.openTelegramLink('https://t.me/nitrobot_support'); } catch { /* noop */ }
  };

  useEffect(() => {
    if (isOpen && tab === 'transactions') {
      getTransactions().then(setTxs);
      getReleases().then(setReleases);
    }
  }, [isOpen, tab]);

  if (!isOpen) return null;

  const fmtDate = (iso: string) =>
    new Date(iso).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });

  const statusLabel = (s: string) =>
    s === 'approved' ? 'تایید شده' : s === 'pending' ? 'در انتظار' : s === 'rejected' ? 'رد شده' : s;

  const statusColor = (s: string) =>
    s === 'approved' ? 'text-emerald-400' : s === 'pending' ? 'text-amber-400' : 'text-rose-400';

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

        {/* Close */}
        <div className="flex justify-end px-5 py-2">
          <button onClick={onClose} className="text-textSecondary hover:text-textPrimary transition p-1">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Avatar + name */}
        <div className="flex flex-col items-center px-6 mb-4">
          <div className="w-20 h-20 rounded-full border-2 border-gold shadow-[0_0_20px_rgba(212,175,55,0.3)] mb-3 overflow-hidden bg-gradient-to-br from-card3 to-card2 flex items-center justify-center">
            {user?.photo_url
              ? <img src={user.photo_url} alt={name} className="w-full h-full object-cover" />
              : <span className="text-3xl font-title text-gold">{name[0]?.toUpperCase()}</span>
            }
          </div>
          <h3 className="font-title text-xl text-textPrimary mb-1">{name}</h3>
          <p className="font-light-ui text-sm text-textSecondary">{handle}</p>
        </div>

        {/* Tabs */}
        <div className="flex mb-4 gap-2 p-1 bg-background rounded-2xl mx-5">
          <button
            onClick={() => setTab('settings')}
            className={`flex-1 py-2 rounded-xl text-sm font-ui transition-all duration-200 ${
              tab === 'settings' ? 'bg-gold text-background shadow-md' : 'text-textSecondary hover:text-textPrimary'
            }`}
          >
            {t('Settings')}
          </button>
          <button
            onClick={() => setTab('transactions')}
            className={`flex-1 py-2 rounded-xl text-sm font-ui transition-all duration-200 ${
              tab === 'transactions' ? 'bg-gold text-background shadow-md' : 'text-textSecondary hover:text-textPrimary'
            }`}
          >
            تراکنش‌ها
          </button>
        </div>

        {/* Settings tab */}
        {tab === 'settings' && (
          <div className="px-5 space-y-2">
            <button
              onClick={toggle}
              className="w-full flex items-center justify-between bg-background rounded-2xl px-4 py-3 hover:bg-card3/30 transition"
            >
              <div className="flex items-center gap-3">
                {theme === 'dark'
                  ? <Moon className="w-5 h-5 text-gold" />
                  : <Sun  className="w-5 h-5 text-gold" />
                }
                <span className="font-ui text-sm text-textPrimary">
                  {theme === 'dark' ? t('Switch to Light Mode') : t('Switch to Dark Mode')}
                </span>
              </div>
              <div className={`relative w-11 h-6 rounded-full transition-colors duration-300 ${theme === 'light' ? 'bg-gold' : 'bg-card3'}`}>
                <div className={`absolute top-1 w-4 h-4 rounded-full bg-white shadow transition-all duration-300 ${theme === 'light' ? 'right-1' : 'left-1'}`} />
              </div>
            </button>

            <button
              onClick={openSupport}
              className="w-full flex items-center gap-3 bg-background rounded-2xl px-4 py-3 hover:bg-card3/30 transition"
            >
              <LifeBuoy className="w-5 h-5 text-gold" />
              <span className="font-ui text-sm text-textPrimary">{t('Contact Support')}</span>
            </button>
          </div>
        )}

        {/* Transactions tab */}
        {tab === 'transactions' && (
          <div className="px-5 space-y-4 max-h-64 overflow-y-auto hide-scrollbar" dir="rtl">

            {/* Charge top-ups */}
            <div>
              <p className="text-xs font-ui text-gold/70 mb-2 px-1">شارژ حساب</p>
              {txs.length === 0 ? (
                <p className="text-center text-xs font-light-ui text-textSecondary py-3 bg-background rounded-xl">
                  هنوز شارژی ثبت نشده
                </p>
              ) : (
                <div className="space-y-1.5">
                  {txs.map(tx => (
                    <div key={tx.id} className="flex items-center gap-3 bg-background rounded-xl px-4 py-2.5">
                      <TrendingUp className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-ui text-textPrimary">
                          +{tx.amount.toLocaleString()} نیترو
                        </p>
                        <p className="text-xs font-light-ui text-textSecondary">
                          {fmtDate(tx.created_at)}
                          {' · '}
                          {tx.payment_method === 'tether' ? 'تتر' : 'کارت بانکی'}
                        </p>
                      </div>
                      <span className={`text-xs font-ui flex-shrink-0 ${statusColor(tx.status)}`}>
                        {statusLabel(tx.status)}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Nitro usage (releases) */}
            <div>
              <p className="text-xs font-ui text-gold/70 mb-2 px-1">مصرف نیترو</p>
              {releases.length === 0 ? (
                <p className="text-center text-xs font-light-ui text-textSecondary py-3 bg-background rounded-xl">
                  هنوز نیتروی استفاده نشده
                </p>
              ) : (
                <div className="space-y-1.5">
                  {releases.map(rel => (
                    <div key={rel.id} className="flex items-center gap-3 bg-background rounded-xl px-4 py-2.5">
                      <TrendingDown className="w-4 h-4 text-rose-400 flex-shrink-0" />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-ui text-textPrimary truncate">
                          {rel.song_name} – {rel.artist_name}
                        </p>
                        <p className="text-xs font-light-ui text-textSecondary">
                          {fmtDate(rel.created_at)}
                          {rel.genre ? ` · ${rel.genre}` : ''}
                        </p>
                      </div>
                      <span className={`text-xs font-ui flex-shrink-0 ${statusColor(rel.status)}`}>
                        {statusLabel(rel.status)}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>

          </div>
        )}
      </div>
    </div>
  );
};
