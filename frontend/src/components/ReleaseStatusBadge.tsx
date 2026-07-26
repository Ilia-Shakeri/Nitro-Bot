import { AlertCircle, CheckCircle2, Clock3, LoaderCircle, RotateCcw } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import type { Release } from '../types/api';
import { releaseStatusKey } from '../utils/releasePresentation';

const styles: Record<string, string> = {
  completed: 'border-emerald-400/30 bg-emerald-400/10 text-emerald-400',
  failed: 'border-red-400/30 bg-red-400/10 text-red-400',
  rollback: 'border-blue-400/30 bg-blue-400/10 text-blue-400',
  manual_staging: 'border-gold/35 bg-gold/10 text-gold',
};

export const ReleaseStatusBadge = ({ release }: { release: Release }) => {
  const { t } = useTranslation();
  const status = releaseStatusKey(release);
  const Icon = status === 'completed'
    ? CheckCircle2
    : status === 'failed'
      ? AlertCircle
      : status === 'rollback'
        ? RotateCcw
        : status === 'processing' || status === 'staging'
          ? LoaderCircle
          : Clock3;
  return (
    <span className={`inline-flex items-center gap-1 rounded-full border px-2 py-1 text-[11px] font-ui ${styles[status] ?? 'border-inputBorder bg-card2 text-textSecondary'}`}>
      <Icon aria-hidden="true" className="h-3 w-3" />
      {t(status)}
    </span>
  );
};
