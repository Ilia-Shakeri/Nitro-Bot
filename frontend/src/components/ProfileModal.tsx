import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { FileText, Gift, Globe2, LifeBuoy, Moon, Sun, TrendingDown, TrendingUp, UserRound, X } from 'lucide-react';
import WebApp from '@twa-dev/sdk';
import { getLedger, getTickets, updateLanguage } from '../api';
import { useTheme } from '../context/ThemeContext';
import { useUser } from '../context/UserContext';
import type { LedgerEntry, SupportTicket } from '../types/api';
import { CopyField } from './CopyField';
import { LANGUAGE_OPTIONS, languageLabel } from '../utils/languages';
import { isRtlLanguage } from '../i18n';

interface Props { isOpen: boolean; onClose: () => void; }

export const ProfileModal = ({ isOpen, onClose }: Props) => {
  const { t, i18n } = useTranslation();
  const { theme, toggle } = useTheme();
  const { user: apiUser, refreshUser } = useUser();
  const navigate = useNavigate();
  const isRTL = isRtlLanguage(i18n.language);
  const user = WebApp.initDataUnsafe?.user;
  const name = user ? [user.first_name, user.last_name].filter(Boolean).join(' ') : 'User';
  const telegramId = apiUser?.telegram_id ?? user?.id;
  const handle = user?.username ? `@${user.username}` : `ID: ${telegramId ?? '---'}`;
  const botUsername = String(import.meta.env.VITE_BOT_USERNAME || 'NitroBot').replace(/^@/, '');
  const referralLink = telegramId ? `https://t.me/${botUsername}?start=ref_${telegramId}` : '';

  const [tab, setTab] = useState<'settings' | 'referrals' | 'transactions' | 'tickets'>('settings');
  const [ledger, setLedger] = useState<LedgerEntry[]>([]);
  const [tickets, setTickets] = useState<SupportTicket[]>([]);

  useEffect(() => {
    if (isOpen && tab === 'transactions') getLedger().then(setLedger);
    if (isOpen && tab === 'tickets') getTickets().then(setTickets);
  }, [isOpen, tab]);

  if (!isOpen) return null;

  const dateLocale = i18n.language.startsWith('ar') ? 'ar-SA' : isRTL ? 'fa-IR' : 'en-US';
  const fmtDate = (iso: string) =>
    new Date(iso).toLocaleDateString(dateLocale, { year: 'numeric', month: 'short', day: 'numeric' });

  const openSupport = () => {
    onClose();
    navigate('/support');
  };

  const openPolicy = () => {
    onClose();
    navigate('/policy');
  };

  const tabClass = (active: boolean) =>
    `py-2 rounded-xl text-xs font-ui transition-all duration-200 ${
      active ? 'bg-gold text-background shadow-md' : 'text-textSecondary hover:text-textPrimary'
    }`;

  const changeLanguage = async (code: string) => {
    await i18n.changeLanguage(code);
    void updateLanguage(code)
      .then(() => refreshUser())
      .catch(() => undefined);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/60 backdrop-blur-sm" onClick={onClose}>
      <div
        className="bg-card1/85 backdrop-blur-xl w-full max-w-md max-h-[90vh] overflow-y-auto rounded-t-3xl pb-10 border-t border-gold/20 shadow-2xl"
        dir={isRTL ? 'rtl' : 'ltr'}
        onClick={e => e.stopPropagation()}
      >
        <div className="flex justify-center pt-3 pb-1">
          <div className="w-10 h-1 rounded-full bg-card3/60" />
        </div>

        <div className="flex justify-end px-5 py-2">
          <button onClick={onClose} className="text-textSecondary hover:text-textPrimary transition p-1">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="flex flex-col items-center px-6 mb-4">
          <div className="w-20 h-20 rounded-full border-2 border-gold shadow-[0_0_20px_rgba(212,175,55,0.3)] mb-3 overflow-hidden bg-gradient-to-br from-card3 to-card2 flex items-center justify-center">
            {user?.photo_url
              ? <img src={user.photo_url} alt={name} className="w-full h-full object-cover" />
              : <UserRound className="w-9 h-9 text-gold" />
            }
          </div>
          <h3 className="font-title text-xl text-textPrimary mb-1">{name}</h3>
          <p className="font-light-ui text-sm text-textSecondary">{handle}</p>
        </div>

        <div className="grid grid-cols-2 mb-4 gap-2 p-1 bg-background rounded-2xl mx-5">
          <button onClick={() => setTab('settings')} className={tabClass(tab === 'settings')}>{t('Settings')}</button>
          <button onClick={() => setTab('referrals')} className={tabClass(tab === 'referrals')}>{t('Referrals')}</button>
          <button onClick={() => setTab('transactions')} className={tabClass(tab === 'transactions')}>{t('Recent Transactions')}</button>
          <button onClick={() => setTab('tickets')} className={tabClass(tab === 'tickets')}>{t('Tickets')}</button>
        </div>

        {tab === 'settings' && (
          <div className="px-5 space-y-2">
            <button
              onClick={toggle}
              className="w-full flex items-center justify-between bg-background rounded-2xl px-4 py-3 hover:bg-card3/30 transition"
            >
              <div className="flex items-center gap-3">
                {theme === 'dark'
                  ? <Moon className="w-5 h-5 text-gold" />
                  : <Sun className="w-5 h-5 text-gold" />
                }
                <span className="font-ui text-sm text-textPrimary">
                  {theme === 'dark' ? t('Switch to Light Mode') : t('Switch to Dark Mode')}
                </span>
              </div>
              <div className={`relative w-11 h-6 rounded-full transition-colors duration-300 ${theme === 'light' ? 'bg-gold' : 'bg-card3'}`}>
                <div className={`absolute top-1 w-4 h-4 rounded-full bg-white shadow transition-all duration-300 ${theme === 'light' ? 'right-1' : 'left-1'}`} />
              </div>
            </button>

            <div className="bg-background rounded-2xl px-4 py-3">
              <div className="flex items-center gap-3 mb-3">
                <Globe2 className="w-5 h-5 text-gold" />
                <span className="font-ui text-sm text-textPrimary">{t('Language')}</span>
              </div>
              <div className="grid grid-cols-2 gap-2">
                {LANGUAGE_OPTIONS.map(option => {
                  const active = i18n.language.split('-')[0] === option.code;
                  return (
                    <button
                      key={option.code}
                      type="button"
                      onClick={() => changeLanguage(option.code)}
                      className={`rounded-xl border px-3 py-2 text-xs font-ui transition ${
                        active ? 'border-gold bg-gold/10 text-textPrimary' : 'border-card3 text-textSecondary'
                      }`}
                    >
                      {languageLabel(option.code)}
                    </button>
                  );
                })}
              </div>
            </div>

            <button
              onClick={openSupport}
              className="w-full flex items-center gap-3 bg-background rounded-2xl px-4 py-3 hover:bg-card3/30 transition"
            >
              <LifeBuoy className="w-5 h-5 text-gold" />
              <span className="font-ui text-sm text-textPrimary">{t('Contact Support')}</span>
            </button>

            <button
              onClick={openPolicy}
              className="w-full flex items-center gap-3 bg-background rounded-2xl px-4 py-3 hover:bg-card3/30 transition"
            >
              <FileText className="w-5 h-5 text-gold" />
              <span className="font-ui text-sm text-textPrimary">{t('Terms and Conditions')}</span>
            </button>
          </div>
        )}

        {tab === 'referrals' && (
          <div className="px-5 space-y-3">
            <div className="flex items-center gap-3 bg-background rounded-2xl px-4 py-3">
              <Gift className="w-5 h-5 text-gold flex-shrink-0" />
              <div>
                <p className="text-xs text-textSecondary">{t('Referral Points')}</p>
                <p className="text-xl font-title text-textPrimary">{apiUser?.referral_points ?? 0}</p>
              </div>
            </div>

            {referralLink && (
              <CopyField label={t('Referral Link')} value={referralLink} display={referralLink} />
            )}

            <p className="bg-background rounded-2xl px-4 py-3 text-xs leading-relaxed text-textSecondary">
              {t('Share your referral link with new users. When a new user starts Nitro Bot through your link, your account earns referral points after the referral is recorded. Points may be reviewed for eligibility before rewards are issued.')}
            </p>
          </div>
        )}

        {tab === 'transactions' && (
          <div className="px-5 space-y-2">
            {ledger.length === 0 ? (
              <p className="text-center text-xs font-light-ui text-textSecondary py-3 bg-background rounded-xl">
                {t('No transactions yet')}
              </p>
            ) : ledger.map(item => (
              <div key={item.id} className="flex items-center gap-3 bg-background rounded-xl px-4 py-2.5">
                {item.direction === 'credit'
                  ? <TrendingUp className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                  : <TrendingDown className="w-4 h-4 text-rose-400 flex-shrink-0" />
                }
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-ui text-textPrimary truncate">{item.title}</p>
                  <p className="text-xs font-light-ui text-textSecondary">{fmtDate(item.created_at)} · {t(item.status)}</p>
                </div>
                <span className={`text-sm font-ui flex-shrink-0 ${item.direction === 'credit' ? 'text-emerald-400' : 'text-rose-400'}`}>
                  {item.direction === 'credit' ? '+' : '-'}{item.amount}
                </span>
              </div>
            ))}
          </div>
        )}

        {tab === 'tickets' && (
          <div className="px-5 space-y-3">
            <button
              onClick={openSupport}
              className="w-full flex items-center justify-center gap-2 bg-gold text-background rounded-xl px-4 py-2.5 font-ui text-sm hover:opacity-90 active:scale-[0.98] transition-all duration-300"
            >
              <LifeBuoy className="w-4 h-4" />
              {t('New Ticket')}
            </button>
            {tickets.length === 0 ? (
              <p className="text-center text-xs font-light-ui text-textSecondary py-3 bg-background rounded-xl">
                {t('No tickets yet')}
              </p>
            ) : tickets.map(ticket => (
              <div key={ticket.id} className="bg-background rounded-xl p-3 space-y-2">
                <div className="flex items-center justify-between gap-3">
                  <p className="text-sm font-ui text-textPrimary truncate">{ticket.subject || `#${ticket.id}`}</p>
                  <span className="text-xs text-gold flex-shrink-0">{t(ticket.status)}</span>
                </div>
                {ticket.messages.map(msg => (
                  <div
                    key={msg.id}
                    className={`rounded-lg p-2 ${msg.sender === 'admin' ? 'bg-gold/10 border border-gold/20' : 'bg-card2/70'}`}
                  >
                    <p className="text-[11px] text-textSecondary mb-1">
                      {msg.sender === 'admin' ? t('Support Team') : t('You')} · {fmtDate(msg.created_at)}
                    </p>
                    <p className="text-sm text-textPrimary leading-relaxed whitespace-pre-wrap">{msg.message}</p>
                  </div>
                ))}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
