import { useTranslation } from 'react-i18next';
import { Bitcoin, Coins } from 'lucide-react';
import { CopyField } from './CopyField';

/** Payment destinations. Kept in one place so they are easy to rotate. */
export const PAYMENT_INFO = {
  card: {
    bank: 'Blu Bank',
    bankFa: 'بلو بانک',
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

/** Visually rich "Blu Bank" debit-card mock with a one-click copyable PAN. */
const BluBankCard = () => {
  const { t, i18n } = useTranslation();
  const isRTL = i18n.language === 'fa';
  const { number, holder } = PAYMENT_INFO.card;

  return (
    <div className="space-y-3">
      <div className="relative overflow-hidden rounded-2xl p-5 bg-gradient-to-br from-[#0A4DA3] via-[#0B63D6] to-[#063b7d] shadow-lg border border-white/10">
        {/* decorative orbs */}
        <div className="absolute -top-10 -right-8 w-40 h-40 rounded-full bg-white/10 blur-2xl pointer-events-none" />
        <div className="absolute -bottom-12 -left-6 w-44 h-44 rounded-full bg-cyan-300/20 blur-2xl pointer-events-none" />

        <div className="relative z-10 flex items-center justify-between mb-8">
          <span className="text-white font-bold text-lg tracking-wide">
            {isRTL ? PAYMENT_INFO.card.bankFa : PAYMENT_INFO.card.bank}
          </span>
          {/* EMV chip */}
          <span className="w-10 h-7 rounded-md bg-gradient-to-br from-yellow-200 to-yellow-500 border border-yellow-600/40" />
        </div>

        <div dir="ltr" className="relative z-10 text-white font-mono text-xl tracking-[0.18em] text-center mb-5 select-text">
          {formatCard(number)}
        </div>

        <div className="relative z-10 flex items-end justify-between">
          <div>
            <span className="block text-[10px] text-white/60 uppercase">{t('Card Holder')}</span>
            <span className="block text-white text-sm font-semibold">{holder}</span>
          </div>
        </div>
      </div>

      <CopyField label={t('Card Number')} value={number} display={formatCard(number)} />
      <CopyField label={t('Card Holder')} value={holder} mono={false} />
    </div>
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
          {t('Send the exact amount, then upload the transaction receipt below.')}
        </p>
      </div>

      <CopyField label={t('Wallet Address')} value={info.address} />
    </div>
  );
};

export const PaymentDetails = ({ method }: { method: string }) => {
  if (method === 'card') return <BluBankCard />;
  if (method === 'btc') return <CryptoCard kind="btc" />;
  if (method === 'usdt') return <CryptoCard kind="usdt" />;
  return null;
};
