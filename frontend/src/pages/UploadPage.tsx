import { ArrowRight, Image as ImageIcon, Music } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { submitRelease } from '../api';
import { ArtistMappingStep } from '../components/ArtistMappingStep';
import { CopyrightOption } from '../components/CopyrightOption';
import { HomeHeader } from '../components/HomeHeader';
import { ReleaseMetadataFields } from '../components/ReleaseMetadataFields';
import { ReleaseReview } from '../components/ReleaseReview';
import { useReleases } from '../context/ReleaseContext';
import { useToast } from '../context/ToastContext';
import { useUser } from '../context/UserContext';
import { isRtlLanguage } from '../i18n';
import { usePricing } from '../pricing';
import type { ArtistMapping } from '../types/api';
import { allowedCoverMessage, allowedMusicMessage, errorText } from '../utils/formMessages';
import {
  appendReleaseMetadata,
  commitPendingMetadata,
  emptyReleaseMetadata,
  metadataErrorField,
  reconcileArtistMappings,
  type ReleaseMetadata,
  type ReleaseStep,
  type ArtistMappingValidationError,
  validateArtistMappings,
  validateReleaseMetadata,
} from '../utils/releaseForm';
import { releaseTotal } from '../utils/releasePresentation';
import { useObjectUrl } from '../utils/useObjectUrl';

const newSubmissionId = () =>
  globalThis.crypto?.randomUUID?.() ?? `${Date.now()}-${Math.random().toString(36).slice(2)}`;

type FieldErrors = Partial<Record<'song' | 'artists' | 'producers' | 'legal_names', string>>;

export const UploadPage = () => {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const { user, refreshUser } = useUser();
  const { invalidateReleases } = useReleases();
  const { toast } = useToast();
  const { pricing } = usePricing();
  const submissionId = useRef(newSubmissionId());
  const submitting = useRef(false);
  const headingRef = useRef<HTMLHeadingElement>(null);
  const [step, setStep] = useState<ReleaseStep>('details');
  const [metadata, setMetadata] = useState(emptyReleaseMetadata);
  const [artistMappings, setArtistMappings] = useState<ArtistMapping[]>([]);
  const [audioFile, setAudioFile] = useState<File | null>(null);
  const [coverFile, setCoverFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [policyAccepted, setPolicyAccepted] = useState(false);
  const [policyError, setPolicyError] = useState('');
  const [mappingError, setMappingError] = useState<ArtistMappingValidationError | null>(null);
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const coverPreview = useObjectUrl(coverFile);
  const credits = user?.credits ?? 0;
  const totalCost = releaseTotal(pricing, false, metadata.copyrightRequested);

  useEffect(() => {
    if (step === 'details') {
      headingRef.current?.focus();
      window.scrollTo({ top: 0, behavior: 'auto' });
    }
  }, [step]);

  const updateMetadata = (next: ReleaseMetadata) => {
    setMetadata(next);
    setPolicyAccepted(false);
    setPolicyError('');
    setFieldErrors({});
  };

  const handleAudioFile = (file?: File) => {
    if (!file) return;
    if (!/\.(mp3|wav)$/i.test(file.name)) {
      toast(allowedMusicMessage(t), 'error');
      return;
    }
    setAudioFile(file);
    setPolicyAccepted(false);
  };

  const handleCoverFile = (file?: File) => {
    if (!file) return;
    if (!/\.(jpe?g|png|webp)$/i.test(file.name)) {
      toast(allowedCoverMessage(t), 'error');
      return;
    }
    setCoverFile(file);
    setPolicyAccepted(false);
  };

  const continueToMapping = () => {
    const committed = commitPendingMetadata(metadata);
    setMetadata(committed.metadata);
    if (committed.error) {
      setFieldErrors({ [committed.field ?? 'artists']: committed.error });
      return;
    }
    const validationError = validateReleaseMetadata(committed.metadata);
    if (!audioFile || !coverFile || validationError) {
      const error = validationError ?? 'required_fields_missing';
      const field = metadataErrorField(committed.metadata, error);
      setFieldErrors(field ? { [field]: error } : {});
      toast(t(error), 'error');
      return;
    }
    setFieldErrors({});
    setArtistMappings(current => reconcileArtistMappings(committed.metadata.artists, current));
    setStep('mapping');
  };

  const continueToReview = () => {
    const error = validateArtistMappings(metadata.artists, artistMappings);
    if (error) {
      setMappingError(error);
      return;
    }
    if (credits < totalCost) {
      toast(t('insufficient_credits'), 'error');
      return;
    }
    setMappingError(null);
    setStep('review');
  };

  const submitFinal = async () => {
    if (submitting.current) return;
    if (!policyAccepted) {
      setPolicyError('policy_acceptance_required');
      return;
    }
    const metadataError = validateReleaseMetadata(metadata);
    const mappingValidation = validateArtistMappings(metadata.artists, artistMappings);
    if (metadataError || mappingValidation || !audioFile || !coverFile) {
      toast(t(metadataError ?? mappingValidation?.key ?? 'required_fields_missing', {
        artist: mappingValidation?.artist,
      }), 'error');
      return;
    }
    submitting.current = true;
    setLoading(true);
    try {
      const form = new FormData();
      form.append('audio', audioFile);
      form.append('cover', coverFile);
      appendReleaseMetadata(form, metadata);
      form.append('artist_mappings', JSON.stringify(artistMappings));
      form.append('policy_accepted', 'true');
      form.append('submission_id', submissionId.current);
      form.append('is_edit', 'false');
      await submitRelease(form);
      invalidateReleases();
      await refreshUser();
      toast(t('Release submitted successfully!'), 'success');
      navigate('/');
    } catch (error: unknown) {
      submitting.current = false;
      toast(errorText(error, t), 'error');
    } finally {
      setLoading(false);
    }
  };

  if (step === 'review') {
    return (
      <div dir={isRtlLanguage(i18n.language) ? 'rtl' : 'ltr'}>
        <ReleaseReview
          metadata={metadata}
          artistMappings={artistMappings}
          pricing={pricing}
          balance={credits}
          audioFile={audioFile}
          coverFile={coverFile}
          coverPreview={coverPreview}
          submitting={loading}
          policyAccepted={policyAccepted}
          policyError={policyError}
          onPolicyAcceptedChange={accepted => {
            setPolicyAccepted(accepted);
            setPolicyError('');
          }}
          onBack={() => setStep('mapping')}
          onConfirm={submitFinal}
        />
      </div>
    );
  }

  return (
    <div
      className="min-h-[var(--tg-viewport-stable-height,100vh)] bg-background"
      dir={isRtlLanguage(i18n.language) ? 'rtl' : 'ltr'}
    >
      <HomeHeader credits={credits} lang={i18n.language} />
      <main className="mx-auto max-w-md px-4 py-2">
        {step === 'mapping' ? (
          <ArtistMappingStep
            artists={metadata.artists}
            mappings={artistMappings}
            error={mappingError}
            onChange={mappings => {
              setArtistMappings(mappings);
              setMappingError(null);
              setPolicyAccepted(false);
            }}
            onBack={() => setStep('details')}
            onContinue={continueToReview}
          />
        ) : (
          <>
            <h1 ref={headingRef} tabIndex={-1} className="mb-2 text-start text-3xl font-title outline-none">
              {t('Release Details')}
            </h1>
            <p className="mb-8 text-start text-sm font-ui leading-relaxed text-textSecondary">
              {t('Publish your next track with clean metadata and platform mapping.')}
            </p>

            <div className="mb-6">
              <label htmlFor="audio-upload" className="mb-2 block text-start font-ui text-gold">
                1. {t('Audio File')} *
              </label>
              <input
                id="audio-upload"
                type="file"
                accept=".mp3,.wav,audio/mpeg,audio/wav"
                onChange={event => handleAudioFile(event.target.files?.[0])}
                className="sr-only"
              />
              <label htmlFor="audio-upload" className="flex min-h-20 cursor-pointer items-center rounded-xl border border-dashed border-card3 bg-card2/50 p-4 hover:bg-card3/20 focus-within:ring-2 focus-within:ring-gold">
                <span className="me-4 flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-full border border-gold/50">
                  <Music aria-hidden="true" className="h-6 w-6 text-gold" />
                </span>
                <span className="min-w-0 text-start">
                  <span dir="ltr" className="block truncate text-left font-ui">
                    {audioFile?.name ?? t('Drop audio or choose file')}
                  </span>
                  <span className="text-xs text-textSecondary">{t('MP3, WAV')}</span>
                </span>
              </label>
            </div>

            <div className="mb-6">
              <label htmlFor="cover-upload" className="mb-2 block text-start font-ui text-gold">
                2. {t('Cover Art')} *
              </label>
              <input
                id="cover-upload"
                type="file"
                accept=".jpg,.jpeg,.png,.webp,image/jpeg,image/png,image/webp"
                onChange={event => handleCoverFile(event.target.files?.[0])}
                className="sr-only"
              />
              <label htmlFor="cover-upload" className="flex min-h-20 cursor-pointer items-center rounded-xl border border-dashed border-card3 bg-card2/50 p-4 hover:bg-card3/20 focus-within:ring-2 focus-within:ring-gold">
                <span className="me-4 flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-full border border-gold/50">
                  <ImageIcon aria-hidden="true" className="h-6 w-6 text-gold" />
                </span>
                <span className="min-w-0 text-start">
                  <span dir="ltr" className="block truncate text-left font-ui">
                    {coverFile?.name ?? t('Drop cover art or choose file')}
                  </span>
                  <span className="text-xs text-textSecondary">{t('JPG, PNG, WEBP')}</span>
                </span>
              </label>
            </div>

            <ReleaseMetadataFields value={metadata} onChange={updateMetadata} fieldErrors={fieldErrors} />
            <CopyrightOption
              checked={metadata.copyrightRequested}
              price={pricing.copyright_price}
              onChange={copyrightRequested => updateMetadata({ ...metadata, copyrightRequested })}
            />
            <button
              type="button"
              onClick={continueToMapping}
              className="mb-8 mt-4 flex min-h-14 w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-gold to-[#B8860B] py-4 font-title text-background shadow-lg hover:opacity-90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gold"
            >
              {t('Continue to Artist Mapping')}
              <ArrowRight aria-hidden="true" className="h-4 w-4 rtl:rotate-180" />
            </button>
          </>
        )}
      </main>
    </div>
  );
};
