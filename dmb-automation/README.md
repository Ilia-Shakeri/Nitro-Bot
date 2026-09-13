# 🎵 DMB Automation Worker

اتوماسیون انتشار آلبوم در پلتفرم DMB (Digital Music Business) و پل اتصال آن به مینی‌اپ.

## 📋 توضیحات پروژه

این پروژه با استفاده از **Robot Framework** و **Selenium** فرآیند ایجاد آلبوم در سیستم DMB را
خودکار می‌کند. یک **worker** پایتون نیز ریلیزهای در صف را از API مینی‌اپ می‌گیرد، فایل‌ها را از
MinIO دانلود می‌کند، برای هر سفارش فایل جدا می‌سازد، اتوماسیون را اجرا می‌کند و فقط با مدرک ثبت نهایی وضعیت را برمی‌گرداند.

### ویژگی‌ها

- ✅ دریافت ریلیزهای در صف از API داخلی مینی‌اپ (`/internal/releases/pending`)
- ✅ دانلود فایل صوتی و کاور از MinIO
- ✅ لاگین خودکار به سیستم DMB
- ✅ ایجاد EAN/UPC، آپلود کاور و ترک، تولید ISRC
- ✅ پر کردن عنوان، ژانر، تاریخ انتشار، خطوط کپی‌رایت و Contributor
- ✅ کلیک Save، بررسی پاسخ DMB و ذخیره شناسه‌ها و اسکرین‌شات
- ✅ lease و heartbeat برای برگشت امن کار پس از مرگ worker
- ⛔ مسیر edit تا ساخت و تست جدا، بسته است

## 📂 ساختار

```
dmb-automation/
├── worker.py              # پل اتصال: claim → فایل کار جدا → اجرای Robot → مدرک → گزارش وضعیت
├── libraries/dmb_job.py   # خواندن قرارداد کار و نوشتن نتیجه اتمی
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

شروع زنده فقط وقتی مجاز است که `DMB_CREATE_ENABLED=true` باشد. مقدار پیش‌فرض false است.
`DRY_RUN` هیچ کار زنده را claim نمی‌کند و completed دروغ نمی‌سازد.

**اجرای دستی سناریو (برای توسعه):**

```bash
set DMB_JOB_FILE=C:\path\to\job.json
set DMB_RESULT_FILE=C:\path\to\result.json
set DMB_SUBMIT_ENABLED=true
robot --outputdir results automation/create_album.robot
```

### پیش‌نیازها
- Python 3.11+ و pip
- Mozilla Firefox + geckodriver (در ایمیج داکر از قبل نصب شده‌اند)
- متغیرهای محیطی: `DMB_USERNAME`, `DMB_PASSWORD` و در حالت worker:
  `API_BASE_URL`, `SELENIUM_SECRET_KEY`, `S3_*`, `DMB_CREATE_ENABLED`

فایل‌های SQLite قدیمی فقط برای رجوع مانده‌اند. مسیر زنده آن‌ها را نمی‌خواند.

## بررسی دستی حالت نامعلوم

اگر مرورگر بعد از شروع Save قطع شود، سفارش به `dmb_verification_required` می‌رود و خودکار دوباره
ارسال نمی‌شود. بازبین باید اول DMB و فایل‌های `results/<release_id>` را ببیند، بعد فقط یکی از این
نتیجه‌ها را به API داخلی بفرستد:

- `completed`: همراه شناسه DMB، EAN/UPC، فهرست ISRC و مسیر مدرک
- `retry`: فقط وقتی بازبین مطمئن است رکوردی در DMB ساخته نشده
- `failed`: پایان سفارش و بازپرداخت یک‌باره

درخواست باید هدر `X-DMB-Reviewer-ID` با شناسه ثابت بازبین و کلید جداگانه
`DMB_REVIEW_SECRET_KEY` در هدر Authorization داشته باشد. این کلید به worker داده نمی‌شود.
تصمیم و زمان بازبینی در رکورد سفارش ذخیره می‌شود. فعال‌سازی مسیر create پیش از تست زنده
selectorها مجاز نیست.
