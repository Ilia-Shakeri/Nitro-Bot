import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { LifeBuoy, Send } from 'lucide-react';
import { HomeHeader } from '../components/HomeHeader';
import { submitTicket, updateLanguage } from '../api';
import { useToast } from '../context/ToastContext';
import { useUser } from '../context/UserContext';
import { errorText } from '../utils/formMessages';

export const SupportPage = () => {
  const { t, i18n } = useTranslation();
  const lang = i18n.language;
  const { user } = useUser();
  const { toast } = useToast();
  const credits = user?.credits ?? 0;
  const isRTL = lang === 'fa';

  const [subject, setSubject] = useState('');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);

  const handleSend = async () => {
    if (!message.trim()) return;
    setLoading(true);
    try {
      await submitTicket(subject.trim(), message.trim());
      setSent(true);
      toast(t('Ticket sent successfully!'), 'success');
      setSubject('');
      setMessage('');
    } catch (e: unknown) {
      toast(errorText(e, t), 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background max-w-md mx-auto relative overflow-y-auto" dir={isRTL ? 'rtl' : 'ltr'}>
      <HomeHeader
        credits={credits}
        onLangToggle={() => {
          const newLang = lang === 'en' ? 'fa' : 'en';
          i18n.changeLanguage(newLang);
          updateLanguage(newLang).catch(console.error);
        }}
        lang={lang}
      />

      <div className="px-4 py-2">
        <div className="flex items-center gap-3 mb-2">
          <LifeBuoy className="w-7 h-7 text-gold" />
          <h1 className="text-3xl font-title">{t('Support')}</h1>
        </div>
        <p className="text-sm font-ui text-textSecondary mb-8 leading-relaxed">
          {t('support_intro')}
        </p>

        <div className="space-y-4">
          <div>
            <h3 className="text-gold font-ui mb-2 text-sm">{t('Subject (optional)')}</h3>
            <div className="bg-inputBg border border-inputBorder rounded-lg p-3">
              <input
                type="text"
                value={subject}
                onChange={e => setSubject(e.target.value)}
                className="bg-transparent border-none outline-none w-full text-textPrimary font-ui"
                placeholder="Ticket subject..."
              />
            </div>
          </div>

          <div>
            <h3 className="text-gold font-ui mb-2 text-sm">{t('Message *')}</h3>
            <div className="bg-inputBg border border-inputBorder rounded-lg p-3">
              <textarea
                value={message}
                onChange={e => setMessage(e.target.value)}
                rows={6}
                className="bg-transparent border-none outline-none w-full text-textPrimary font-ui resize-none"
                placeholder="Write your message here..."
              />
            </div>
          </div>
        </div>

        <div className="mt-6 pb-8">
          <button
            onClick={handleSend}
            disabled={loading || !message.trim()}
            className="w-full bg-gradient-to-r from-gold to-[#B8860B] text-background font-title py-4 rounded-xl flex justify-center items-center gap-3 shadow-lg hover:opacity-90 disabled:opacity-50 transition-opacity active:scale-[0.98]"
          >
            <Send className="w-5 h-5" />
            <span className="text-lg">{loading ? t('Processing...') : t('Send Ticket')}</span>
          </button>
        </div>

        {sent && (
          <div className="mt-2 p-4 bg-emerald-500/10 border border-emerald-500/30 rounded-xl text-center">
            <p className="text-sm font-ui text-emerald-400">{t('Ticket sent successfully!')}</p>
          </div>
        )}
      </div>
    </div>
  );
};
