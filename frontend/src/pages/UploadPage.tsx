import { Image as ImageIcon, Music } from 'lucide-react';
import { useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
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
import { allowedCoverMessage, allowedMusicMessage, errorText } from '../utils/formMessages';
import {
  appendReleaseMetadata,
  emptyReleaseMetadata,
  releaseStepAction,
  validateReleaseMetadata,
} from '../utils/releaseForm';
import { useObjectUrl } from '../utils/useObjectUrl';
import { releaseTotal } from '../utils/releasePresentation';

const newSubmissionId = () =>
  globalThis.crypto?.randomUUID?.() ?? `${Date.now()}-${Math.random().toString(36).slice(2)}`;

export const UploadPage = () => {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const { user, refreshUser } = useUser();
  const { invalidateReleases } = useReleases();
  const { toast } = useToast();
  const { pricing } = usePricing();
  const submissionId = useRef(newSubmissionId());
  const submitting = useRef(false);
  const [metadata, setMetadata] = useState(emptyReleaseMetadata);
  const [audioFile, setAudioFile] = useState<File | null>(null);
  const [coverFile, setCoverFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [reviewing, setReviewing] = useState(false);
  const [needsNewProfile, setNeedsNewProfile] = useState(false);
  const [profileEmail, setProfileEmail] = useState('');
  const [spotifyUrl, setSpotifyUrl] = useState('');
  const [appleUrl, setAppleUrl] = useState('');
  const coverPreview = useObjectUrl(coverFile);
  const lang = i18n.language;
  const credits = user?.credits ?? 0;
  const totalCost = releaseTotal(pricing, false, metadata.copyrightRequested);

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
    const validationError = validateReleaseMetadata(metadata);
    if (!audioFile || !coverFile || validationError) {
      toast(t(validationError ?? 'required_fields_missing'), 'error');
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
      || !audioFile
      || !coverFile
    ) return;
    submitting.current = true;
    setLoading(true);
    try {
      const form = new FormData();
      form.append('audio', audioFile);
      form.append('cover', coverFile);
      appendReleaseMetadata(form, metadata);
      form.append('submission_id', submissionId.current);
      form.append('requires_new_profile', String(needsNewProfile));
      form.append('is_edit', 'false');
      if (profileEmail.trim()) form.append('profile_email', profileEmail.trim());
      if (!needsNewProfile) {
        if (spotifyUrl.trim()) form.append('mapping_spotify', spotifyUrl.trim());
        if (appleUrl.trim()) form.append('mapping_apple', appleUrl.trim());
      }
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

  if (reviewing) {
    return (
      <div dir={isRtlLanguage(lang) ? 'rtl' : 'ltr'}>
        <ReleaseReview
          metadata={metadata}
          pricing={pricing}
          balance={credits}
          audioFile={audioFile}
          coverFile={coverFile}
          coverPreview={coverPreview}
          needsNewProfile={needsNewProfile}
          profileEmail={profileEmail}
          spotifyUrl={spotifyUrl}
          appleUrl={appleUrl}
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
      dir={isRtlLanguage(lang) ? 'rtl' : 'ltr'}
    >
      <HomeHeader credits={credits} lang={lang} />
      <main className="mx-auto max-w-md px-4 py-2">
        <h1 className="mb-2 text-start text-3xl font-title">{t('Upload Your Art')}</h1>
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
          <label
            htmlFor="audio-upload"
            className="flex min-h-20 cursor-pointer items-center rounded-xl border border-dashed border-card3 bg-card2/50 p-4 hover:bg-card3/20 focus-within:ring-2 focus-within:ring-gold"
          >
            <span className="me-4 flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-full border border-gold/50">
              <Music aria-hidden="true" className="h-6 w-6 text-gold" />
            </span>
            <span className="min-w-0 text-start">
              <span dir="auto" className="block truncate font-ui">
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
          <label
            htmlFor="cover-upload"
            className="flex min-h-20 cursor-pointer items-center rounded-xl border border-dashed border-card3 bg-card2/50 p-4 hover:bg-card3/20 focus-within:ring-2 focus-within:ring-gold"
          >
            <span className="me-4 flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-full border border-gold/50">
              <ImageIcon aria-hidden="true" className="h-6 w-6 text-gold" />
            </span>
            <span className="min-w-0 text-start">
              <span dir="auto" className="block truncate font-ui">
                {coverFile?.name ?? t('Drop cover art or choose file')}
              </span>
              <span className="text-xs text-textSecondary">{t('JPG, PNG, WEBP')}</span>
            </span>
          </label>
        </div>

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
      </main>
    </div>
  );
};
