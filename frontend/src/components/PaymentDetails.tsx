import { Bitcoin, Coins, Copy } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import type { PaymentConfig, PaymentMethod } from '../types/api';
import { useToast } from '../context/ToastContext';
import { CopyField } from './CopyField';

const formatCard = (value: string) => value.replace(/(.{4})/g, '$1 ').trim();

const copyToClipboard = async (value: string): Promise<boolean> => {
  try {
    await navigator.clipboard.writeText(value);
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
      className="relative w-full overflow-hidden rounded-2xl border border-white/10 bg-gradient-to-br from-[#0A4DA3] via-[#0B63D6] to-[#063b7d] p-5 text-start shadow-lg focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gold"
    >
      <div className="relative z-10 mb-6 h-8 w-11 rounded-md border border-[#8A6D1F] bg-gradient-to-br from-[#FCEFB4] via-[#E6B84D] to-[#B8860B]" />
      <div dir="ltr" className="relative z-10 mb-5 flex items-center justify-center gap-2">
        <span className="select-text font-mono text-base tracking-[0.14em] text-white">
          {formatCard(info.number)}
        </span>
        <Copy className="h-4 w-4 shrink-0 text-white/70" />
      </div>
      <span className="block text-[10px] uppercase text-white/60">{t('Card Holder')}</span>
      <span dir="auto" className="block text-sm font-semibold text-white">{info.holder}</span>
    </button>
  );
};

const CryptoCard = ({ info, kind }: { info: PaymentMethod; kind: 'btc' | 'usdt' }) => {
  const { t } = useTranslation();
  const Icon = kind === 'btc' ? Bitcoin : Coins;
  if (!info.address || !info.network) return null;
  return (
    <div className="space-y-3">
      <div className="rounded-2xl border border-gold/25 bg-gradient-to-br from-cardGold to-card1 p-5 shadow-lg">
        <div className="flex items-center gap-3">
          <span className="flex h-11 w-11 items-center justify-center rounded-full border border-gold/40 bg-gold/15 text-gold">
            <Icon className="h-6 w-6" />
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
  method: string;
  config: PaymentConfig | null;
}) => {
  const { t } = useTranslation();
  if (!config) {
    return <p role="alert" className="rounded-xl border border-red-500/30 p-3 text-sm text-red-400">{t('payment_config_unavailable')}</p>;
  }
  if (method === 'card' && config.card) return <BankCard info={config.card} />;
  if (method === 'btc' && config.btc) return <CryptoCard kind="btc" info={config.btc} />;
  if (method === 'usdt' && config.usdt) return <CryptoCard kind="usdt" info={config.usdt} />;
  return <p role="alert" className="text-sm text-red-400">{t('payment_method_unavailable')}</p>;
};
