import { useTranslation } from 'react-i18next';
import { Bitcoin, Coins, Copy } from 'lucide-react';
import { CopyField } from './CopyField';
import { useToast } from '../context/ToastContext';

/** Payment destinations. Kept in one place so they are easy to rotate. */
const PAYMENT_INFO = {
  card: {
    number: '6219861899632193',
    holder: 'محمد رحیم کریم‌زاده',
  },
  btc: {
    network: 'Bitcoin (BTC)',
    address: 'bc1qavfpkffqq68vxsyqlt330d8mu93z8nr533fhfa',
  },
  usdt: {
    network: 'USDT (TRC20)',
    address: 'TP1Yadt466uCb5pBQTbMZ8jqRk7TpZowXH',
  },
} as const;

/** Group the 16-digit PAN into 4-digit blocks for readability. */
const formatCard = (n: string) => n.replace(/(.{4})/g, '$1 ').trim();

/** Copy text to the clipboard with a fallback for insecure/older webviews. */
const copyToClipboard = async (value: string): Promise<boolean> => {
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
    return true;
  } catch {
    return false;
  }
};

/** Realistic gold EMV chip drawn with an inline SVG gradient. */
const GoldChip = () => (
  <svg width="42" height="32" viewBox="0 0 42 32" fill="none" aria-hidden="true" className="drop-shadow">
    <defs>
      <linearGradient id="nitroChipGold" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0" stopColor="#FCEFB4" />
        <stop offset="0.5" stopColor="#E6B84D" />
        <stop offset="1" stopColor="#B8860B" />
      </linearGradient>
    </defs>
    <rect x="0.6" y="0.6" width="40.8" height="30.8" rx="6" fill="url(#nitroChipGold)" stroke="#8A6D1F" strokeWidth="1" />
    {/* contact pad divider lines */}
    <path
      d="M0 11 H42 M0 21 H42 M14 0 V32 M28 0 V32"
      stroke="#8A6D1F"
      strokeOpacity="0.55"
      strokeWidth="1"
    />
    <rect x="14" y="11" width="14" height="10" fill="none" stroke="#8A6D1F" strokeOpacity="0.7" strokeWidth="1" />
  </svg>
);

/** Clickable debit-card mock — tapping anywhere copies the card number. */
const BankCard = () => {
  const { t } = useTranslation();
  const { toast } = useToast();
  const { number, holder } = PAYMENT_INFO.card;

  const handleCopy = async () => {
    const ok = await copyToClipboard(number);
    toast(
      ok ? t('Card number copied successfully.') : t('Copy failed'),
      ok ? 'success' : 'error',
    );
  };

  return (
    <button
      type="button"
      onClick={handleCopy}
      aria-label={t('Card Number')}
      className="relative w-full overflow-hidden rounded-2xl p-5 text-left bg-gradient-to-br from-[#0A4DA3] via-[#0B63D6] to-[#063b7d] shadow-lg border border-white/10 transition active:scale-[0.99] hover:border-white/25"
    >
      {/* decorative orbs */}
      <div className="absolute -top-10 -right-8 w-40 h-40 rounded-full bg-white/10 blur-2xl pointer-events-none" />
      <div className="absolute -bottom-12 -left-6 w-44 h-44 rounded-full bg-cyan-300/20 blur-2xl pointer-events-none" />

      {/* gold chip (top-left) */}
      <div className="relative z-10 mb-7">
        <GoldChip />
      </div>

      {/* 16-digit PAN — smaller font, copy icon directly beside it */}
      <div dir="ltr" className="relative z-10 flex items-center justify-center gap-2 mb-5">
        <span className="text-white font-mono text-base tracking-[0.14em] select-text">
          {formatCard(number)}
        </span>
        <Copy className="w-4 h-4 text-white/70 shrink-0" />
      </div>

      <div className="relative z-10">
        <span className="block text-[10px] text-white/60 uppercase">{t('Card Holder')}</span>
        <span className="block text-white text-sm font-semibold">{holder}</span>
      </div>
    </button>
  );
};

/** Crypto wallet panel (BTC / USDT) with copyable address. */
const CryptoCard = ({ kind }: { kind: 'btc' | 'usdt' }) => {
  const { t } = useTranslation();
  const info = PAYMENT_INFO[kind];
  const Icon = kind === 'btc' ? Bitcoin : Coins;

  return (
    <div className="space-y-3">
      <div className="relative overflow-hidden rounded-2xl p-5 bg-gradient-to-br from-cardGold to-card1 border border-gold/25 shadow-lg">
        <div className="absolute -top-10 -right-8 w-36 h-36 rounded-full bg-gold/10 blur-2xl pointer-events-none" />
        <div className="relative z-10 flex items-center gap-3 mb-2">
          <span className="w-11 h-11 rounded-full bg-gold/15 border border-gold/40 flex items-center justify-center text-gold">
            <Icon className="w-6 h-6" />
          </span>
          <div>
            <span className="block text-[11px] text-textSecondary">{t('Network')}</span>
            <span className="block text-gold font-bold">{info.network}</span>
          </div>
        </div>
        <p className="relative z-10 text-[11px] text-textSecondary leading-relaxed mt-2">
          {t('Send the exact amount shown below to this wallet address.')}
        </p>
      </div>

      <CopyField label={t('Wallet Address')} value={info.address} />
    </div>
  );
};

export const PaymentDetails = ({ method }: { method: string }) => {
  if (method === 'card') return <BankCard />;
  if (method === 'btc') return <CryptoCard kind="btc" />;
  if (method === 'usdt') return <CryptoCard kind="usdt" />;
  return null;
};
