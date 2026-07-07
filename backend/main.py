import asyncio
import logging
import os
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import storage
from bot import bot, configure_menu_button, dp
from middleware import RateLimitMiddleware
from routers import internal, releases, transactions, users, support

_MINI_APP_URL = os.getenv("MINI_APP_URL", "https://nitrobot.duckdns.org")
logger = logging.getLogger("nitro.bot")


async def _run_polling() -> None:
    """Long-poll Telegram with auto-restart on network errors."""
    await bot.delete_webhook(drop_pending_updates=True)
    while True:
        try:
            await dp.start_polling(bot, handle_signals=False)
            return
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Polling crashed; restarting in 5s")
            await asyncio.sleep(5)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await storage.ensure_bucket()
    try:
        await configure_menu_button()
    except Exception:
        logger.exception("Failed to update Mini App menu button")
    polling_task = asyncio.create_task(_run_polling())
    yield
    polling_task.cancel()
    with suppress(asyncio.CancelledError):
        await polling_task
    await bot.session.close()


app = FastAPI(title="Nitro Bot API", lifespan=lifespan)

app.add_middleware(RateLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[_MINI_APP_URL, "http://localhost:5173", "http://localhost"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router)
app.include_router(releases.router)
app.include_router(transactions.router)
app.include_router(internal.router)
app.include_router(support.router)
