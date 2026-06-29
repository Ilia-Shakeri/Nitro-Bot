import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { X, Upload } from 'lucide-react';
import { submitReceipt } from '../api';
import { useToast } from '../context/ToastContext';

export const PaymentModal = ({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) => {
  const { t } = useTranslation();
  const { toast } = useToast();
  const [amount, setAmount]   = useState(10);
  const [method, setMethod]   = useState('card');
  const [receipt, setReceipt] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);

  if (!isOpen) return null;

  const handleUpload = async () => {
    if (!receipt || amount <= 0) return;
    setLoading(true);
    try {
      await submitReceipt(receipt, amount, method);
      toast(t('Receipt submitted successfully. Awaiting admin approval.'), 'success');
      onClose();
    } catch (e: unknown) {
      toast(e instanceof Error ? e.message : 'Unknown error', 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4">
      <div className="bg-card1 w-full max-w-sm rounded-2xl p-6 border border-gold/20 relative">
        <button onClick={onClose} className="absolute top-4 right-4 rtl:left-4 rtl:right-auto text-textSecondary hover:text-textPrimary">
          <X className="w-6 h-6" />
        </button>

        <h2 className="text-xl font-bold text-gold mb-4">{t('Refill Nitro')}</h2>

        <div className="space-y-4">
          <div>
            <label className="text-sm text-textSecondary block mb-1">{t('Nitro Amount')}</label>
            <input
              type="number"
              value={amount}
              onChange={e => setAmount(Number(e.target.value))}
              className="w-full bg-inputBg border border-inputBorder rounded-lg p-3 text-textPrimary outline-none"
              min="1"
            />
          </div>

          <div>
            <label className="text-sm text-textSecondary block mb-1">{t('Payment Method')}</label>
            <select
              value={method}
              onChange={e => setMethod(e.target.value)}
              className="w-full bg-inputBg border border-inputBorder rounded-lg p-3 text-textPrimary outline-none appearance-none"
            >
              <option value="card">{t('Card to Card')}</option>
              <option value="tether">{t('Tether (USDT)')}</option>
            </select>
          </div>

          <div className="pt-2">
            <input
              type="file"
              id="receiptUpload"
              accept="image/*"
              onChange={e => setReceipt(e.target.files?.[0] || null)}
              className="hidden"
            />
            <label
              htmlFor="receiptUpload"
              className="border border-dashed border-card3 bg-card2/50 rounded-xl p-4 flex flex-col items-center justify-center cursor-pointer hover:bg-card3/20 transition"
            >
              <Upload className="text-gold w-8 h-8 mb-2" />
              <span className="text-sm font-semibold">
                {receipt ? receipt.name : t('Upload Receipt Screenshot')}
              </span>
            </label>
          </div>

          <button
            onClick={handleUpload}
            disabled={loading || !receipt}
            className="w-full bg-gold text-background font-bold py-3 rounded-xl shadow-lg hover:opacity-90 disabled:opacity-50 mt-4"
          >
            {loading ? 'Processing...' : t('Submit Receipt')}
          </button>
        </div>
      </div>
    </div>
  );
};
