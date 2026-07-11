import { useTranslation } from 'react-i18next';
import { HomeHeader } from '../components/HomeHeader';
import { useUser } from '../context/UserContext';
import { isRtlLanguage } from '../i18n';

export const PolicyPage = () => {
  const { t, i18n } = useTranslation();
  const { user } = useUser();
  const isRTL = isRtlLanguage(i18n.language);

  return (
    <div className="min-h-screen bg-background max-w-md mx-auto relative overflow-y-auto" dir={isRTL ? 'rtl' : 'ltr'}>
      <HomeHeader credits={user?.credits ?? 0} lang={i18n.language} />

      <main className="px-4 py-4 space-y-5">
        <section className="bg-card1 border border-inputBorder rounded-xl p-4">
          <h1 className="font-title text-2xl text-textPrimary mb-3">{t('Terms and Conditions')}</h1>
          <p className="text-sm text-textSecondary leading-relaxed">{t('Terms placeholder')}</p>
        </section>

        <section className="bg-card1 border border-inputBorder rounded-xl p-4">
          <h2 className="font-title text-2xl text-textPrimary mb-3">{t('Privacy Policy')}</h2>
          <p className="text-sm text-textSecondary leading-relaxed">{t('Privacy placeholder')}</p>
        </section>
      </main>
    </div>
  );
};
