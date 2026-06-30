import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Copy, Check } from 'lucide-react';
import { useToast } from '../context/ToastContext';

interface Props {
  /** Small caption shown above the value (already translated). */
  label: string;
  /** The raw value that gets copied to the clipboard. */
  value: string;
  /** Optional pretty version shown to the user (e.g. spaced card number). */
  display?: string;
  /** Render the value with a monospace, ltr-locked font (good for numbers/addresses). */
  mono?: boolean;
}

/**
 * One-click "copy to clipboard" field.
 * Falls back to a hidden <textarea> + execCommand when the async Clipboard API
 * is unavailable (older Telegram in-app webviews / insecure contexts).
 */
export const CopyField = ({ label, value, display, mono = true }: Props) => {
  const { t } = useTranslation();
  const { toast } = useToast();
  const [copied, setCopied] = useState(false);

  const copy = async () => {
    try {
      if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(value);
      } else {
        const ta = document.createElement('textarea');
        ta.value = value;
        ta.style.position = 'fixed';
        ta.style.opacity = '0';
        document.body.appendChild(ta);
        ta.focus();
        ta.select();
        document.execCommand('copy');
        document.body.removeChild(ta);
      }
      setCopied(true);
      toast(t('Copied to clipboard'), 'success');
      window.setTimeout(() => setCopied(false), 1500);
    } catch {
      toast(t('Copy failed'), 'error');
    }
  };

  return (
    <button
      type="button"
      onClick={copy}
      className="w-full bg-inputBg/80 border border-inputBorder rounded-xl p-3 flex items-center justify-between gap-3 text-left hover:border-gold/50 transition-colors active:scale-[0.99]"
    >
      <span className="min-w-0">
        <span className="block text-[11px] text-textSecondary mb-0.5">{label}</span>
        <span
          dir={mono ? 'ltr' : undefined}
          className={`block text-textPrimary truncate ${mono ? 'font-mono tracking-wide text-sm' : 'text-sm font-semibold'}`}
        >
          {display ?? value}
        </span>
      </span>
      <span className="shrink-0 text-gold">
        {copied ? <Check className="w-5 h-5" /> : <Copy className="w-5 h-5" />}
      </span>
    </button>
  );
};
