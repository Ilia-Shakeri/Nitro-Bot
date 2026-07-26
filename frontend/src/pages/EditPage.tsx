import { Image as ImageIcon, Music } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate, useParams } from 'react-router-dom';
import { submitRelease } from '../api';
import { HomeHeader } from '../components/HomeHeader';
import { NitroCostSummary } from '../components/NitroCostSummary';
import { PlatformMappingFields } from '../components/PlatformMappingFields';
import { ReleaseMetadataFields } from '../components/ReleaseMetadataFields';
import { ReleaseReview } from '../components/ReleaseReview';
import { useReleases } from '../context/ReleaseContext';
import { useToast } from '../context/ToastContext';
import { useUser } from '../context/UserContext';
import { isRtlLanguage } from '../i18n';
import { usePricing } from '../pricing';
import type { Release } from '../types/api';
import { allowedCoverMessage, allowedMusicMessage, errorText } from '../utils/formMessages';
import {
  appendReleaseMetadata,
  emptyReleaseMetadata,
  releaseStepAction,
  type ReleaseMetadata,
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
});

const newSubmissionId = () =>
  globalThis.crypto?.randomUUID?.() ?? `${Date.now()}-${Math.random().toString(36).slice(2)}`;

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
  const [metadata, setMetadata] = useState(emptyReleaseMetadata);
  const [source, setSource] = useState<Release | null>(null);
  const [audioFile, setAudioFile] = useState<File | null>(null);
  const [coverFile, setCoverFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [prefillLoading, setPrefillLoading] = useState(Number.isInteger(Number(id)));
  const [reviewing, setReviewing] = useState(false);
  const [needsNewProfile, setNeedsNewProfile] = useState(false);
  const [profileEmail, setProfileEmail] = useState('');
  const [spotifyUrl, setSpotifyUrl] = useState('');
  const [appleUrl, setAppleUrl] = useState('');
  const replacementCoverPreview = useObjectUrl(coverFile);
  const credits = user?.credits ?? 0;
  const totalCost = releaseTotal(pricing, true, metadata.copyrightRequested);

  useEffect(() => {
    let cancelled = false;
    const releaseId = Number(id);
    if (!Number.isInteger(releaseId)) {
      return;
    }
    loadRelease(releaseId)
      .then(found => {
        if (cancelled) return;
        setSource(found);
        setMetadata(releaseMetadata(found));
        setNeedsNewProfile(found.requires_new_profile);
        setProfileEmail(found.profile_email ?? '');
        setSpotifyUrl(found.mapping_spotify ?? '');
        setAppleUrl(found.mapping_apple ?? '');
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

  const validateDraft = () => {
    if (!id || !source) {
      toast(t('edited_release_id_required'), 'error');
      return false;
    }
    const validationError = validateReleaseMetadata(
      metadata,
      metadata.isRerelease === source.is_rerelease ? source.release_date : undefined,
    );
    if (validationError) {
      toast(t(validationError), 'error');
      return false;
    }
    if (needsNewProfile && !profileEmail.trim()) {
      toast(t('profile_email_required'), 'error');
      return false;
    }
    if (credits < totalCost) {
      toast(t('insufficient_credits'), 'error');
      return false;
    }
    return true;
  };

  const openReview = () => {
    if (releaseStepAction('form', validateDraft()) === 'review') setReviewing(true);
  };

  const submitFinal = async () => {
    if (
      submitting.current
      || releaseStepAction('review', validateDraft()) !== 'submit'
      || !id
    ) return;
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
      form.append('requires_new_profile', String(needsNewProfile));
      if (profileEmail.trim()) form.append('profile_email', profileEmail.trim());
      if (!needsNewProfile) {
        form.append('mapping_spotify', spotifyUrl.trim());
        form.append('mapping_apple', appleUrl.trim());
      }
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

  if (reviewing && source) {
    return (
      <div dir={isRtlLanguage(i18n.language) ? 'rtl' : 'ltr'}>
        <ReleaseReview
          metadata={metadata}
          pricing={pricing}
          balance={credits}
          audioFile={audioFile}
          coverFile={coverFile}
          coverPreview={replacementCoverPreview ?? source.cover_url}
          needsNewProfile={needsNewProfile}
          profileEmail={profileEmail}
          spotifyUrl={spotifyUrl}
          appleUrl={appleUrl}
          source={source}
          submitting={loading}
          onBack={() => setReviewing(false)}
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
        <h1 className="mb-2 text-start text-3xl font-title">{t('Edit Release')}</h1>
        <p className="mb-8 text-start text-sm font-ui leading-relaxed text-textSecondary">
          {t('Update your release metadata and assets.')}
        </p>

        <div className="mb-6">
          <label htmlFor="edit-audio" className="mb-2 block text-start font-ui text-gold">
            1. {t('Audio File')}
          </label>
          <input
            id="edit-audio"
            type="file"
            accept=".mp3,.wav,audio/mpeg,audio/wav"
            onChange={event => handleAudioFile(event.target.files?.[0])}
            className="sr-only"
          />
          <label htmlFor="edit-audio" className="flex min-h-20 cursor-pointer items-center rounded-xl border border-dashed border-card3 bg-card2/50 p-4 focus-within:ring-2 focus-within:ring-gold">
            <Music aria-hidden="true" className="me-4 h-6 w-6 flex-shrink-0 text-gold" />
            <span dir="auto" className="truncate text-start">
              {audioFile?.name ?? t('Keep current audio or choose file')}
            </span>
          </label>
        </div>

        <div className="mb-6">
          <label htmlFor="edit-cover" className="mb-2 block text-start font-ui text-gold">
            2. {t('Cover Art')}
          </label>
          <input
            id="edit-cover"
            type="file"
            accept=".jpg,.jpeg,.png,.webp,image/jpeg,image/png,image/webp"
            onChange={event => handleCoverFile(event.target.files?.[0])}
            className="sr-only"
          />
          <label htmlFor="edit-cover" className="flex min-h-20 cursor-pointer items-center rounded-xl border border-dashed border-card3 bg-card2/50 p-4 focus-within:ring-2 focus-within:ring-gold">
            <ImageIcon aria-hidden="true" className="me-4 h-6 w-6 flex-shrink-0 text-gold" />
            <span dir="auto" className="truncate text-start">
              {coverFile?.name ?? t('Keep current cover or choose file')}
            </span>
          </label>
        </div>

        {prefillLoading ? (
          <div className="space-y-4 py-4" aria-label={t('Loading...')}>
            {[0, 1, 2, 3].map(item => (
              <div key={item} className="h-20 animate-pulse rounded-xl bg-card1" />
            ))}
          </div>
        ) : source ? (
          <>
            <ReleaseMetadataFields value={metadata} onChange={setMetadata} />
            <PlatformMappingFields
              needsNewProfile={needsNewProfile}
              onNeedsNewProfileChange={setNeedsNewProfile}
              profileEmail={profileEmail}
              onProfileEmailChange={setProfileEmail}
              spotifyUrl={spotifyUrl}
              onSpotifyUrlChange={setSpotifyUrl}
              appleUrl={appleUrl}
              onAppleUrlChange={setAppleUrl}
            />
            <div className="pb-8">
              <NitroCostSummary
                pricing={pricing}
                isEdit
                copyrightRequested={metadata.copyrightRequested}
              />
              <button
                type="button"
                onClick={openReview}
                className="mt-4 flex min-h-14 w-full items-center justify-center rounded-xl bg-gradient-to-r from-gold to-[#B8860B] py-4 font-title text-background shadow-lg hover:opacity-90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gold"
              >
                {t('Continue to review')}
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
