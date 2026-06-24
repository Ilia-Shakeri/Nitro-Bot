import { useTranslation } from 'react-i18next';
import { X, Moon, Sun, LifeBuoy } from 'lucide-react';
import { useTheme } from '../context/ThemeContext';
import WebApp from '@twa-dev/sdk';

interface Props { isOpen: boolean; onClose: () => void; }

export const ProfileModal = ({ isOpen, onClose }: Props) => {
  const { t, i18n } = useTranslation();
  const { theme, toggle } = useTheme();
  const isRTL = i18n.language === 'fa';
  const user = WebApp.initDataUnsafe?.user;
  const name = user ? [user.first_name, user.last_name].filter(Boolean).join(' ') : 'User';
  const handle = user?.username ? `@${user.username}` : `ID: ${user?.id ?? '---'}`;

  const openSupport = () => {
    try { WebApp.openTelegramLink('https://t.me/nitrobot_support'); } catch { /* noop */ }
  };

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

        {/* Close */}
        <div className="flex justify-end px-5 py-2">
          <button onClick={onClose} className="text-textSecondary hover:text-textPrimary transition p-1">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Avatar + name */}
        <div className="flex flex-col items-center px-6 mb-6">
          <div className="w-20 h-20 rounded-full border-2 border-gold shadow-[0_0_20px_rgba(212,175,55,0.3)] mb-3 overflow-hidden bg-gradient-to-br from-card3 to-card2 flex items-center justify-center">
            {user?.photo_url
              ? <img src={user.photo_url} alt={name} className="w-full h-full object-cover" />
              : <span className="text-3xl font-title text-gold">{name[0]?.toUpperCase()}</span>
            }
          </div>
          <h3 className="font-title text-xl text-textPrimary mb-1">{name}</h3>
          <p className="font-light-ui text-sm text-textSecondary">{handle}</p>
        </div>

        {/* Actions */}
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
            {/* Toggle pill */}
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
      </div>
    </div>
  );
};
