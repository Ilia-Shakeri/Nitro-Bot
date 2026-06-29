import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useLocation, useNavigate } from 'react-router-dom';
import { ArrowRight, ArrowLeft } from 'lucide-react';
import WebApp from '@twa-dev/sdk';
import { ProfileModal } from './ProfileModal';
import { CreditsModal } from './CreditsModal';

interface Props {
  credits: number;
  onLangToggle: () => void;
  lang: string;
  onBuyNitro?: () => void;
}

export const HomeHeader = ({ credits, onLangToggle, lang, onBuyNitro }: Props) => {
  const { t } = useTranslation();
  const location = useLocation();
  const navigate = useNavigate();
  const [profileOpen, setProfileOpen] = useState(false);
  const [creditsOpen, setCreditsOpen] = useState(false);

  const isHome = location.pathname === '/';
  const isRTL  = lang === 'fa';
  const user    = WebApp.initDataUnsafe?.user;
  const initial = user?.first_name?.[0]?.toUpperCase() ?? 'N';

  return (
    <>
      <div className="flex justify-between items-center py-4 px-4 w-full relative z-10">

        {/* Left: back button (sub-pages) or credits badge (home) */}
        <div className="flex items-center gap-2">
          {!isHome ? (
            <button
              onClick={() => navigate(-1)}
              className="w-9 h-9 flex items-center justify-center rounded-full bg-card1 border border-card3 hover:bg-card3/50 transition"
            >
              {isRTL
                ? <ArrowRight className="w-4 h-4 text-textPrimary" />
                : <ArrowLeft  className="w-4 h-4 text-textPrimary" />
              }
            </button>
          ) : (
            <button
              onClick={() => setCreditsOpen(true)}
              className="flex items-center gap-2 bg-card3/30 border border-gold/30 rounded-full px-3 py-1.5 hover:bg-gold/10 transition"
            >
              <img src="/Logo/Nitro.png" alt="Nitro" className="w-6 h-6 object-contain select-none pointer-events-none flex-shrink-0" />
              <span className="text-textPrimary font-ui text-sm">
                {credits.toLocaleString()} {t('Credits')}
              </span>
            </button>
          )}
        </div>

        {/* Right: language toggle + avatar */}
        <div className="flex items-center gap-3">
          <button
            onClick={onLangToggle}
            className="text-xs bg-card1 border border-card3 text-textPrimary px-3 py-1.5 rounded-lg font-ui hover:bg-card3/50 transition-all duration-200 active:scale-95"
          >
            {isRTL ? 'EN' : 'FA'}
          </button>

          <button
            onClick={() => setProfileOpen(true)}
            className="w-10 h-10 rounded-full border border-gold/30 shadow-md hover:border-gold/70 hover:shadow-[0_0_12px_rgba(212,175,55,0.3)] transition overflow-hidden bg-gradient-to-br from-card3 to-card2 flex items-center justify-center"
          >
            {user?.photo_url
              ? <img src={user.photo_url} alt={user.first_name} className="w-full h-full object-cover" />
              : <span className="text-textPrimary font-title">{initial}</span>
            }
          </button>
        </div>
      </div>

      <ProfileModal isOpen={profileOpen} onClose={() => setProfileOpen(false)} />
      <CreditsModal
        isOpen={creditsOpen}
        onClose={() => setCreditsOpen(false)}
        balance={credits}
        onBuyNitro={onBuyNitro ?? (() => {})}
      />
    </>
  );
};
