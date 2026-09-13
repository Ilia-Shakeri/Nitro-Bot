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
- ✅ ساخت کاور JPG دقیق `3000x3000` و رد فایل صوتی غیر WAV
- ✅ پر کردن عنوان، Language انگلیسی، ژانر DMB، Label ثابت `Mitrxv` و تاریخ‌ها
- ✅ انتخاب Price Codeهای `MA` و `Digital 45`
- ✅ سال C بر پایه انتشار اصلی و سال P بر پایه سال جاری
- ✅ Contributor حساب‌دار از نتیجه DMB و Contributor جدید فقط با نقش Performer
- ✅ انتخاب Worldwide، همه پلتفرم‌ها و بررسی داده‌ها پیش از Save
- ✅ کلیک Save، بررسی پاسخ DMB و ذخیره شناسه‌ها و اسکرین‌شات
- ✅ lease و heartbeat برای برگشت امن کار پس از مرگ worker
- ✅ circuit breaker پایدار؛ سه خطای پیاپی یا یک نتیجه نامعلوم، claim تازه را می‌بندد
- ⛔ مسیر edit تا ساخت و تست جدا، بسته است

## 📂 ساختار

```
dmb-automation/
├── worker.py              # پل اتصال: claim → فایل کار جدا → اجرای Robot → مدرک → گزارش وضعیت
├── dmb_contract.py        # تبدیل داده مینی‌اپ به مقدارهای دقیق DMB
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

راه اصلی، اجرای headless روی VPS خارجی است. این راه صف، lease، restart و مدرک پایدار دارد.
اجرای یک‌ساعته با shortcut لپ‌تاپ فقط راه اضطراری است؛ خاموشی، sleep، اینترنت ناپایدار و قطع
مرورگر وسط Save، ریسک بیشتری می‌سازد.

PostgreSQL و MinIO منبع اصلی داده‌اند. DMB worker دیتابیس SQLite جدا و ناسازگار نمی‌سازد.
اطلاعات سفارش در PostgreSQL و فایل‌ها در MinIO می‌مانند. فقط قرارداد موقت هر job روی worker
ساخته و پس از پایان پاک می‌شود. مدرک‌ها در `dmb-results` پایدار می‌مانند.

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

## ترتیب create

1. ورود، Music، Create album، انتخاب `(Maxi-) Single`.
2. Generate EAN، کاور JPG، Title، English، ژانر تبدیل‌شده به متن DMB.
3. Label برابر `Mitrxv`، Digital release، Expiration برابر `2099-12-31`.
4. Price Code برابر `MA` و iTunes برابر `45`.
5. C line و P line با Label برابر `Mitrxv`.
6. افزودن Contributorها با قرارداد حساب‌دار یا Performer جدید.
7. Next، Add Tracks، فایل WAV، Title و Generate ISRC.
8. Worldwide، Next، دکمه `<<` برای همه پلتفرم‌ها، Next.
9. بررسی Title، EAN، ISRC، تاریخ، ژانر، Label و Contributorها.
10. نوشتن checkpoint، سپس `Save & View Audio Product`.
11. ذخیره DMB ID، EAN، ISRC، URL و اسکرین‌شات PNG معتبر.

## circuit breaker

فایل `results/dmb-circuit.json` وضعیت حفاظ را نگه می‌دارد. سه خطای پیاپی قبل Save، حفاظ را
باز می‌کند. خطا بعد شروع Save یا شکست گزارش به API، حفاظ را همان بار اول باز می‌کند. تا بازبین
صفحه DMB و سفارش نامعلوم را نبیند، این فایل نباید پاک یا جابه‌جا شود. پس از رفع selector یا
تأیید وضعیت سفارش، اپراتور فایل را آرشیو می‌کند و worker دوباره claim می‌گیرد.

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
