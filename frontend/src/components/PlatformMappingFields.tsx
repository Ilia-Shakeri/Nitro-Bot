import { Mail } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { FormToggle } from './FormToggle';
import { ReleaseField } from './ReleaseField';

interface Props {
  needsNewProfile: boolean;
  onNeedsNewProfileChange: (value: boolean) => void;
  profileEmail: string;
  onProfileEmailChange: (value: string) => void;
  spotifyUrl: string;
  onSpotifyUrlChange: (value: string) => void;
  appleUrl: string;
  onAppleUrlChange: (value: string) => void;
}

const PlatformLogo = ({ src, alt }: { src: string; alt: string }) => (
  <img src={src} alt={alt} className="h-5 w-5 object-contain" width="20" height="20" />
);

export const PlatformMappingFields = ({
  needsNewProfile,
  onNeedsNewProfileChange,
  profileEmail,
  onProfileEmailChange,
  spotifyUrl,
  onSpotifyUrlChange,
  appleUrl,
  onAppleUrlChange,
}: Props) => {
  const { t } = useTranslation();
  return (
    <section className="mb-6">
      <h3 className="mb-2 text-start text-sm font-ui text-gold">9. {t('Mapping')}</h3>
      <div className="mb-4">
        <FormToggle
          id="newProfile"
          checked={needsNewProfile}
          onChange={() => onNeedsNewProfileChange(!needsNewProfile)}
          label={t("I don't have a profile (Create one for me)")}
        />
      </div>
      {!needsNewProfile ? (
        <div className="space-y-3">
          <ReleaseField
            id="spotify-url"
            label={t('Spotify')}
            icon={<PlatformLogo src="/Logo/Spotify.webp" alt={t('Spotify logo')} />}
          >
            <input
              id="spotify-url"
              type="url"
              value={spotifyUrl}
              onChange={event => onSpotifyUrlChange(event.target.value)}
              dir="ltr"
              inputMode="url"
              className="w-full bg-transparent text-start text-sm text-textPrimary outline-none"
              placeholder="https://open.spotify.com/..."
            />
          </ReleaseField>
          <ReleaseField
            id="apple-url"
            label={t('Apple Music')}
            icon={<PlatformLogo src="/Logo/AppleMusic.webp" alt={t('Apple Music logo')} />}
          >
            <input
              id="apple-url"
              type="url"
              value={appleUrl}
              onChange={event => onAppleUrlChange(event.target.value)}
              dir="ltr"
              inputMode="url"
              className="w-full bg-transparent text-start text-sm text-textPrimary outline-none"
              placeholder="https://music.apple.com/..."
            />
          </ReleaseField>
        </div>
      ) : (
        <div className="rounded-xl border border-gold/20 bg-gold/5 p-4">
          <p className="mb-3 text-start text-xs font-ui text-gold">{t('New profile info needed')}</p>
          <ReleaseField id="profile-email" label={t('Profile Email')} required icon={<Mail className="h-5 w-5" />}>
            <input
              id="profile-email"
              type="email"
              value={profileEmail}
              onChange={event => onProfileEmailChange(event.target.value)}
              dir="ltr"
              inputMode="email"
              className="w-full bg-transparent text-start text-sm text-textPrimary outline-none"
              placeholder={t('Profile Email')}
            />
          </ReleaseField>
        </div>
      )}
    </section>
  );
};
