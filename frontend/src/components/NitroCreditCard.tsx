import { useTranslation } from 'react-i18next';
import { ChevronRight } from 'lucide-react';

interface Props { balance?: number; onRefillClick?: () => void; }

export const NitroCreditCard = ({ onRefillClick }: Props) => {
  const { t, i18n } = useTranslation();
  const isRTL = i18n.language === 'fa';

  return (
    <div className="px-4 pb-8">
      <div className="bg-gradient-to-br from-cardGold to-card1 rounded-2xl p-5 border border-gold/20 shadow-lg relative overflow-hidden">
        <div className="absolute top-1/2 left-12 w-48 h-48 border border-gold/10 rounded-full -translate-y-1/2 -translate-x-1/2 pointer-events-none" />
        <div className="absolute top-1/2 left-12 w-32 h-32 border border-gold/5  rounded-full -translate-y-1/2 -translate-x-1/2 pointer-events-none" />

        <div className="flex items-center mb-6 relative z-10 gap-5">
          <div className="w-20 h-20 rounded-full border-4 border-gold/20 flex items-center justify-center flex-shrink-0">
            <div className="w-16 h-16 rounded-full border-4 border-gold flex items-center justify-center shadow-[0_0_15px_#D4AF37]">
              <img
                src="/Logo/Nitro.png"
                alt="Nitro"
                className="w-9 h-9 object-contain aspect-square select-none pointer-events-none drop-shadow-[0_0_6px_rgba(212,175,55,0.45)]"
              />
            </div>
          </div>

          <div className="flex-1">
            <h2 className="text-3xl font-title text-gold mb-3">{t('Nitro')}</h2>
            <p className="text-sm font-ui text-textSecondary leading-relaxed">
              {t('Refill your credits and keep creating music.')}
            </p>
          </div>
        </div>

        <button
          onClick={onRefillClick}
          className="w-full bg-gradient-to-r from-gold to-[#B8860B] text-background font-title py-3 px-5 rounded-xl flex justify-center items-center gap-2 shadow-md hover:opacity-90 transition-opacity active:scale-[0.98]"
        >
          <span>{t('Refill Nitro')}</span>
          <ChevronRight className={`w-5 h-5 text-background ${isRTL ? 'rotate-180' : ''}`} />
        </button>
      </div>
    </div>
  );
};
