
import { useTranslation } from 'react-i18next';

export const HorizontalMusicSlider = () => {
  const { t } = useTranslation();

  const tracks = [
    { title: "Midnight Freq...", artist: "Arman Vale", listens: "18.4k", color: "bg-[#1E3C5A]" },
    { title: "Golden Static", artist: "NOVA District", listens: "16.3k", color: "bg-[#D4AF37]" },
    { title: "Blue Room Echo", artist: "Liora", listens: "14.1k", color: "bg-[#0B1D33]" }
  ];

  return (
    <div className="w-full px-4 mb-8">
      <div className="flex items-center space-x-2 mb-1">
        <h2 className="text-2xl font-bold">{t('My Music')}</h2>
        <span className="text-gold text-2xl">{'>'}</span>
      </div>
      <p className="text-textSecondary text-sm mb-4">{t('Ordered by your most listened tracks')}</p>

      <div className="flex space-x-4 overflow-x-auto pb-4 hide-scrollbar">
        {tracks.map((track, i) => (
          <div key={i} className="flex-shrink-0 w-32">
            <div className={`w-32 h-32 rounded-xl mb-2 relative overflow-hidden ${track.color}`}>
              {/* Abstract shapes matching design somewhat */}
              <div className="absolute -bottom-4 -left-4 w-20 h-20 bg-black/40 rounded-full"></div>
              <div className="absolute -top-4 -right-4 w-20 h-20 bg-black/40 rounded-full"></div>
              {track.color === 'bg-[#D4AF37]' && (
                  <div className="absolute inset-0 flex items-center justify-center">
                      <div className="w-full h-0.5 bg-black/20 my-2 rotate-12"></div>
                      <div className="w-full h-0.5 bg-black/20 my-2 -rotate-12"></div>
                  </div>
              )}
              <div className="absolute top-2 left-2 bg-black/60 px-2 py-0.5 rounded-full text-xs font-semibold">
                {track.listens}
              </div>
            </div>
            <h3 className="text-sm font-semibold truncate text-right rtl:text-right ltr:text-left">{track.title}</h3>
            <p className="text-xs text-textSecondary truncate text-right rtl:text-right ltr:text-left">{track.artist}</p>
          </div>
        ))}
      </div>
    </div>
  );
};
