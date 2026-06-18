import { useState, useEffect } from "react";
import { HomeHeader } from '../components/HomeHeader';
import { HorizontalMusicSlider } from '../components/HorizontalMusicSlider';
import { UploadArtBox } from '../components/UploadArtBox';
import { NitroCreditCard } from '../components/NitroCreditCard';
import { PaymentModal } from '../components/PaymentModal';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { fetchUser, updateLanguage } from '../api';

export const HomePage = () => {
  const [lang, setLang] = useState('fa');
  const [credits, setCredits] = useState(0);
  const [isPaymentOpen, setIsPaymentOpen] = useState(false);
  
  const navigate = useNavigate();
  const { i18n } = useTranslation();

  useEffect(() => {
    fetchUser()
      .then(user => {
        setCredits(user.credits);
        if (user.language_preference) {
          setLang(user.language_preference);
          i18n.changeLanguage(user.language_preference);
        }
      })
      .catch(console.error);
  }, [i18n]);

  const toggleLang = async () => {
    const newLang = lang === 'en' ? 'fa' : 'en';
    setLang(newLang);
    i18n.changeLanguage(newLang);
    try {
      await updateLanguage(newLang);
    } catch (e) {
      console.error(e);
    }
  };

  const handleUploadClick = () => {
    navigate('/upload');
  };

  return (
    <div className="min-h-screen bg-background max-w-md mx-auto relative overflow-hidden flex flex-col font-sans" dir={lang === 'fa' ? 'rtl' : 'ltr'}>
      <div className="absolute top-0 right-0 w-64 h-64 bg-card3/20 blur-[100px] rounded-full pointer-events-none"></div>

      <HomeHeader credits={credits} onLangToggle={toggleLang} lang={lang} />

      <div className="flex-1 overflow-y-auto pb-4 pt-2">
        <HorizontalMusicSlider />
        <UploadArtBox onClick={handleUploadClick} />
        <NitroCreditCard balance={credits} onRefillClick={() => setIsPaymentOpen(true)} />
      </div>

      <PaymentModal isOpen={isPaymentOpen} onClose={() => setIsPaymentOpen(false)} />
    </div>
  );
};