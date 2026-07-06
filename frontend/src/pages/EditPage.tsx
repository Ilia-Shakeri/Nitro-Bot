import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate, useParams } from 'react-router-dom';
import { AlignLeft, Calendar, Image as ImageIcon, Music, User } from 'lucide-react';
import { FormToggle } from '../components/FormToggle';
import { GenreSelect } from '../components/GenreSelect';
import { HomeHeader } from '../components/HomeHeader';
import { NitroCostSummary } from '../components/NitroCostSummary';
import { PersianDatePicker } from '../components/PersianDatePicker';
import { submitRelease, updateLanguage } from '../api';
import { useToast } from '../context/ToastContext';
import { useUser } from '../context/UserContext';

const EDIT_RELEASE_COST = 2;
const COPYRIGHT_COST = 1;

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
    legalName: '',
    releaseDate: '',
    genre: '',
    subGenre: '',
    copyrightRequested: false,
  });
  const [audioFile, setAudioFile] = useState<File | null>(null);
  const [coverFile, setCoverFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);

  const costItems = [
    { label: t('Edit release cost'), amount: EDIT_RELEASE_COST },
    ...(formData.copyrightRequested ? [{ label: t('Copyright protection cost'), amount: COPYRIGHT_COST }] : []),
  ];

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

    setLoading(true);
    try {
      const form = new FormData();
      form.append('audio', audioFile);
      form.append('cover', coverFile);
      form.append('song_name', formData.songName);
      form.append('artist_name', formData.artistName);
      form.append('legal_name', formData.legalName);
      form.append('release_date', formData.releaseDate);
      form.append('genre', formData.genre);
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
      toast(e instanceof Error ? e.message : 'Unknown error', 'error');
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
          <h3 className="text-gold font-ui mb-2">1. MP3/WAV File</h3>
          <input
            type="file"
            accept="audio/*"
            onChange={e => setAudioFile(e.target.files?.[0] ?? null)}
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
          <h3 className="text-gold font-ui mb-2">2. Cover Art</h3>
          <input
            type="file"
            accept="image/*"
            onChange={e => setCoverFile(e.target.files?.[0] ?? null)}
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
          <div>
            <h3 className="text-gold font-ui mb-2 text-sm">5. {t('Legal Name')}</h3>
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
            disabled={loading}
            className="w-full bg-gradient-to-r from-gold to-[#B8860B] text-background font-title py-4 rounded-xl flex justify-center items-center shadow-lg hover:opacity-90 disabled:opacity-50"
          >
            <span className="text-lg">{loading ? '...' : t('Submit Edit')}</span>
          </button>
        </div>
      </div>
    </div>
  );
};
