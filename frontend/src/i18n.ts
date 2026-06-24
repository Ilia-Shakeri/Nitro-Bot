import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

const resources = {
  en: {
    translation: {
      "My Music": "My Music",
      "Ordered by your most listened tracks": "Ordered by your most listened tracks",
      "Drop Your Art": "Drop Your Art",
      "Upload audio, tracks or artwork": "Upload audio, tracks or artwork",
      "Nitro": "Nitro",
      "Refill your credits and keep creating music.": "Refill your credits and keep creating music.",
      "Balance": "Balance: {{balance}}",
      "Refill Nitro": "Refill Nitro",
      "Upload Your Art": "Upload Your Art",
      "Publish your next track with clean metadata and platform mapping.": "Publish your next track with clean metadata and platform mapping.",
      "Drop audio or choose file": "Drop audio or choose file",
      "Drop cover art or choose file": "Drop cover art or choose file",
      "MP3, WAV": "MP3, WAV",
      "JPG, PNG, WEBP": "JPG, PNG, WEBP",
      "Song Name": "Song Name",
      "Artist Name": "Artist Name",
      "Legal Name": "Legal Name",
      "Release Date": "Release Date",
      "Mapping": "Mapping",
      "Spotify": "Spotify",
      "Apple Music": "Apple Music",
      "Let's Cook!": "Let's Cook!",
      "I don't have a profile (Create one for me)": "I don't have a profile (Create one for me)",
      "Credits": "Credits",
      "Edit Previous Release (1 Nitro)": "Edit Previous Release (1 Nitro)",
      "Add Copyright Protection (+2 Nitro)": "Add Copyright Protection (+2 Nitro)",
      "Payment Method": "Payment Method",
      "Card to Card": "Card to Card",
      "Tether (USDT)": "Tether (USDT)",
      "Submit Receipt": "Submit Receipt"
    }
  },
  fa: {
    translation: {
      "My Music": "موزیک‌های من",
      "Ordered by your most listened tracks": "مرتب شده بر اساس بیشترین شنیده شده",
      "Drop Your Art": "هنرت رو بنداز",
      "Upload audio, tracks or artwork": "آپلود صدا، ترک‌ها یا آثار هنری",
      "Nitro": "نیترو",
      "Refill your credits and keep creating music.": "نیترو هاتو بیشتر کن",
      "Balance": "موجودی: {{balance}}",
      "Refill Nitro": "شارژ نیترو",
      "Upload Your Art": "آپلود هنر شما",
      "Publish your next track with clean metadata and platform mapping.": "ترک بعدی خود را با متادیتا و مپینگ پلتفرم‌ها منتشر کنید.",
      "Drop audio or choose file": "صدا را رها کنید یا فایل را انتخاب کنید",
      "Drop cover art or choose file": "کاور را رها کنید یا فایل را انتخاب کنید",
      "MP3, WAV": "MP3, WAV",
      "JPG, PNG, WEBP": "JPG, PNG, WEBP",
      "Song Name": "نام آهنگ",
      "Artist Name": "نام هنرمند",
      "Legal Name": "نام قانونی",
      "Release Date": "تاریخ انتشار",
      "Mapping": "مپینگ (لینک‌ها)",
      "Spotify": "اسپاتیفای",
      "Apple Music": "اپل موزیک",
      "Let's Cook!": "بزن بریم!",
      "I don't have a profile (Create one for me)": "پروفایل ندارم (برام بسازید)",
      "Credits": "اعتبار",
      "Edit Previous Release (1 Nitro)": "ویرایش ریلیز قبلی (۱ نیترو)",
      "Add Copyright Protection (+2 Nitro)": "اضافه کردن کپی رایت (+۲ نیترو)",
      "Payment Method": "روش پرداخت",
      "Card to Card": "کارت به کارت",
      "Tether (USDT)": "تتر (USDT)",
      "Submit Receipt": "ثبت رسید"
    }
  }
};

i18n
  .use(initReactI18next)
  .init({
    resources,
    lng: "fa", 
    fallbackLng: "en",
    interpolation: {
      escapeValue: false
    }
  });

export default i18n;