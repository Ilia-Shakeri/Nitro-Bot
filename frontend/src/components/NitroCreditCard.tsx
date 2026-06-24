
import { useTranslation } from 'react-i18next';
import { Zap, ChevronRight } from 'lucide-react';

export const NitroCreditCard = ({ balance, onRefillClick }: { balance: number, onRefillClick?: () => void }) => {
  const { t, i18n } = useTranslation();
  const isRTL = i18n.language === 'fa';

  return (
    <div className="px-4 pb-8">
      <div className="bg-gradient-to-br from-[#1c1810] to-card1 rounded-2xl p-5 border border-gold/20 shadow-lg relative overflow-hidden">
        {/* Subtle glow / orbits effect */}
        <div className="absolute top-1/2 left-12 w-48 h-48 border border-gold/10 rounded-full -translate-y-1/2 -translate-x-1/2"></div>
        <div className="absolute top-1/2 left-12 w-32 h-32 border border-gold/5 rounded-full -translate-y-1/2 -translate-x-1/2"></div>

        <div className="flex items-center mb-6 relative z-10 gap-5">
          <div className="w-20 h-20 rounded-full border-4 border-gold/20 flex items-center justify-center flex-shrink-0">
            <div className="w-16 h-16 rounded-full border-4 border-gold flex items-center justify-center shadow-[0_0_15px_#D4AF37]">
              <Zap fill="#D4AF37" className="text-gold w-8 h-8" strokeWidth={0} />
            </div>
          </div>

          <div className="flex-1">
            <h2 className="text-3xl font-title text-gold mb-1">{t('Nitro')}</h2>
            <p className="text-sm font-ui text-textSecondary mb-3 leading-relaxed">
              {t('Refill your credits and keep creating music.')}
            </p>
            <div className="inline-flex items-center gap-2 bg-black/40 border border-gold/20 rounded-full px-3 py-1">
              <div className="w-3 h-3 bg-gold rounded-full shadow-[0_0_5px_#D4AF37] flex-shrink-0"></div>
              <span className="text-xs font-ui">{t('Balance', { balance })}</span>
            </div>
          </div>
        </div>

        <button
          onClick={onRefillClick}
          className="w-full bg-gradient-to-r from-gold to-[#B8860B] text-background font-title py-3 px-5 rounded-xl flex justify-center items-center gap-2 shadow-md hover:opacity-90 transition-opacity"
        >
          <span>{t('Refill Nitro')}</span>
          <ChevronRight className={`w-5 h-5 text-background ${isRTL ? 'rotate-180' : ''}`} />
        </button>
      </div>
    </div>
  );
};
