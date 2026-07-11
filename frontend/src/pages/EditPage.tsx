import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate, useParams } from 'react-router-dom';
import { AlignLeft, Calendar, Image as ImageIcon, Music, User } from 'lucide-react';
import { FormToggle } from '../components/FormToggle';
import { GenreSelect } from '../components/GenreSelect';
import { HomeHeader } from '../components/HomeHeader';
import { NitroCostSummary } from '../components/NitroCostSummary';
import { PersianDatePicker } from '../components/PersianDatePicker';
import { ProducerTagInput } from '../components/ProducerTagInput';
import { getReleases, submitRelease, updateLanguage } from '../api';
import { useToast } from '../context/ToastContext';
import { useUser } from '../context/UserContext';
import { allowedCoverMessage, allowedMusicMessage, errorText } from '../utils/formMessages';

const EDIT_RELEASE_COST = 2;
const COPYRIGHT_COST = 1;

const parseProducers = (raw: string | null) => {
  if (!raw) return [];
  try {
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed.filter(item => typeof item === 'string') : [];
  } catch {
    return [];
  }
};

export const EditPage = () => {
  const { t, i18n } = useTranslation();
  const { id } = useParams();
  const navigate = useNavigate();
  const lang = i18n.language;
  const { user, refreshUser } = useUser();
  const { toast } = useToast();
  const credits = user?.credits ?? 0;
  const isRTL = lang === 'fa';

  const [formData, setFormData] = useState({
    songName: '',
    artistName: '',
    producers: [] as string[],
    legalName: '',
    releaseDate: '',
    genre: '',
    subGenre: '',
    copyrightRequested: false,
  });
  const [audioFile, setAudioFile] = useState<File | null>(null);
  const [coverFile, setCoverFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [prefillLoading, setPrefillLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      const releases = await getReleases();
      const release = releases.find(item => String(item.id) === String(id));
      if (cancelled) return;
      if (!release) {
        toast(t('Source release not found'), 'error');
        setPrefillLoading(false);
        return;
      }
      setFormData({
        songName: release.song_name,
        artistName: release.artist_name,
        producers: parseProducers(release.producers),
        legalName: release.legal_name,
        releaseDate: release.release_date,
        genre: release.genre ?? '',
        subGenre: release.sub_genre ?? '',
        copyrightRequested: false,
      });
      setPrefillLoading(false);
    };
    load();
    return () => { cancelled = true; };
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

  const costItems = [
    { label: t('Edit release cost'), amount: EDIT_RELEASE_COST },
    ...(formData.copyrightRequested ? [{ label: t('Copyright protection cost'), amount: COPYRIGHT_COST }] : []),
  ];

  const handleSubmit = async () => {
    if (!id) {
      toast(t('Edited release id is required'), 'error');
      return;
    }

    setLoading(true);
    try {
      const form = new FormData();
      if (audioFile) form.append('audio', audioFile);
      if (coverFile) form.append('cover', coverFile);
      if (formData.songName) form.append('song_name', formData.songName);
      if (formData.artistName) form.append('artist_name', formData.artistName);
      form.append('producers', JSON.stringify(formData.producers));
      if (formData.legalName) form.append('legal_name', formData.legalName);
      if (formData.releaseDate) form.append('release_date', formData.releaseDate);
      if (formData.genre) form.append('genre', formData.genre);
      if (formData.subGenre) form.append('sub_genre', formData.subGenre);
      if (id) form.append('edited_release_id', id);
      form.append('requires_new_profile', 'false');
      form.append('is_edit', 'true');
      form.append('copyright_requested', formData.copyrightRequested.toString());
      await submitRelease(form);
      await refreshUser();
      toast(t('Edit submitted successfully!'), 'success');
      navigate('/');
    } catch (e: unknown) {
      toast(errorText(e, t), 'error');
    } finally {
      setLoading(false);
    }
  };

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
        <h1 className="text-3xl font-title mb-2">{t('Edit Release')}</h1>
        <p className="text-sm font-ui text-textSecondary mb-8 leading-relaxed">
          {t('Update your release metadata and assets.')}
        </p>

        <div className="mb-6 relative">
          <h3 className="text-gold font-ui mb-2">1. {t('Audio File')}</h3>
          <input
            type="file"
            onChange={e => handleAudioFile(e.target.files?.[0])}
            accept=".mp3,.wav,audio/mpeg,audio/wav"
            className="absolute inset-0 opacity-0 cursor-pointer z-10 w-full h-full mt-8"
          />
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

        <div className="mb-6 relative">
          <h3 className="text-gold font-ui mb-2">2. {t('Cover Art')}</h3>
          <input
            type="file"
            onChange={e => handleCoverFile(e.target.files?.[0])}
            accept=".jpg,.jpeg,.png,.webp,image/jpeg,image/png,image/webp"
            className="absolute inset-0 opacity-0 cursor-pointer z-10 w-full h-full mt-8"
          />
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

        <div className="space-y-4 mb-6 relative z-20">
          <div>
            <h3 className="text-gold font-ui mb-2 text-sm">3. {t('Song Name')}</h3>
            <div className="bg-inputBg border border-inputBorder rounded-lg p-3 flex items-center">
              <Music className="w-5 h-5 text-textSecondary me-3 flex-shrink-0" />
              <input
                type="text"
                value={formData.songName}
                dir="ltr"
                onChange={e => setFormData(f => ({ ...f, songName: e.target.value }))}
                className="bg-transparent border-none outline-none w-full text-textPrimary font-ui"
                placeholder="Midnight Frequency"
              />
            </div>
          </div>
          <div>
            <h3 className="text-gold font-ui mb-2 text-sm">4. {t('Artist Name')}</h3>
            <div className="bg-inputBg border border-inputBorder rounded-lg p-3 flex items-center">
              <User className="w-5 h-5 text-textSecondary me-3 flex-shrink-0" />
              <input
                type="text"
                value={formData.artistName}
                dir="ltr"
                onChange={e => setFormData(f => ({ ...f, artistName: e.target.value }))}
                className="bg-transparent border-none outline-none w-full text-textPrimary font-ui"
                placeholder="Arman Vale"
              />
            </div>
          </div>
          <ProducerTagInput
            labelPrefix="5."
            producers={formData.producers}
            onChange={producers => setFormData(f => ({ ...f, producers }))}
          />
          <div>
            <h3 className="text-gold font-ui mb-2 text-sm">6. {t('Legal Name')}</h3>
            <div className="bg-inputBg border border-inputBorder rounded-lg p-3 flex items-center">
              <AlignLeft className="w-5 h-5 text-textSecondary me-3 flex-shrink-0" />
              <input
                type="text"
                value={formData.legalName}
                dir="ltr"
                onChange={e => setFormData(f => ({ ...f, legalName: e.target.value }))}
                className="bg-transparent border-none outline-none w-full text-textPrimary font-ui"
                placeholder="Arman V. Rahimi"
              />
            </div>
          </div>
          <div>
            <h3 className="text-gold font-ui mb-2 text-sm">7. {t('Release Date')}</h3>
            <div className="bg-inputBg border border-inputBorder rounded-lg p-3 flex items-center">
              <Calendar className="w-5 h-5 text-textSecondary me-3 flex-shrink-0" />
              <PersianDatePicker onChange={iso => setFormData(f => ({ ...f, releaseDate: iso }))} />
            </div>
          </div>
          <div className="relative z-40">
            <h3 className="text-gold font-ui mb-2 text-sm">8. {t('Genre')}</h3>
            <GenreSelect
              genre={formData.genre}
              subGenre={formData.subGenre}
              onGenreChange={g => setFormData(f => ({ ...f, genre: g }))}
              onSubGenreChange={s => setFormData(f => ({ ...f, subGenre: s }))}
            />
          </div>
        </div>

        <div className="mb-8 p-4 bg-card1 rounded-xl border border-inputBorder relative z-0">
          <FormToggle
            id="copyrightRequested"
            checked={formData.copyrightRequested}
            onChange={() => setFormData(f => ({ ...f, copyrightRequested: !f.copyrightRequested }))}
            label={t('Add Copyright Protection (+1 Nitro)')}
            tone="gold"
          />
          <NitroCostSummary items={costItems} />
        </div>

        <div className="pb-8">
          <button
            onClick={handleSubmit}
            disabled={loading || prefillLoading}
            className="w-full bg-gradient-to-r from-gold to-[#B8860B] text-background font-title py-4 rounded-xl flex justify-center items-center shadow-lg hover:opacity-90 disabled:opacity-50"
          >
            <span className="text-lg">{loading ? t('Processing...') : t('Submit Edit')}</span>
          </button>
        </div>
      </div>
    </div>
  );
};
