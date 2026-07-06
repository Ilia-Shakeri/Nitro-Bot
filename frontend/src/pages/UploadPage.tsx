import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { HomeHeader } from '../components/HomeHeader';
import { PersianDatePicker } from '../components/PersianDatePicker';
import { Music, Image as ImageIcon, Calendar, User, AlignLeft, Mail } from 'lucide-react';
import { submitRelease, updateLanguage } from '../api';
import { useUser } from '../context/UserContext';
import { useToast } from '../context/ToastContext';
import { GenreSelect } from '../components/GenreSelect';
import { FormToggle } from '../components/FormToggle';
import { NitroCostSummary } from '../components/NitroCostSummary';
import { ProducerTagInput } from '../components/ProducerTagInput';
import { allowedCoverMessage, allowedMusicMessage, errorText } from '../utils/formMessages';

const NEW_RELEASE_WITH_PROFILE_COST = 10;
const NEW_RELEASE_WITHOUT_PROFILE_COST = 8;
const COPYRIGHT_COST = 1;

export const UploadPage = () => {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const lang = i18n.language;
  const { user, refreshUser } = useUser();
  const { toast } = useToast();
  const credits = user?.credits ?? 0;

  const [formData, setFormData] = useState({
    songName: '',
    artistName: '',
    producers: [] as string[],
    legalName: '',
    releaseDate: '',
    genre: '',
    subGenre: '',
    spotifyUrl: '',
    appleUrl: '',
    needsNewProfile: false,
    copyrightRequested: false,
    profileEmail: '',
  });

  const [audioFile, setAudioFile] = useState<File | null>(null);
  const [coverFile, setCoverFile] = useState<File | null>(null);
  const [loading, setLoading]     = useState(false);

  const handleToggleProfile   = () => setFormData(f => ({ ...f, needsNewProfile:    !f.needsNewProfile }));
  const handleToggleCopyright = () => setFormData(f => ({ ...f, copyrightRequested: !f.copyrightRequested }));

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
    if (
      !audioFile ||
      !coverFile ||
      !formData.songName ||
      !formData.artistName ||
      !formData.legalName ||
      !formData.releaseDate ||
      !formData.genre
    ) {
      toast(t('Please fill all required fields.'), 'error');
      return;
    }
    if (formData.needsNewProfile && !formData.profileEmail.trim()) {
      toast(t('Profile email is required.'), 'error');
      return;
    }
    setLoading(true);
    try {
      const form = new FormData();
      form.append('audio',    audioFile);
      form.append('cover',    coverFile);
      form.append('song_name',   formData.songName);
      form.append('artist_name', formData.artistName);
      form.append('producers', JSON.stringify(formData.producers));
      form.append('legal_name',  formData.legalName);
      form.append('release_date', formData.releaseDate);
      form.append('genre',        formData.genre);
      if (formData.subGenre) form.append('sub_genre', formData.subGenre);
      if (!formData.needsNewProfile) {
        if (formData.spotifyUrl) form.append('mapping_spotify', formData.spotifyUrl);
        if (formData.appleUrl)   form.append('mapping_apple',   formData.appleUrl);
      }
      if (formData.profileEmail)     form.append('profile_email',     formData.profileEmail);
      form.append('requires_new_profile', formData.needsNewProfile.toString());
      form.append('is_edit',              'false');
      form.append('copyright_requested',  formData.copyrightRequested.toString());
      await submitRelease(form);
      await refreshUser();
      toast(t('Release submitted successfully!'), 'success');
      navigate('/');
    } catch (e: unknown) {
      toast(errorText(e, t), 'error');
    } finally {
      setLoading(false);
    }
  };

  const isRTL = lang === 'fa';
  const baseCost = formData.needsNewProfile ? NEW_RELEASE_WITH_PROFILE_COST : NEW_RELEASE_WITHOUT_PROFILE_COST;
  const costItems = [
    {
      label: formData.needsNewProfile ? t('New profile release cost') : t('New release cost'),
      amount: baseCost,
    },
    ...(formData.copyrightRequested ? [{ label: t('Copyright protection cost'), amount: COPYRIGHT_COST }] : []),
  ];

  return (
    <div className="min-h-screen bg-background max-w-md mx-auto relative overflow-y-auto" dir={isRTL ? 'rtl' : 'ltr'}>
      <HomeHeader
        credits={credits}
        onLangToggle={() => {
          const newLang = lang === 'en' ? 'fa' : 'en';
          i18n.changeLanguage(newLang);
          updateLanguage(newLang).catch(console.error);
        }}
        lang={lang}
      />

      <div className="px-4 py-2">
        <h1 className="text-3xl font-title mb-2">{t('Upload Your Art')}</h1>
        <p className="text-sm font-ui text-textSecondary mb-8 leading-relaxed">
          {t('Publish your next track with clean metadata and platform mapping.')}
        </p>

        {/* 1. MP3/WAV */}
        <div className="mb-6 relative">
          <h3 className="text-gold font-ui mb-2">1. {t('Audio File')}</h3>
          <input type="file" accept=".mp3,.wav,audio/mpeg,audio/wav" onChange={e => handleAudioFile(e.target.files?.[0])}
            className="absolute inset-0 opacity-0 cursor-pointer z-10 w-full h-full mt-8" />
          <div className="border border-dashed border-card3 bg-card2/50 rounded-xl p-4 flex items-center hover:bg-card3/20 transition">
            <div className="w-12 h-12 rounded-full border border-gold/50 flex items-center justify-center me-4 flex-shrink-0">
              <Music className="text-gold w-6 h-6" />
            </div>
            <div>
              <p className="font-ui">{audioFile ? audioFile.name : t('Drop audio or choose file')}</p>
              <p className="text-xs font-light-ui text-textSecondary">{t('MP3, WAV')}</p>
            </div>
          </div>
        </div>

        {/* 2. Cover Art */}
        <div className="mb-6 relative">
          <h3 className="text-gold font-ui mb-2">2. {t('Cover Art')}</h3>
          <input type="file" accept=".jpg,.jpeg,.png,.webp,image/jpeg,image/png,image/webp" onChange={e => handleCoverFile(e.target.files?.[0])}
            className="absolute inset-0 opacity-0 cursor-pointer z-10 w-full h-full mt-8" />
          <div className="border border-dashed border-card3 bg-card2/50 rounded-xl p-4 flex items-center hover:bg-card3/20 transition">
            <div className="w-12 h-12 rounded-full border border-gold/50 flex items-center justify-center me-4 flex-shrink-0">
              <ImageIcon className="text-gold w-6 h-6" />
            </div>
            <div>
              <p className="font-ui">{coverFile ? coverFile.name : t('Drop cover art or choose file')}</p>
              <p className="text-xs font-light-ui text-textSecondary">{t('JPG, PNG, WEBP')}</p>
            </div>
          </div>
        </div>

        {/* Form Fields */}
        <div className="space-y-4 mb-6">
          <div>
            <h3 className="text-gold font-ui mb-2 text-sm">3. {t('Song Name')}</h3>
            <div className="bg-inputBg border border-inputBorder rounded-lg p-3 flex items-center">
              <Music className="w-5 h-5 text-textSecondary me-3 flex-shrink-0" />
              <input type="text" value={formData.songName} dir="ltr"
                onChange={e => setFormData(f => ({ ...f, songName: e.target.value }))}
                className="bg-transparent border-none outline-none w-full text-textPrimary font-ui"
                placeholder="Midnight Frequency" />
            </div>
          </div>
          <div>
            <h3 className="text-gold font-ui mb-2 text-sm">4. {t('Artist Name')}</h3>
            <div className="bg-inputBg border border-inputBorder rounded-lg p-3 flex items-center">
              <User className="w-5 h-5 text-textSecondary me-3 flex-shrink-0" />
              <input type="text" value={formData.artistName} dir="ltr"
                onChange={e => setFormData(f => ({ ...f, artistName: e.target.value }))}
                className="bg-transparent border-none outline-none w-full text-textPrimary font-ui"
                placeholder="Arman Vale" />
            </div>
          </div>
          <ProducerTagInput
            producers={formData.producers}
            onChange={producers => setFormData(f => ({ ...f, producers }))}
          />
          <div>
            <h3 className="text-gold font-ui mb-2 text-sm">5. {t('Legal Name')}</h3>
            <div className="bg-inputBg border border-inputBorder rounded-lg p-3 flex items-center">
              <AlignLeft className="w-5 h-5 text-textSecondary me-3 flex-shrink-0" />
              <input type="text" value={formData.legalName} dir="ltr"
                onChange={e => setFormData(f => ({ ...f, legalName: e.target.value }))}
                className="bg-transparent border-none outline-none w-full text-textPrimary font-ui"
                placeholder="Arman V. Rahimi" />
            </div>
          </div>
          <div>
            <h3 className="text-gold font-ui mb-2 text-sm">6. {t('Release Date')}</h3>
            <div className="bg-inputBg border border-inputBorder rounded-lg p-3 flex items-center">
              <Calendar className="w-5 h-5 text-textSecondary me-3 flex-shrink-0" />
              <PersianDatePicker onChange={iso => setFormData(f => ({ ...f, releaseDate: iso }))} />
            </div>
          </div>
          <div className="relative z-40">
            <h3 className="text-gold font-ui mb-2 text-sm">7. {t('Genre')}</h3>
            <GenreSelect
              genre={formData.genre}
              subGenre={formData.subGenre}
              onGenreChange={g => setFormData(f => ({ ...f, genre: g }))}
              onSubGenreChange={s => setFormData(f => ({ ...f, subGenre: s }))}
            />
          </div>
        </div>

        {/* 8. Mapping */}
        <div className="mb-6 relative z-0">
          <h3 className="text-gold font-ui mb-2 text-sm">8. {t('Mapping')}</h3>
          <div className="mb-4">
            <FormToggle
              id="newProfile"
              checked={formData.needsNewProfile}
              onChange={handleToggleProfile}
              label={t("I don't have a profile (Create one for me)")}
            />
          </div>

          {!formData.needsNewProfile ? (
            <div className="space-y-3">
              <div>
                <p className="text-xs font-light-ui text-textSecondary mb-1">{t('Spotify')}</p>
                <div className="bg-inputBg border border-inputBorder rounded-lg p-3 flex items-center">
                  <img src="/Logo/Spotify.png" alt="Spotify" className="w-5 h-5 object-contain me-3 flex-shrink-0" />
                  <input type="text" value={formData.spotifyUrl}
                    onChange={e => setFormData(f => ({ ...f, spotifyUrl: e.target.value }))}
                    dir="ltr"
                    className="bg-transparent border-none outline-none w-full text-textPrimary text-sm font-ui"
                    placeholder="https://open.spotify.com/..." />
                </div>
              </div>
              <div>
                <p className="text-xs font-light-ui text-textSecondary mb-1">{t('Apple Music')}</p>
                <div className="bg-inputBg border border-inputBorder rounded-lg p-3 flex items-center">
                  <img src="/Logo/AppleMusic.png" alt="Apple Music" className="w-5 h-5 object-contain me-3 flex-shrink-0" />
                  <input type="text" value={formData.appleUrl}
                    onChange={e => setFormData(f => ({ ...f, appleUrl: e.target.value }))}
                    dir="ltr"
                    className="bg-transparent border-none outline-none w-full text-textPrimary text-sm font-ui"
                    placeholder="https://music.apple.com/..." />
                </div>
              </div>
            </div>
          ) : (
            <div className="space-y-3 bg-gold/5 border border-gold/20 rounded-xl p-4">
              <p className="text-xs font-ui text-gold mb-2">{t('New profile info needed')}</p>
              <div className="bg-inputBg border border-inputBorder rounded-lg p-3 flex items-center">
                <Mail className="w-5 h-5 text-gold me-3 flex-shrink-0" />
                <input type="email" value={formData.profileEmail}
                  onChange={e => setFormData(f => ({ ...f, profileEmail: e.target.value }))}
                  dir="ltr"
                  className="bg-transparent border-none outline-none w-full text-textPrimary text-sm font-ui"
                  placeholder={t('Profile Email')} />
              </div>
            </div>
          )}
        </div>

        <div className="mb-8 p-4 bg-card1 rounded-xl border border-inputBorder">
          <div className="space-y-3">
            <FormToggle
              id="copyrightRequested"
              checked={formData.copyrightRequested}
              onChange={handleToggleCopyright}
              label={t('Add Copyright Protection (+1 Nitro)')}
              tone="gold"
            />
          </div>
          <NitroCostSummary items={costItems} />
        </div>

        {/* Submit */}
        <div className="pb-8">
          <button
            onClick={handleSubmit}
            disabled={loading}
            className="w-full bg-gradient-to-r from-gold to-[#B8860B] text-background font-title py-4 rounded-xl flex justify-center items-center shadow-lg hover:opacity-90 disabled:opacity-50"
          >
            <span className="text-lg">{loading ? '...' : t("Let's Cook!")}</span>
          </button>
        </div>
      </div>
    </div>
  );
};
