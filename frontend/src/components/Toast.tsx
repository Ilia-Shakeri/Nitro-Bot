import { X } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { useToast } from '../context/ToastContext';
import { isRtlLanguage } from '../i18n';

const isPersian = (text: string) => /[؀-ۿ]/.test(text);

export const ToastContainer = () => {
  const { toasts, dismiss } = useToast();
  const { i18n } = useTranslation();
  const isRTL = isRtlLanguage(i18n.language);

  return (
    <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-[100] flex flex-col gap-2 w-[calc(100%-2rem)] max-w-sm pointer-events-none">
      {toasts.map(t => {
        const msgRTL = isPersian(t.message) || isRTL;
        return (
          <div
            key={t.id}
            dir={msgRTL ? 'rtl' : 'ltr'}
            className={[
              'flex items-center justify-between px-4 py-3 rounded-xl shadow-lg text-sm font-ui animate-toast-in pointer-events-auto',
              t.type === 'success' && 'bg-emerald-800 text-emerald-100',
              t.type === 'error'   && 'bg-red-900 text-red-100',
              t.type === 'info'    && 'bg-card1 text-textPrimary border border-card3',
            ].filter(Boolean).join(' ')}
          >
            <span>{t.message}</span>
            <button
              onClick={() => dismiss(t.id)}
              className={`${msgRTL ? 'mr-3' : 'ml-3'} opacity-70 hover:opacity-100 flex-shrink-0`}
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        );
      })}
    </div>
  );
};
