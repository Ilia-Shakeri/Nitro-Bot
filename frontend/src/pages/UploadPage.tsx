import { useState } from "react";
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { HomeHeader } from '../components/HomeHeader';
import { Music, Image as ImageIcon, Calendar, User, AlignLeft, ArrowRight, Sparkles } from 'lucide-react';
import { submitRelease } from '../api';

export const UploadPage = () => {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const lang = i18n.language;

  const [formData, setFormData] = useState({
    songName: '',
    artistName: '',
    legalName: '',
    releaseDate: '',
    spotifyUrl: '',
    appleUrl: '',
    needsNewProfile: false,
    isEdit: false,
    copyrightRequested: false
  });

  const [audioFile, setAudioFile] = useState<File | null>(null);
  const [coverFile, setCoverFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);

  const handleToggleProfile = () => {
    setFormData({ ...formData, needsNewProfile: !formData.needsNewProfile });
  };

  const handleToggleEdit = () => {
    setFormData({ ...formData, isEdit: !formData.isEdit });
  };

  const handleToggleCopyright = () => {
    setFormData({ ...formData, copyrightRequested: !formData.copyrightRequested });
  };

  const handleSubmit = async () => {
    if (!audioFile || !coverFile || !formData.songName || !formData.artistName) {
      alert("Please fill all required fields and upload files.");
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
      if (formData.spotifyUrl) form.append('mapping_spotify', formData.spotifyUrl);
      if (formData.appleUrl) form.append('mapping_apple', formData.appleUrl);
      
      form.append('requires_new_profile', formData.needsNewProfile.toString());
      form.append('is_edit', formData.isEdit.toString());
      form.append('copyright_requested', formData.copyrightRequested.toString());

      await submitRelease(form);
      alert("Release submitted successfully!");
      navigate('/');
    } catch (e: any) {
      alert(e.message);
    } finally {
      setLoading(false);
    }
  };

  const isRTL = lang === 'fa';

  return (
    <div className="min-h-screen bg-background max-w-md mx-auto relative overflow-y-auto font-sans" dir={isRTL ? 'rtl' : 'ltr'}>
      <HomeHeader credits={1240} onLangToggle={() => i18n.changeLanguage(lang === 'en' ? 'fa' : 'en')} lang={lang} />

      <div className="px-4 py-2">
        <div className="flex items-center space-x-2 mb-2">
          <h1 className="text-3xl font-bold">{t('Upload Your Art')}</h1>
          <span className="text-gold text-2xl rtl:mr-2 ltr:ml-2">{'>'}</span>
        </div>
        <p className="text-sm text-textSecondary mb-8 leading-relaxed">
          {t('Publish your next track with clean metadata and platform mapping.')}
        </p>

        {/* 1. MP3/WAV File */}
        <div className="mb-6 relative">
          <h3 className="text-gold font-semibold mb-2">1. MP3/WAV File</h3>
          <input type="file" accept="audio/*" onChange={(e) => setAudioFile(e.target.files?.[0] || null)} className="absolute inset-0 opacity-0 cursor-pointer z-10 w-full h-full mt-8" />
          <div className="border border-dashed border-card3 bg-card2/50 rounded-xl p-4 flex items-center hover:bg-card3/20 transition relative">
            <div className="w-12 h-12 rounded-full border border-gold/50 flex items-center justify-center mr-4 rtl:ml-4">
              <Music className="text-gold w-6 h-6" />
            </div>
            <div>
              <p className="font-semibold">{audioFile ? audioFile.name : t('Drop audio or choose file')}</p>
              <p className="text-xs text-textSecondary">{t('MP3, WAV')}</p>
            </div>
          </div>
        </div>

        {/* 2. Cover Art */}
        <div className="mb-6 relative">
          <h3 className="text-gold font-semibold mb-2">2. Cover Art</h3>
          <input type="file" accept="image/*" onChange={(e) => setCoverFile(e.target.files?.[0] || null)} className="absolute inset-0 opacity-0 cursor-pointer z-10 w-full h-full mt-8" />
          <div className="border border-dashed border-card3 bg-card2/50 rounded-xl p-4 flex items-center hover:bg-card3/20 transition relative">
            <div className="w-12 h-12 rounded-full border border-gold/50 flex items-center justify-center mr-4 rtl:ml-4">
              <ImageIcon className="text-textPrimary w-6 h-6" />
            </div>
            <div>
              <p className="font-semibold">{coverFile ? coverFile.name : t('Drop cover art or choose file')}</p>
              <p className="text-xs text-textSecondary">{t('JPG, PNG, WEBP')}</p>
            </div>
          </div>
        </div>

        {/* Form Fields */}
        <div className="space-y-4 mb-6">
          <div>
            <h3 className="text-gold font-semibold mb-2 text-sm">3. {t('Song Name')}</h3>
            <div className="bg-[#111115] border border-gray-800 rounded-lg p-3 flex items-center">
              <Music className="w-5 h-5 text-gray-500 mr-3 rtl:ml-3" />
              <input type="text" value={formData.songName} onChange={(e) => setFormData({...formData, songName: e.target.value})} className="bg-transparent border-none outline-none w-full text-white placeholder-gray-600" placeholder="Midnight Frequency" />
            </div>
          </div>
          <div>
            <h3 className="text-gold font-semibold mb-2 text-sm">4. {t('Artist Name')}</h3>
            <div className="bg-[#111115] border border-gray-800 rounded-lg p-3 flex items-center">
              <User className="w-5 h-5 text-gray-500 mr-3 rtl:ml-3" />
              <input type="text" value={formData.artistName} onChange={(e) => setFormData({...formData, artistName: e.target.value})} className="bg-transparent border-none outline-none w-full text-white placeholder-gray-600" placeholder="Arman Vale" />
            </div>
          </div>
          <div>
            <h3 className="text-gold font-semibold mb-2 text-sm">5. {t('Legal Name')}</h3>
            <div className="bg-[#111115] border border-gray-800 rounded-lg p-3 flex items-center">
              <AlignLeft className="w-5 h-5 text-gray-500 mr-3 rtl:ml-3" />
              <input type="text" value={formData.legalName} onChange={(e) => setFormData({...formData, legalName: e.target.value})} className="bg-transparent border-none outline-none w-full text-white placeholder-gray-600" placeholder="Arman V. Rahimi" />
            </div>
          </div>
          <div>
            <h3 className="text-gold font-semibold mb-2 text-sm">6. {t('Release Date')}</h3>
            <div className="bg-[#111115] border border-gray-800 rounded-lg p-3 flex items-center justify-between">
              <div className="flex items-center w-full">
                <Calendar className="w-5 h-5 text-gray-500 mr-3 rtl:ml-3" />
                <input type="date" value={formData.releaseDate} onChange={(e) => setFormData({...formData, releaseDate: e.target.value})} className="bg-transparent border-none outline-none w-full text-white placeholder-gray-600 color-scheme-dark" />
              </div>
            </div>
          </div>
        </div>

        {/* 7. Mapping */}
        <div className="mb-6">
          <h3 className="text-gold font-semibold mb-2 text-sm">7. {t('Mapping')}</h3>

          <div className="flex items-center mb-4">
            <input type="checkbox" id="newProfile" checked={formData.needsNewProfile} onChange={handleToggleProfile} className="mr-2 rtl:ml-2 accent-gold w-4 h-4" />
            <label htmlFor="newProfile" className="text-sm cursor-pointer">{t("I don't have a profile (Create one for me)")}</label>
          </div>

          <div className={`space-y-3 transition-opacity ${formData.needsNewProfile ? 'opacity-30 pointer-events-none' : 'opacity-100'}`}>
            <div>
              <p className="text-xs text-textSecondary mb-1 rtl:text-right">{t('Spotify')}</p>
              <div className="bg-[#111115] border border-gray-800 rounded-lg p-3 flex items-center">
                <div className="w-5 h-5 rounded-full bg-green-500 mr-3 rtl:ml-3 flex-shrink-0"></div>
                <input type="text" value={formData.spotifyUrl} onChange={(e) => setFormData({...formData, spotifyUrl: e.target.value})} className="bg-transparent border-none outline-none w-full text-white text-sm placeholder-gray-600" placeholder="https://open.spotify.com/..." disabled={formData.needsNewProfile} />
              </div>
            </div>
            <div>
              <p className="text-xs text-textSecondary mb-1 rtl:text-right">{t('Apple Music')}</p>
              <div className="bg-[#111115] border border-gray-800 rounded-lg p-3 flex items-center">
                <div className="w-5 h-5 rounded-md bg-red-500 mr-3 rtl:ml-3 flex-shrink-0"></div>
                <input type="text" value={formData.appleUrl} onChange={(e) => setFormData({...formData, appleUrl: e.target.value})} className="bg-transparent border-none outline-none w-full text-white text-sm placeholder-gray-600" placeholder="https://music.apple.com/..." disabled={formData.needsNewProfile} />
              </div>
            </div>
          </div>
        </div>

        {/* 8. Additional Options */}
        <div className="mb-8 p-4 bg-card1 rounded-xl border border-gray-800">
          <div className="flex items-center mb-3">
            <input type="checkbox" id="isEdit" checked={formData.isEdit} onChange={handleToggleEdit} className="mr-2 rtl:ml-2 accent-gold w-4 h-4" />
            <label htmlFor="isEdit" className="text-sm cursor-pointer">{t("Edit Previous Release (1 Nitro)")}</label>
          </div>
          <div className="flex items-center">
            <input type="checkbox" id="copyrightRequested" checked={formData.copyrightRequested} onChange={handleToggleCopyright} className="mr-2 rtl:ml-2 accent-gold w-4 h-4" />
            <label htmlFor="copyrightRequested" className="text-sm cursor-pointer text-gold">{t("Add Copyright Protection (+2 Nitro)")}</label>
          </div>
        </div>

        {/* Submit Button */}
        <div className="pb-8">
          <button
            onClick={handleSubmit}
            disabled={loading}
            className="w-full bg-gradient-to-r from-gold to-[#B8860B] text-background font-bold py-4 rounded-xl flex justify-between items-center shadow-lg hover:opacity-90 px-6 disabled:opacity-50"
          >
            <Sparkles className="w-5 h-5" />
            <span className="text-lg">{loading ? 'Cooking...' : t("Let's Cook!")}</span>
            <ArrowRight className="w-5 h-5 rtl:rotate-180" />
          </button>
        </div>

      </div>
    </div>
  );
};