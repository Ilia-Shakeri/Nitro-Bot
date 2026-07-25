import { useRef, useState } from 'react';
import { Image as ImageIcon, Mail, Music } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { submitRelease } from '../api';
import { FormToggle } from '../components/FormToggle';
import { HomeHeader } from '../components/HomeHeader';
import { NitroCostSummary } from '../components/NitroCostSummary';
import { ReleaseMetadataFields } from '../components/ReleaseMetadataFields';
import { useToast } from '../context/ToastContext';
import { useUser } from '../context/UserContext';
import { isRtlLanguage } from '../i18n';
import { usePricing } from '../pricing';
import { allowedCoverMessage, allowedMusicMessage, errorText } from '../utils/formMessages';
import {
  appendReleaseMetadata,
  emptyReleaseMetadata,
  validateReleaseMetadata,
} from '../utils/releaseForm';

const newSubmissionId = () =>
  globalThis.crypto?.randomUUID?.() ?? `${Date.now()}-${Math.random().toString(36).slice(2)}`;

export const UploadPage = () => {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const { user, refreshUser } = useUser();
  const { toast } = useToast();
  const { pricing } = usePricing();
  const submissionId = useRef(newSubmissionId());
  const submitting = useRef(false);
  const [metadata, setMetadata] = useState(emptyReleaseMetadata);
  const [audioFile, setAudioFile] = useState<File | null>(null);
  const [coverFile, setCoverFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [needsNewProfile, setNeedsNewProfile] = useState(false);
  const [profileEmail, setProfileEmail] = useState('');
  const [spotifyUrl, setSpotifyUrl] = useState('');
  const [appleUrl, setAppleUrl] = useState('');
  const lang = i18n.language;
  const credits = user?.credits ?? 0;
  const totalCost = pricing.discounted_release_price
    + (metadata.copyrightRequested ? pricing.copyright_price : 0);

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
    const validationError = validateReleaseMetadata(metadata);
    if (!audioFile || !coverFile || validationError) {
      toast(t(validationError ?? 'required_fields_missing'), 'error');
      return;
    }
    if (needsNewProfile && !profileEmail.trim()) {
      toast(t('profile_email_required'), 'error');
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

  return (
    <div
      className="min-h-[var(--tg-viewport-stable-height,100vh)] bg-background max-w-md mx-auto relative overflow-y-auto"
      dir={isRtlLanguage(lang) ? 'rtl' : 'ltr'}
    >
      <HomeHeader credits={credits} lang={lang} />
      <main className="px-4 py-2">
        <h1 className="text-3xl font-title mb-2">{t('Upload Your Art')}</h1>
        <p className="text-sm font-ui text-textSecondary mb-8 leading-relaxed">
          {t('Publish your next track with clean metadata and platform mapping.')}
        </p>

        <div className="mb-6">
          <label htmlFor="audio-upload" className="block text-gold font-ui mb-2">
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
              <Music className="h-6 w-6 text-gold" />
            </span>
            <span className="min-w-0">
              <span dir="auto" className="block truncate font-ui">
                {audioFile?.name ?? t('Drop audio or choose file')}
              </span>
              <span className="text-xs text-textSecondary">{t('MP3, WAV')}</span>
            </span>
          </label>
        </div>

        <div className="mb-6">
          <label htmlFor="cover-upload" className="block text-gold font-ui mb-2">
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
            className="flex min-h-20 cursor-pointer items-center rounded-xl border border-dashed border-card3 bg-card2/50 p-4 hover:bg-card3/20"
          >
            <span className="me-4 flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-full border border-gold/50">
              <ImageIcon className="h-6 w-6 text-gold" />
            </span>
            <span className="min-w-0">
              <span dir="auto" className="block truncate font-ui">
                {coverFile?.name ?? t('Drop cover art or choose file')}
              </span>
              <span className="text-xs text-textSecondary">{t('JPG, PNG, WEBP')}</span>
            </span>
          </label>
        </div>

        <ReleaseMetadataFields value={metadata} onChange={setMetadata} />

        <section className="mb-6">
          <h3 className="text-gold font-ui mb-2 text-sm">9. {t('Mapping')}</h3>
          <div className="mb-4">
            <FormToggle
              id="newProfile"
              checked={needsNewProfile}
              onChange={() => setNeedsNewProfile(current => !current)}
              label={t("I don't have a profile (Create one for me)")}
            />
          </div>
          {!needsNewProfile ? (
            <div className="space-y-3">
              <label className="block text-xs text-textSecondary">
                {t('Spotify')}
                <input
                  type="url"
                  value={spotifyUrl}
                  onChange={event => setSpotifyUrl(event.target.value)}
                  dir="ltr"
                  className="mt-1 w-full rounded-lg border border-inputBorder bg-inputBg p-3 text-textPrimary outline-none focus:border-gold/60"
                  placeholder="https://open.spotify.com/..."
                />
              </label>
              <label className="block text-xs text-textSecondary">
                {t('Apple Music')}
                <input
                  type="url"
                  value={appleUrl}
                  onChange={event => setAppleUrl(event.target.value)}
                  dir="ltr"
                  className="mt-1 w-full rounded-lg border border-inputBorder bg-inputBg p-3 text-textPrimary outline-none focus:border-gold/60"
                  placeholder="https://music.apple.com/..."
                />
              </label>
            </div>
          ) : (
            <div className="rounded-xl border border-gold/20 bg-gold/5 p-4">
              <p className="mb-2 text-xs font-ui text-gold">{t('New profile info needed')}</p>
              <label className="flex items-center rounded-lg border border-inputBorder bg-inputBg p-3">
                <Mail className="me-3 h-5 w-5 flex-shrink-0 text-gold" />
                <span className="sr-only">{t('Profile Email')}</span>
                <input
                  type="email"
                  value={profileEmail}
                  onChange={event => setProfileEmail(event.target.value)}
                  dir="ltr"
                  className="w-full bg-transparent text-sm text-textPrimary outline-none"
                  placeholder={t('Profile Email')}
                />
              </label>
            </div>
          )}
        </section>

        <div className="pb-8">
          <NitroCostSummary
            items={[
              {
                label: t('New release cost'),
                amount: pricing.discounted_release_price,
                originalAmount: pricing.original_release_price,
              },
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
            {loading ? t('Processing...') : t("Let's Cook!")}
          </button>
        </div>
      </main>
    </div>
  );
};
