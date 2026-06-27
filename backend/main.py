import asyncio
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import storage
from bot import bot, dp
from middleware import RateLimitMiddleware
from routers import internal, releases, transactions, users

_MINI_APP_URL = os.getenv("MINI_APP_URL", "https://nitrobot.duckdns.org")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await storage.ensure_bucket()
    polling_task = asyncio.create_task(dp.start_polling(bot))
    yield
    polling_task.cancel()
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
