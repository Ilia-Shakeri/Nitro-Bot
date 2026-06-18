
import { useTranslation } from 'react-i18next';
import { Zap, ChevronRight } from 'lucide-react';

export const NitroCreditCard = ({ balance, onRefillClick }: { balance: number, onRefillClick?: () => void }) => {
  const { t } = useTranslation();
  return (
    <div className="px-4 pb-8">
      <div className="bg-gradient-to-br from-[#1c1810] to-card1 rounded-2xl p-5 border border-gold/20 shadow-lg relative overflow-hidden">
        {/* Subtle glow / orbits effect */}
        <div className="absolute top-1/2 left-12 w-48 h-48 border border-gold/10 rounded-full -translate-y-1/2 -translate-x-1/2"></div>
        <div className="absolute top-1/2 left-12 w-32 h-32 border border-gold/5 rounded-full -translate-y-1/2 -translate-x-1/2"></div>

        <div className="flex justify-between items-center mb-6 relative z-10">
          <div className="w-20 h-20 rounded-full border-4 border-gold/20 flex items-center justify-center">
            <div className="w-16 h-16 rounded-full border-4 border-gold flex items-center justify-center shadow-[0_0_15px_#D4AF37]">
              <Zap fill="#D4AF37" className="text-gold w-8 h-8" strokeWidth={0} />
            </div>
          </div>

          <div className="flex-1 ml-6">
            <h2 className="text-3xl font-bold text-gold mb-1">{t('Nitro')}</h2>
            <p className="text-sm text-textSecondary mb-3">
              {t('Refill your credits and keep creating music.')}
            </p>
            <div className="inline-flex items-center space-x-2 bg-black/40 border border-gold/20 rounded-full px-3 py-1">
              <div className="w-3 h-3 bg-gold rounded-full shadow-[0_0_5px_#D4AF37]"></div>
              <span className="text-xs font-semibold mr-1 ml-1">{t('Balance', { balance })}</span>
            </div>
          </div>
        </div>

        <button
          onClick={onRefillClick}
          className="w-full bg-gradient-to-r from-gold to-[#B8860B] text-background font-bold py-3 px-4 rounded-xl flex justify-center items-center shadow-md hover:opacity-90 transition-opacity"
        >
          <span className="mr-2 ml-2">{t('Refill Nitro')}</span>
          <ChevronRight className="w-5 h-5 text-background" />
        </button>
      </div>
    </div>
  );
};
