
import { useTranslation } from 'react-i18next';
import { Plus } from 'lucide-react';

export const UploadArtBox = ({ onClick }: { onClick?: () => void }) => {
  const { t } = useTranslation();
  return (
    <div className="px-4 mb-8">
      <div
        onClick={onClick}
        className="w-full h-48 border border-dashed border-card3 bg-card2 rounded-2xl flex flex-col items-center justify-center cursor-pointer transition-colors hover:bg-card3/30"
      >
        <div className="w-16 h-16 rounded-full border-2 border-gold flex items-center justify-center mb-4">
          <Plus className="text-gold w-8 h-8" strokeWidth={1.5} />
        </div>
        <h3 className="font-bold text-lg mb-1">{t('Drop Your Art')}</h3>
        <p className="text-sm text-textSecondary">{t('Upload audio, tracks or artwork')}</p>
      </div>
    </div>
  );
};
