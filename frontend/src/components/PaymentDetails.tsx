import { Coins, Copy } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import type { PaymentConfig, PaymentMethod } from '../types/api';
import { useToast } from '../context/ToastContext';
import type { TopupPaymentMethod } from '../utils/paymentMethods';
import { CopyField } from './CopyField';

const formatCard = (value: string) => value.replace(/(.{4})/g, '$1 ').trim();

const copyToClipboard = async (value: string): Promise<boolean> => {
  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(value);
    } else {
      const textarea = document.createElement('textarea');
      textarea.value = value;
      textarea.style.position = 'fixed';
      textarea.style.opacity = '0';
      document.body.appendChild(textarea);
      try {
        textarea.focus();
        textarea.select();
        if (!document.execCommand('copy')) return false;
      } finally {
        document.body.removeChild(textarea);
      }
    }
    return true;
  } catch {
    return false;
  }
};

const BankCard = ({ info }: { info: PaymentMethod }) => {
  const { t } = useTranslation();
  const { toast } = useToast();
  if (!info.number || !info.holder) return null;

  return (
    <button
      type="button"
      onClick={async () => {
        const copied = await copyToClipboard(info.number ?? '');
        toast(t(copied ? 'Card number copied successfully.' : 'Copy failed'), copied ? 'success' : 'error');
      }}
      aria-label={t('Copy card number')}
      className="relative min-h-52 w-full overflow-hidden rounded-2xl border border-white/15 bg-gradient-to-br from-[#1677D2] via-[#075AAF] to-[#02396F] p-5 text-start shadow-[0_18px_45px_rgba(2,57,111,0.38)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gold"
    >
      <span aria-hidden="true" className="absolute -end-14 -top-16 h-40 w-40 rounded-full border border-white/10 bg-white/5" />
      <span aria-hidden="true" className="absolute -bottom-20 -start-10 h-44 w-44 rounded-full border border-white/10 bg-black/5" />
      <div className="relative z-10 mb-5 flex items-start justify-between">
        <div className="h-9 w-12 rounded-md border border-[#8A6D1F] bg-gradient-to-br from-[#FCEFB4] via-[#E6B84D] to-[#B8860B]" />
        <span className="inline-flex items-center gap-1 rounded-full bg-white/10 px-2 py-1 text-[10px] text-white/80">
          <Copy aria-hidden="true" className="h-3 w-3" />
          {t('card_copy_hint')}
        </span>
      </div>
      <span className="relative z-10 mb-1 block text-[10px] uppercase text-white/60">{t('Card Number')}</span>
      <div dir="ltr" className="relative z-10 mb-5 flex items-center justify-start">
        <span className="select-text whitespace-nowrap font-mono text-sm tracking-[0.08em] text-white sm:text-lg sm:tracking-[0.12em]">
          {formatCard(info.number)}
        </span>
      </div>
      <span className="relative z-10 block text-[10px] uppercase text-white/60">{t('Card Holder')}</span>
      <span dir="auto" className="relative z-10 block text-sm font-semibold text-white">{info.holder}</span>
    </button>
  );
};

const CryptoCard = ({ info }: { info: PaymentMethod }) => {
  const { t } = useTranslation();
  if (!info.address || !info.network) return null;
  return (
    <div className="space-y-3">
      <div className="rounded-2xl border border-gold/25 bg-gradient-to-br from-cardGold to-card1 p-5 shadow-lg">
        <div className="flex items-center gap-3">
          <span className="flex h-11 w-11 items-center justify-center rounded-full border border-gold/40 bg-gold/15 text-gold">
            <Coins className="h-6 w-6" />
          </span>
          <span>
            <span className="block text-[11px] text-textSecondary">{t('Network')}</span>
            <span dir="ltr" className="block font-bold text-gold">{info.network}</span>
          </span>
        </div>
        <p className="mt-2 text-[11px] leading-relaxed text-textSecondary">
          {t('Send the exact amount shown below to this wallet address.')}
        </p>
      </div>
      <CopyField label={t('Wallet Address')} value={info.address} />
    </div>
  );
};

export const PaymentDetails = ({
  method,
  config,
}: {
  method: TopupPaymentMethod;
  config: PaymentConfig | null;
}) => {
  const { t } = useTranslation();
  if (!config) {
    return <p role="alert" className="rounded-xl border border-red-500/30 p-3 text-sm text-red-400">{t('payment_config_unavailable')}</p>;
  }
  if (method === 'card' && config.card) return <BankCard info={config.card} />;
  if (method === 'usdt' && config.usdt) return <CryptoCard info={config.usdt} />;
  return <p role="alert" className="text-sm text-red-400">{t('payment_method_unavailable')}</p>;
};
