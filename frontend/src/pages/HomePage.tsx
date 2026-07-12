import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { HomeHeader } from '../components/HomeHeader';
import { HorizontalMusicSlider } from '../components/HorizontalMusicSlider';
import { UploadArtBox } from '../components/UploadArtBox';
import { NitroCreditCard } from '../components/NitroCreditCard';
import { PaymentModal } from '../components/PaymentModal';
import { useUser } from '../context/UserContext';
import { isRtlLanguage } from '../i18n';

export const HomePage = () => {
  const { user } = useUser();
  const credits = user?.credits ?? 0;

  const [isPaymentOpen, setIsPaymentOpen] = useState(false);

  const navigate = useNavigate();
  const { i18n } = useTranslation();
  const lang = i18n.language;

  return (
    <div
      className="min-h-[var(--tg-viewport-stable-height,100vh)] bg-background max-w-md mx-auto relative overflow-hidden flex flex-col"
      dir={isRtlLanguage(lang) ? 'rtl' : 'ltr'}
    >
      <div className="absolute top-0 right-0 w-64 h-64 bg-card3/20 blur-[100px] rounded-full pointer-events-none" />

      <HomeHeader
        credits={credits}
        lang={lang}
        onBuyNitro={() => setIsPaymentOpen(true)}
      />

      <div
        className="flex-1 overflow-y-auto pb-4 pt-2"
      >
        <HorizontalMusicSlider />
        <UploadArtBox onClick={() => navigate('/upload')} />
        <NitroCreditCard balance={credits} onRefillClick={() => setIsPaymentOpen(true)} />
      </div>

      <PaymentModal isOpen={isPaymentOpen} onClose={() => setIsPaymentOpen(false)} />
    </div>
  );
};
