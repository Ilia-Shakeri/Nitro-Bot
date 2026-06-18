# 🎵 Nitro Bot — Premium Music Distribution Mini-App

Nitro Bot is a production-ready Telegram Mini-App and Bot platform designed for high-end music creators. It provides a seamless, mobile-first interface for artists to upload tracks (MP3/WAV), cover art, and metadata for distribution (integrating with DMB Kontor). The platform features a native wallet system ("Nitro Credits"), manual receipt approvals via Telegram, and full bilingual support (Persian/English).

## ✨ Key Features

* **Telegram Mini-App UI:** A premium, dark-themed, mobile-first interface built with React and Tailwind CSS.
* **Track Uploads & Metadata:** Direct-to-S3 uploading for audio files and cover art with comprehensive metadata tagging (Spotify/Apple Music mapping).
* **Nitro Credit System:** Internal currency wallet for releasing tracks and managing copyrights.
* **Automated Admin Approvals:** Users upload transfer receipts, which are securely forwarded to an Admin Telegram Group with inline `Approve/Reject` buttons.
* **Secure Object Storage:** Integrated MinIO (S3-compatible) storage for assets, ensuring the app remains stateless and scalable.
* **Bilingual (i18n):** Full support for Persian (RTL) and English (LTR) across both the Mini-App UI and Telegram Bot notifications.
* **Production Infrastructure:** Fully containerized with Docker Compose, utilizing Nginx and Caddy for automated HTTPS/SSL termination.

## 🛠 Tech Stack

**Frontend (Mini-App)**
* React 19 + TypeScript
* Vite
* Tailwind CSS (v4)
* `@twa-dev/sdk` (Telegram WebApp Integration)
* `react-i18next` (Localization)

**Backend (API & Bot)**
* Python 3.11
* FastAPI (REST API)
* Aiogram v3.x (Asynchronous Telegram Bot)
* SQLAlchemy 2.0 + Asyncpg (PostgreSQL ORM)
* Boto3 (S3/MinIO Integration)
* Alembic (Database Migrations)

**Infrastructure & DevOps**
* Docker & Docker Compose
* PostgreSQL 15
* MinIO (Object Storage)
* Nginx (Frontend static serving)
* Caddy (Reverse Proxy & Auto Let's Encrypt SSL)

## 📂 Project Structure

```text
Nitro-Bot/
├── backend/                  # Python FastAPI & Aiogram
│   ├── alembic/              # Database migration scripts
│   ├── bot.py                # Telegram Bot handlers & logic
│   ├── main.py               # FastAPI application & endpoints
│   ├── models.py             # SQLAlchemy database models
│   ├── requirements.txt      
│   ├── alembic.ini
│   └── Dockerfile
├── frontend/                 # React + Vite Telegram Mini App
│   ├── src/
│   │   ├── components/       # UI Components (Header, Sliders, Cards)
│   │   ├── pages/            # View components (Home, Upload)
│   │   ├── api.ts            # Backend API communication
│   │   ├── i18n.ts           # Translation configuration
│   │   └── main.tsx          # App entry point
│   ├── nginx.conf            # Nginx routing configuration
│   ├── package.json
│   ├── tailwind.config.js
│   └── Dockerfile
├── docker-compose.yml        # Multi-container orchestration
├── Caddyfile                 # SSL and Reverse Proxy configuration
└── .env                      # Environment variables (Do not commit)
```


## 🚀 Deployment & Installation

### 1. Prerequisites

* A Linux server/VPS (tested on IP: `2.58.172.239`).
* Docker and Docker Compose installed.
* A domain pointed to your server's IP (e.g., `nitrobot.duckdns.org`).
* A Telegram Bot Token from [@BotFather](https://t.me/BotFather).

### 2. Environment Variables

Create a `.env` file in the root directory:

```env
# Telegram Configuration
BOT_TOKEN=your_telegram_bot_token_here
ADMIN_GROUP_ID=-100XXXXXXXXXX
MINI_APP_URL=[https://nitrobot.duckdns.org](https://nitrobot.duckdns.org)

# Database Configuration (Used internally by Docker)
DATABASE_URL=postgresql+asyncpg://user:password@db/nitrodb
POSTGRES_USER=user
POSTGRES_PASSWORD=password
POSTGRES_DB=nitrodb

# MinIO / S3 Configuration
S3_ENDPOINT=http://minio:9000
S3_ACCESS_KEY=admin
S3_SECRET_KEY=password123
```

### 3. Caddyfile Configuration

Ensure your `Caddyfile` in the root directory is configured for your domain:

```text
nitrobot.duckdns.org {
    encode zstd gzip

    handle /users* { reverse_proxy backend:8000 }
    handle /releases* { reverse_proxy backend:8000 }
    handle /transactions* { reverse_proxy backend:8000 }

    handle { reverse_proxy frontend:80 }
}
```

### 4. Build and Run

Start the entire stack using Docker Compose:

```bash
docker-compose up -d --build
```

This command will:

1. Provision the PostgreSQL database.
2. Start the MinIO storage server.
3. Build and launch the FastAPI backend + Aiogram Bot.
4. Build the React app and serve it via Nginx.
5. Provision Let's Encrypt SSL certificates and route traffic via Caddy.

### 5. Database Migrations

Once the containers are running, apply the initial database schema:

```bash
docker-compose exec backend alembic upgrade head
```

## 🤖 Bot Workflows

1. **Initialization:** User sends `/start` to the bot.
2. **Mini-App Access:** Bot replies with an inline button to open the WebApp.
3. **Purchasing Nitro:** * User transfers funds (Card-to-Card or Tether).
* User uploads the receipt via the Mini-App.
* Backend generates a secure, expiring S3 link for the receipt.
* Bot forwards the receipt to the `ADMIN_GROUP_ID` with inline `Approve/Reject` buttons.
* Admin clicks `Approve`, backend updates user's PostgreSQL balance, and notifies the user in their preferred language.


4. **Track Release:** User submits a track (10 Nitro). Audio/Cover files stream asynchronously to MinIO to prevent event loop blocking.

## 🌐 Localization (i18n)

The project natively supports English (`en`) and Persian (`fa`).

* **Frontend:** Managed via `i18next` in `frontend/src/i18n.ts`. Changes are saved to the backend database.
* **Backend:** Handled via the `TRANSLATIONS` dictionary in `backend/bot.py`.