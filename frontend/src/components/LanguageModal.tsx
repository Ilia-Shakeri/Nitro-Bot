import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Check } from 'lucide-react';
import { updateLanguage } from '../api';
import { useUser } from '../context/UserContext';
import {
  LANGUAGE_OPTIONS,
  hasSavedLanguageChoice,
  isSupportedLanguage,
  markLanguageChoiceSaved,
  type LanguageCode,
} from '../utils/languages';

export const LanguageModal = () => {
  const { t, i18n } = useTranslation();
  const { user, loading, refreshUser } = useUser();
  const [selected, setSelected] = useState<LanguageCode | ''>('');
  const [dismissed, setDismissed] = useState(false);

  const preferred = isSupportedLanguage(user?.language_preference) ? user.language_preference : 'en';
  const currentSelection = selected || preferred;
  const visible = !loading && !dismissed && !hasSavedLanguageChoice();

  if (!visible) return null;

  const persistLanguage = (code: LanguageCode) => {
    void updateLanguage(code)
      .then(() => refreshUser())
      .catch(() => undefined);
  };

  const chooseLanguage = async (code: LanguageCode) => {
    setSelected(code);
    await i18n.changeLanguage(code);
    markLanguageChoiceSaved();
    setDismissed(true);
    persistLanguage(code);
  };

  return (
    <div className="fixed inset-0 z-[80] flex items-center justify-center bg-black/75 backdrop-blur-md px-4">
      <div className="w-full max-w-sm bg-card1 border border-gold/20 rounded-2xl p-5 shadow-2xl" dir="ltr">
        <h2 className="font-title text-2xl text-textPrimary mb-2">{t('Choose Language')}</h2>
        <p className="text-sm text-textSecondary mb-5">{t('Choose your language to continue.')}</p>

        <div className="grid grid-cols-1 gap-2 mb-5">
          {LANGUAGE_OPTIONS.map(option => {
            const active = currentSelection === option.code;
            return (
              <button
                key={option.code}
                type="button"
                onClick={() => chooseLanguage(option.code)}
                className={`flex items-center justify-between rounded-xl border px-4 py-3 transition ${
                  active ? 'border-gold bg-gold/10 text-textPrimary' : 'border-card3 bg-background text-textSecondary'
                }`}
              >
                <span className="font-ui text-sm">{option.flag} {option.label}</span>
                {active && <Check className="w-4 h-4 text-gold" />}
              </button>
            );
          })}
        </div>

        <button
          type="button"
          onClick={() => chooseLanguage(currentSelection)}
          className="w-full bg-gold text-background rounded-xl py-3 font-ui text-sm disabled:opacity-60"
        >
          {t('Save Language')}
        </button>
      </div>
    </div>
  );
};
