import { useEffect, useRef, useState } from 'react';
import { Image as ImageIcon, Music } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { useNavigate, useParams } from 'react-router-dom';
import { getReleases, submitRelease } from '../api';
import { HomeHeader } from '../components/HomeHeader';
import { NitroCostSummary } from '../components/NitroCostSummary';
import { ReleaseMetadataFields } from '../components/ReleaseMetadataFields';
import { useToast } from '../context/ToastContext';
import { useUser } from '../context/UserContext';
import { isRtlLanguage } from '../i18n';
import { usePricing } from '../pricing';
import type { Release } from '../types/api';
import { allowedCoverMessage, allowedMusicMessage, errorText } from '../utils/formMessages';
import {
  appendReleaseMetadata,
  emptyReleaseMetadata,
  type ReleaseMetadata,
  validateReleaseMetadata,
} from '../utils/releaseForm';

const parseProducers = (raw: string | null) => {
  if (!raw) return [];
  try {
    const parsed: unknown = JSON.parse(raw);
    return Array.isArray(parsed)
      ? parsed.filter((item): item is string => typeof item === 'string')
      : [];
  } catch {
    return [];
  }
};

const releaseMetadata = (release: Release): ReleaseMetadata => ({
  songName: release.song_name,
  artists: release.artists?.length
    ? release.artists
    : [{ name: release.artist_name, role: 'primary' }],
  producers: parseProducers(release.producers),
  legalNames: release.legal_names?.length ? release.legal_names : [release.legal_name],
  releaseDate: release.release_date,
  isRerelease: release.is_rerelease,
  originalReleaseDate: release.original_release_date ?? '',
  genre: release.genre ?? '',
  subGenre: release.sub_genre ?? '',
  copyrightRequested: false,
});

const newSubmissionId = () =>
  globalThis.crypto?.randomUUID?.() ?? `${Date.now()}-${Math.random().toString(36).slice(2)}`;

export const EditPage = () => {
  const { t, i18n } = useTranslation();
  const { id } = useParams();
  const navigate = useNavigate();
  const { user, refreshUser } = useUser();
  const { toast } = useToast();
  const { pricing } = usePricing();
  const submitting = useRef(false);
  const submissionId = useRef(newSubmissionId());
  const [metadata, setMetadata] = useState(emptyReleaseMetadata);
  const [source, setSource] = useState<Release | null>(null);
  const [audioFile, setAudioFile] = useState<File | null>(null);
  const [coverFile, setCoverFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [prefillLoading, setPrefillLoading] = useState(true);
  const credits = user?.credits ?? 0;
  const totalCost = pricing.edit_release_price
    + (metadata.copyrightRequested ? pricing.copyright_price : 0);

  useEffect(() => {
    let cancelled = false;
    getReleases()
      .then(releases => {
        if (cancelled) return;
        const found = releases.find(item => String(item.id) === String(id));
        if (!found) {
          toast(t('source_release_not_found'), 'error');
          return;
        }
        setSource(found);
        setMetadata(releaseMetadata(found));
      })
      .catch(error => {
        if (!cancelled) toast(errorText(error, t), 'error');
      })
      .finally(() => {
        if (!cancelled) setPrefillLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [id, t, toast]);

  const handleAudioFile = (file?: File) => {
    if (!file) return;
    if (!/\.(mp3|wav)$/i.test(file.name)) {
      toast(allowedMusicMessage(t), 'error');
      return;
    }
    setAudioFile(file);
  };
  const handleCoverFile = (file?: File) => {
    if (!file) return;
    if (!/\.(jpe?g|png|webp)$/i.test(file.name)) {
      toast(allowedCoverMessage(t), 'error');
      return;
    }
    setCoverFile(file);
  };

  const handleSubmit = async () => {
    if (submitting.current) return;
    if (!id || !source) {
      toast(t('edited_release_id_required'), 'error');
      return;
    }
    const validationError = validateReleaseMetadata(
      metadata,
      metadata.isRerelease === source.is_rerelease ? source.release_date : undefined,
    );
    if (validationError) {
      toast(t(validationError), 'error');
      return;
    }
    if (credits < totalCost) {
      toast(t('insufficient_credits'), 'error');
      return;
    }

    submitting.current = true;
    setLoading(true);
    try {
      const form = new FormData();
      if (audioFile) form.append('audio', audioFile);
      if (coverFile) form.append('cover', coverFile);
      appendReleaseMetadata(form, metadata);
      form.append('edited_release_id', id);
      form.append('submission_id', submissionId.current);
      form.append('is_edit', 'true');
      await submitRelease(form);
      await refreshUser();
      toast(t('Edit submitted successfully!'), 'success');
      navigate('/');
    } catch (error: unknown) {
      submitting.current = false;
      toast(errorText(error, t), 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      className="min-h-[var(--tg-viewport-stable-height,100vh)] bg-background max-w-md mx-auto relative overflow-y-auto"
      dir={isRtlLanguage(i18n.language) ? 'rtl' : 'ltr'}
    >
      <HomeHeader credits={credits} lang={i18n.language} />
      <main className="px-4 py-2">
        <h1 className="text-3xl font-title mb-2">{t('Edit Release')}</h1>
        <p className="text-sm font-ui text-textSecondary mb-8 leading-relaxed">
          {t('Update your release metadata and assets.')}
        </p>

        <div className="mb-6">
          <label htmlFor="edit-audio" className="block text-gold font-ui mb-2">
            1. {t('Audio File')}
          </label>
          <input
            id="edit-audio"
            type="file"
            accept=".mp3,.wav,audio/mpeg,audio/wav"
            onChange={event => handleAudioFile(event.target.files?.[0])}
            className="sr-only"
          />
          <label htmlFor="edit-audio" className="flex min-h-20 cursor-pointer items-center rounded-xl border border-dashed border-card3 bg-card2/50 p-4">
            <Music className="me-4 h-6 w-6 flex-shrink-0 text-gold" />
            <span dir="auto" className="truncate">
              {audioFile?.name ?? t('Keep current audio or choose file')}
            </span>
          </label>
        </div>

        <div className="mb-6">
          <label htmlFor="edit-cover" className="block text-gold font-ui mb-2">
            2. {t('Cover Art')}
          </label>
          <input
            id="edit-cover"
            type="file"
            accept=".jpg,.jpeg,.png,.webp,image/jpeg,image/png,image/webp"
            onChange={event => handleCoverFile(event.target.files?.[0])}
            className="sr-only"
          />
          <label htmlFor="edit-cover" className="flex min-h-20 cursor-pointer items-center rounded-xl border border-dashed border-card3 bg-card2/50 p-4">
            <ImageIcon className="me-4 h-6 w-6 flex-shrink-0 text-gold" />
            <span dir="auto" className="truncate">
              {coverFile?.name ?? t('Keep current cover or choose file')}
            </span>
          </label>
        </div>

        {prefillLoading ? (
          <p className="py-10 text-center text-textSecondary">{t('Loading...')}</p>
        ) : source ? (
          <>
            <ReleaseMetadataFields value={metadata} onChange={setMetadata} />
            <div className="pb-8">
              <NitroCostSummary
                items={[
                  { label: t('Edit release cost'), amount: pricing.edit_release_price },
                  ...(metadata.copyrightRequested
                    ? [{ label: t('Copyright protection cost'), amount: pricing.copyright_price }]
                    : []),
                ]}
              />
              <button
                type="button"
                onClick={handleSubmit}
                disabled={loading}
                className="mt-4 flex min-h-14 w-full items-center justify-center rounded-xl bg-gradient-to-r from-gold to-[#B8860B] py-4 font-title text-background shadow-lg hover:opacity-90 disabled:opacity-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gold"
              >
                {loading ? t('Processing...') : t('Submit Edit')}
              </button>
            </div>
          </>
        ) : (
          <p className="py-10 text-center text-red-400">{t('source_release_not_found')}</p>
        )}
      </main>
    </div>
  );
};
