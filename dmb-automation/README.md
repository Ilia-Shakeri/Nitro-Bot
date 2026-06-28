# 🎵 DMB Automation Worker

اتوماسیون انتشار آلبوم در پلتفرم DMB (Digital Music Business) و پل اتصال آن به مینی‌اپ.

## 📋 توضیحات پروژه

این پروژه با استفاده از **Robot Framework** و **Selenium** فرآیند ایجاد آلبوم در سیستم DMB را
خودکار می‌کند. یک **worker** پایتون نیز ریلیزهای در صف را از API مینی‌اپ می‌گیرد، فایل‌ها را از
MinIO دانلود می‌کند، در دیتابیس SQLite می‌نویسد، اتوماسیون را اجرا می‌کند و وضعیت را برمی‌گرداند.

### ویژگی‌ها

- ✅ دریافت ریلیزهای در صف از API داخلی مینی‌اپ (`/internal/releases/pending`)
- ✅ دانلود فایل صوتی و کاور از MinIO
- ✅ لاگین خودکار به سیستم DMB
- ✅ ایجاد EAN/UPC، آپلود کاور و ترک، تولید ISRC
- ✅ پر کردن metadata (عنوان، ژانر، تاریخ انتشار، کپی‌رایت، Contributor)
- ✅ انتخاب Territory (Worldwide) و گزارش وضعیت به مینی‌اپ

## 📂 ساختار

```
dmb-automation/
├── worker.py              # پل اتصال: poll API → دانلود → SQLite → اجرای Robot → گزارش وضعیت
├── seed_sample_data.py    # (توسعه) درج یک ردیف نمونه برای اجرای دستی Robot
├── automation/
│   └── create_album.robot # سناریوی اصلی ایجاد آلبوم
├── resources/             # page objects, locators, queries, variables (ساختار استاندارد Robot)
├── assets/                # sample_cover.jpg / sample_track.wav (نمونه برای تست دستی)
├── Dockerfile             # Firefox + geckodriver + Xvfb + پایتون
└── requirements.txt
```

## 🚀 اجرا

**در پروداکشن** worker از طریق `docker-compose` (سرویس `dmb-automation`) اجرا می‌شود و به‌صورت
خودکار صف را پردازش می‌کند.

**اجرای دستی سناریو (برای توسعه):**

```bash
python seed_sample_data.py
robot --outputdir results automation/create_album.robot
```

### پیش‌نیازها
- Python 3.11+ و pip
- Mozilla Firefox + geckodriver (در ایمیج داکر از قبل نصب شده‌اند)
- متغیرهای محیطی: `DMB_USERNAME`, `DMB_PASSWORD` و در حالت worker:
  `API_BASE_URL`, `SELENIUM_SECRET_KEY`, `S3_*`
