import { ArrowRight, Image as ImageIcon, Music } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate, useParams } from 'react-router-dom';
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
import type { ArtistMapping, Release } from '../types/api';
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
import { parseProducers, releaseTotal } from '../utils/releasePresentation';
import { useObjectUrl } from '../utils/useObjectUrl';

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
  pendingArtist: '',
  pendingProducer: '',
  pendingLegalName: '',
});

const recoveredMappings = (release: Release): ArtistMapping[] => {
  if (release.artist_mappings?.length) return release.artist_mappings;
  const primary = (release.artists?.find(artist => artist.role === 'primary')?.name)
    ?? release.artist_name;
  if (
    release.mapping_spotify
    || release.mapping_apple
    || release.profile_email
    || release.requires_new_profile
  ) {
    return [{
      artist_name: primary,
      requires_new_profile: release.requires_new_profile,
      profile_email: release.profile_email,
      spotify_url: release.mapping_spotify,
      apple_music_url: release.mapping_apple,
    }];
  }
  return [];
};

const newSubmissionId = () =>
  globalThis.crypto?.randomUUID?.() ?? `${Date.now()}-${Math.random().toString(36).slice(2)}`;

type FieldErrors = Partial<Record<'song' | 'artists' | 'producers' | 'legal_names', string>>;

export const EditPage = () => {
  const { t, i18n } = useTranslation();
  const { id } = useParams();
  const navigate = useNavigate();
  const { user, refreshUser } = useUser();
  const { loadRelease, invalidateReleases } = useReleases();
  const { toast } = useToast();
  const { pricing } = usePricing();
  const submitting = useRef(false);
  const submissionId = useRef(newSubmissionId());
  const headingRef = useRef<HTMLHeadingElement>(null);
  const [step, setStep] = useState<ReleaseStep>('details');
  const [metadata, setMetadata] = useState(emptyReleaseMetadata);
  const [artistMappings, setArtistMappings] = useState<ArtistMapping[]>([]);
  const [source, setSource] = useState<Release | null>(null);
  const [audioFile, setAudioFile] = useState<File | null>(null);
  const [coverFile, setCoverFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [prefillLoading, setPrefillLoading] = useState(Number.isInteger(Number(id)));
  const [policyAccepted, setPolicyAccepted] = useState(false);
  const [policyError, setPolicyError] = useState('');
  const [mappingError, setMappingError] = useState<ArtistMappingValidationError | null>(null);
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const replacementCoverPreview = useObjectUrl(coverFile);
  const credits = user?.credits ?? 0;
  const totalCost = releaseTotal(pricing, true, metadata.copyrightRequested);

  useEffect(() => {
    let cancelled = false;
    const releaseId = Number(id);
    if (!Number.isInteger(releaseId)) return;
    loadRelease(releaseId)
      .then(found => {
        if (cancelled) return;
        const nextMetadata = releaseMetadata(found);
        setSource(found);
        setMetadata(nextMetadata);
        setArtistMappings(reconcileArtistMappings(nextMetadata.artists, recoveredMappings(found)));
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
  }, [id, loadRelease, t, toast]);

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
    if (!source) return;
    const committed = commitPendingMetadata(metadata);
    setMetadata(committed.metadata);
    if (committed.error) {
      setFieldErrors({ [committed.field ?? 'artists']: committed.error });
      return;
    }
    const validationError = validateReleaseMetadata(
      committed.metadata,
      committed.metadata.isRerelease === source.is_rerelease ? source.release_date : undefined,
    );
    if (validationError) {
      const field = metadataErrorField(committed.metadata, validationError);
      setFieldErrors(field ? { [field]: validationError } : {});
      toast(t(validationError), 'error');
      return;
    }
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
    if (submitting.current || !id || !source) return;
    if (!policyAccepted) {
      setPolicyError('policy_acceptance_required');
      return;
    }
    const metadataError = validateReleaseMetadata(
      metadata,
      metadata.isRerelease === source.is_rerelease ? source.release_date : undefined,
    );
    const mappingValidation = validateArtistMappings(metadata.artists, artistMappings);
    if (metadataError || mappingValidation) {
      toast(t(metadataError ?? mappingValidation?.key ?? 'required_fields_missing', {
        artist: mappingValidation?.artist,
      }), 'error');
      return;
    }
    submitting.current = true;
    setLoading(true);
    try {
      const form = new FormData();
      if (audioFile) form.append('audio', audioFile);
      if (coverFile) form.append('cover', coverFile);
      appendReleaseMetadata(form, metadata);
      form.append('artist_mappings', JSON.stringify(artistMappings));
      form.append('policy_accepted', 'true');
      form.append('edited_release_id', id);
      form.append('submission_id', submissionId.current);
      form.append('is_edit', 'true');
      await submitRelease(form);
      invalidateReleases();
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

  if (step === 'review' && source) {
    return (
      <div dir={isRtlLanguage(i18n.language) ? 'rtl' : 'ltr'}>
        <ReleaseReview
          metadata={metadata}
          artistMappings={artistMappings}
          pricing={pricing}
          balance={credits}
          audioFile={audioFile}
          coverFile={coverFile}
          coverPreview={replacementCoverPreview ?? source.cover_url}
          source={source}
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
              {t('Update your release metadata and assets.')}
            </p>

            <div className="mb-6">
              <label htmlFor="edit-audio" className="mb-2 block text-start font-ui text-gold">
                1. {t('Audio File')}
              </label>
              <input id="edit-audio" type="file" accept=".mp3,.wav,audio/mpeg,audio/wav" onChange={event => handleAudioFile(event.target.files?.[0])} className="sr-only" />
              <label htmlFor="edit-audio" className="flex min-h-20 cursor-pointer items-center rounded-xl border border-dashed border-card3 bg-card2/50 p-4 focus-within:ring-2 focus-within:ring-gold">
                <Music aria-hidden="true" className="me-4 h-6 w-6 flex-shrink-0 text-gold" />
                <span dir="ltr" className="truncate text-left">
                  {audioFile?.name ?? t('Keep current audio or choose file')}
                </span>
              </label>
            </div>

            <div className="mb-6">
              <label htmlFor="edit-cover" className="mb-2 block text-start font-ui text-gold">
                2. {t('Cover Art')}
              </label>
              <input id="edit-cover" type="file" accept=".jpg,.jpeg,.png,.webp,image/jpeg,image/png,image/webp" onChange={event => handleCoverFile(event.target.files?.[0])} className="sr-only" />
              <label htmlFor="edit-cover" className="flex min-h-20 cursor-pointer items-center rounded-xl border border-dashed border-card3 bg-card2/50 p-4 focus-within:ring-2 focus-within:ring-gold">
                <ImageIcon aria-hidden="true" className="me-4 h-6 w-6 flex-shrink-0 text-gold" />
                <span dir="ltr" className="truncate text-left">
                  {coverFile?.name ?? t('Keep current cover or choose file')}
                </span>
              </label>
            </div>

            {prefillLoading ? (
              <div className="space-y-4 py-4" aria-label={t('Loading...')}>
                {[0, 1, 2, 3].map(item => <div key={item} className="h-20 animate-pulse rounded-xl bg-card1" />)}
              </div>
            ) : source ? (
              <>
                <ReleaseMetadataFields value={metadata} onChange={updateMetadata} fieldErrors={fieldErrors} />
                <CopyrightOption
                  checked={metadata.copyrightRequested}
                  price={pricing.copyright_price}
                  onChange={copyrightRequested => updateMetadata({ ...metadata, copyrightRequested })}
                />
                <button
                  type="button"
                  onClick={continueToMapping}
                  className="mb-8 mt-4 flex min-h-14 w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-gold to-[#B8860B] py-4 font-title text-background shadow-lg focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gold"
                >
                  {t('Continue to Artist Mapping')}
                  <ArrowRight aria-hidden="true" className="h-4 w-4 rtl:rotate-180" />
                </button>
              </>
            ) : (
              <p className="py-10 text-center text-red-400">{t('source_release_not_found')}</p>
            )}
          </>
        )}
      </main>
    </div>
  );
};
