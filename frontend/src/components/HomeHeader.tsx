
import { useTranslation } from 'react-i18next';

export const HomeHeader = ({ credits, onLangToggle, lang }: { credits: number, onLangToggle: () => void, lang: string }) => {
  const { t } = useTranslation();
  return (
    <div className="flex justify-between items-center py-4 px-4 w-full relative z-10">
      <div className="flex items-center space-x-2 bg-black/40 border border-gold/30 rounded-full px-3 py-1">
        <div className="w-4 h-4 bg-gold rounded-full shadow-[0_0_8px_#D4AF37]"></div>
        <span className="text-white font-semibold text-sm mr-2">{credits.toLocaleString()} {t('Credits')}</span>
      </div>
      <div className="flex items-center space-x-3">
        <button onClick={onLangToggle} className="text-xs bg-card1 border border-card3 text-textPrimary px-2 py-1 rounded">
          {lang.toUpperCase()}
        </button>
        <div className="w-10 h-10 rounded-full bg-gradient-to-br from-gray-600 to-gray-800 flex items-center justify-center border border-gray-500 shadow-md">
          <span className="text-white font-bold">G</span>
        </div>
      </div>
    </div>
  );
};
