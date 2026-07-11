import os
import re
import json
import logging
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from aiogram import Bot, Dispatcher, F, types
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, ForceReply
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.future import select

from database import AsyncSessionLocal
from models import User, Transaction, SupportMessage, SupportTicket, get_naive_utc

BOT_TOKEN = os.getenv("BOT_TOKEN", "REPLACE_WITH_YOUR_TOKEN")
ADMIN_GROUP_ID = os.getenv("ADMIN_GROUP_ID", "-1000000000")
APP_VERSION = os.getenv("APP_VERSION", "2026-07-06-producers-convert-v5")
logger = logging.getLogger("nitro.bot")


def _topic(env_name: str) -> int | None:
    """Parse a forum topic id. Empty means the General topic."""
    raw = os.getenv(env_name, "").strip()
    return int(raw) if raw else None


ORDER_TOPIC_ID = _topic("ORDER_TOPIC_ID")
TICKET_TOPIC_ID = _topic("TICKET_TOPIC_ID")
PAYMENT_TOPIC_ID = _topic("PAYMENT_TOPIC_ID")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

_ANSWER_MARKER = "[answer:{ticket_id}:{tg_id}]"
_ANSWER_RE = re.compile(r"\[answer:(\d+):(\d+)\]")

_TRANSLATIONS = {
    "en": {
        "welcome": "Welcome to Nitro Bot!\nLaunch the Mini App to start.",
        "tx_approved": "Your receipt for {} Nitro has been approved!\nCredits added.",
        "tx_rejected": "Your receipt for {} Nitro was rejected.\nPlease contact support.",
        "ticket_reply": "Support reply:\n\n{}",
    },
    "fa": {
        "welcome": "به ربات نیترو خوش آمدید!\nمینی اپ را باز کنید.",
        "tx_approved": "رسید شما برای {} نیترو تایید شد!\nاعتبار اضافه شد.",
        "tx_rejected": "رسید شما برای {} نیترو رد شد.\nلطفا با پشتیبانی تماس بگیرید.",
        "ticket_reply": "پاسخ پشتیبانی:\n\n{}",
    },
}


def _is_missing_message_thread(exc: TelegramBadRequest) -> bool:
    return "message thread not found" in str(exc).lower()


async def _send_with_thread_fallback(method_name: str, **kwargs: Any) -> Any:
    chat_id = kwargs.get("chat_id")
    message_thread_id = kwargs.get("message_thread_id")
    logger.info(
        "Telegram %s call chat_id=%s message_thread_id=%s",
        method_name,
        chat_id,
        message_thread_id,
    )
    send_method = getattr(bot, method_name)
    try:
        return await send_method(**kwargs)
    except TelegramBadRequest as exc:
        if not _is_missing_message_thread(exc) or message_thread_id is None:
            raise
        fallback_kwargs = {**kwargs, "message_thread_id": None}
        logger.info(
            "Telegram %s missing thread for chat_id=%s message_thread_id=%s; retrying with message_thread_id=None",
            method_name,
            chat_id,
            message_thread_id,
            exc_info=True,
        )
        try:
            return await send_method(**fallback_kwargs)
        except Exception:
            logger.exception(
                "Telegram %s fallback failed for chat_id=%s message_thread_id=None",
                method_name,
                chat_id,
            )
            raise


async def _send_message(**kwargs: Any) -> Any:
    return await _send_with_thread_fallback("send_message", **kwargs)


async def _send_photo(**kwargs: Any) -> Any:
    return await _send_with_thread_fallback("send_photo", **kwargs)


async def _send_document(**kwargs: Any) -> Any:
    return await _send_with_thread_fallback("send_document", **kwargs)


async def _send_audio(**kwargs: Any) -> Any:
    return await _send_with_thread_fallback("send_audio", **kwargs)


async def _send_media_group(**kwargs: Any) -> Any:
    return await _send_with_thread_fallback("send_media_group", **kwargs)


def _mini_app_url() -> str:
    """Return the Mini App URL with a deploy version to bypass Telegram webview cache."""
    raw = os.getenv("MINI_APP_URL", "https://example.com").strip()
    parts = urlsplit(raw)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    query["v"] = APP_VERSION
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


async def configure_menu_button() -> None:
    """Update the persistent Telegram menu button to the current Mini App URL."""
    await bot.set_chat_menu_button(
        menu_button=types.MenuButtonWebApp(
            text="Open Mini App",
            web_app=types.WebAppInfo(url=_mini_app_url()),
        )
    )


async def _user_lang(tg_id: int) -> str:
    """Look up user language preference, default to Farsi if not found."""
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(User).where(User.telegram_id == tg_id))
        user = res.scalars().first()
    lang = user.language_preference if user else "fa"
    return lang if lang in _TRANSLATIONS else "fa"


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.telegram_id == message.from_user.id))
        user = result.scalars().first()
        if not user:
            user = User(
                telegram_id=message.from_user.id,
                username=message.from_user.username,
                first_name=message.from_user.first_name,
                language_preference="fa",
                credits=0,
            )
            db.add(user)
            await db.commit()
        lang = user.language_preference

    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(
            text="Open Mini App",
            web_app=types.WebAppInfo(url=_mini_app_url()),
        )
    )
    await message.answer(_TRANSLATIONS[lang]["welcome"], reply_markup=builder.as_markup())


@dp.message(Command("version"))
async def cmd_version(message: types.Message):
    await message.answer(f"Mini App version: {APP_VERSION}\n{_mini_app_url()}")


async def notify_admin_new_ticket(ticket_id: int, tg_id: int, name: str, username: str, subject: str, message: str):
    subj_line = f"Subject: {subject}\n" if subject else ""
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(text="Answer", callback_data=f"ticket_answer_{ticket_id}_{tg_id}"),
    )
    await _send_message(
        chat_id=ADMIN_GROUP_ID,
        message_thread_id=TICKET_TOPIC_ID,
        text=(
            f"New Support Ticket\n"
            f"Ticket ID: {ticket_id}\n"
            f"From: {name} ({username}) [ID:{tg_id}]\n"
            f"{subj_line}"
            f"\n{message}"
        ),
        reply_markup=builder.as_markup(),
    )


async def notify_admin_new_receipt(
    tx_id: int,
    amount: int,
    payment_method: str,
    submitter: str,
    receipt_bytes: bytes,
    receipt_filename: str,
):
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(text="Approve", callback_data=f"tx_approve_{tx_id}"),
        types.InlineKeyboardButton(text="Reject", callback_data=f"tx_reject_{tx_id}"),
    )
    caption = (
        f"New Payment Receipt\n"
        f"Transaction ID: {tx_id}\n"
        f"From: {submitter}\n"
        f"Method: {payment_method.upper()}\n"
        f"Amount: {amount} Nitro"
    )
    photo = BufferedInputFile(receipt_bytes, filename=receipt_filename)
    try:
        await _send_photo(
            chat_id=ADMIN_GROUP_ID,
            message_thread_id=PAYMENT_TOPIC_ID,
            photo=photo,
            caption=caption,
            reply_markup=builder.as_markup(),
        )
    except Exception:
        logger.error("Failed to send receipt %s as photo; trying document", tx_id, exc_info=True)
        try:
            await _send_document(
                chat_id=ADMIN_GROUP_ID,
                message_thread_id=PAYMENT_TOPIC_ID,
                document=BufferedInputFile(receipt_bytes, filename=receipt_filename),
                caption=caption,
                reply_markup=builder.as_markup(),
            )
        except Exception:
            logger.error("Failed to send receipt %s document to Telegram payment topic", tx_id, exc_info=True)
            raise


async def notify_admin_new_release(
    release_id: int,
    song_name: str,
    artist_name: str,
    producers: str | None,
    legal_name: str,
    genre: str,
    sub_genre: str | None,
    release_date: str,
    mapping_spotify: str | None,
    mapping_apple: str | None,
    requires_new_profile: bool,
    profile_email: str | None,
    is_edit: bool,
    copyright_requested: bool,
    cost: int,
    submitter: str,
    audio_bytes: bytes | None,
    audio_filename: str | None,
    cover_bytes: bytes | None,
    cover_filename: str | None,
):
    # Format the producer list for the caption
    producer_text = "-"
    if producers:
        try:
            parsed = json.loads(producers)
            if isinstance(parsed, list) and parsed:
                producer_text = ", ".join(str(item) for item in parsed)
        except Exception:
            producer_text = producers

    # Build the caption text
    caption = (
        f"New Release (Staging)\n"
        f"Release ID: {release_id}\n"
        f"From: {submitter}\n"
        f"Song: {song_name}\n"
        f"Artist: {artist_name}\n"
        f"Legal name: {legal_name}\n"
        f"Producers: {producer_text}\n"
        f"Genre: {genre}\n"
        f"Subgenre: {sub_genre or '-'}\n"
        f"Release date: {release_date}\n"
        f"Spotify: {mapping_spotify or '-'}\n"
        f"Apple Music: {mapping_apple or '-'}\n"
        f"New profile: {'yes' if requires_new_profile else 'no'}\n"
        f"Profile email: {profile_email or '-'}\n"
        f"Edit order: {'yes' if is_edit else 'no'}\n"
        f"Copyright: {'yes' if copyright_requested else 'no'}\n"
        f"Cost: {cost} Nitro"
    )

    # Handle cases where no media was uploaded
    if not audio_bytes and not cover_bytes:
        await _send_message(
            chat_id=ADMIN_GROUP_ID,
            message_thread_id=ORDER_TOPIC_ID,
            text=caption + "\nMedia: unchanged from source release",
        )
        return

    try:
        # Send a single audio message and attach the cover as a thumbnail
        if audio_bytes and audio_filename:
            await _send_audio(
                chat_id=ADMIN_GROUP_ID,
                message_thread_id=ORDER_TOPIC_ID,
                audio=BufferedInputFile(audio_bytes, filename=audio_filename),
                thumbnail=BufferedInputFile(cover_bytes, filename=cover_filename) if cover_bytes else None,
                caption=caption,
            )
            if cover_bytes and cover_filename:
                try:
                    await _send_photo(
                        chat_id=ADMIN_GROUP_ID,
                        message_thread_id=ORDER_TOPIC_ID,
                        photo=BufferedInputFile(cover_bytes, filename=cover_filename),
                        caption=f"Cover for release ID: {release_id}",
                    )
                except Exception:
                    logger.error("Failed to send release %s cover photo", release_id, exc_info=True)
                    await _send_document(
                        chat_id=ADMIN_GROUP_ID,
                        message_thread_id=ORDER_TOPIC_ID,
                        document=BufferedInputFile(cover_bytes, filename=cover_filename),
                        caption=f"Cover for release ID: {release_id}",
                    )
            return

        # Fallback if only the cover image exists
        if cover_bytes and cover_filename:
            await _send_photo(
                chat_id=ADMIN_GROUP_ID,
                message_thread_id=ORDER_TOPIC_ID,
                photo=BufferedInputFile(cover_bytes, filename=cover_filename),
                caption=caption,
            )
            return

    except Exception:
        logger.error("Failed to send release %s media to Telegram order topic", release_id, exc_info=True)
        fallback_data = audio_bytes or cover_bytes
        fallback_name = audio_filename or cover_filename or "release.bin"
        if fallback_data:
            try:
                await _send_document(
                    chat_id=ADMIN_GROUP_ID,
                    message_thread_id=ORDER_TOPIC_ID,
                    document=BufferedInputFile(fallback_data, filename=fallback_name),
                    caption=caption + "\nMedia upload failed - files unavailable",
                )
            except Exception:
                logger.error("Fallback release %s document send failed", release_id, exc_info=True)
                raise

async def _append_status(message: types.Message, suffix: str) -> None:
    """Append a status line to a group message when Telegram allows editing."""
    try:
        if message.caption is not None:
            await message.edit_caption(caption=message.caption + suffix)
        elif message.text is not None:
            await message.edit_text(message.text + suffix)
    except Exception:
        pass


@dp.callback_query(F.data.startswith("tx_"))
async def handle_tx_decision(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    action, tx_id = parts[1], int(parts[2])

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Transaction).where(Transaction.id == tx_id))
        tx = result.scalars().first()

        if not tx or tx.status != "pending":
            await callback.answer("Transaction already processed or not found.")
            return

        user_res = await db.execute(select(User).where(User.telegram_id == tx.user_id))
        user = user_res.scalars().first()
        lang = user.language_preference if user else "fa"

        if action == "approve":
            tx.status = "approved"
            if user:
                user.credits += tx.amount
            await db.commit()
            await _send_message(chat_id=tx.user_id, text=_TRANSLATIONS[lang]["tx_approved"].format(tx.amount))
            await _append_status(callback.message, "\n\nStatus: APPROVED")

        elif action == "reject":
            tx.status = "rejected"
            await db.commit()
            await _send_message(chat_id=tx.user_id, text=_TRANSLATIONS[lang]["tx_rejected"].format(tx.amount))
            await _append_status(callback.message, "\n\nStatus: REJECTED")

    await callback.answer()


@dp.callback_query(F.data.startswith("ticket_answer_"))
async def handle_ticket_answer(callback: types.CallbackQuery):
    """Prompt an admin reply and tag the target ticket and user."""
    _, _, ticket_id, tg_id = callback.data.split("_")
    await _send_message(
        chat_id=ADMIN_GROUP_ID,
        message_thread_id=TICKET_TOPIC_ID,
        text=(
            "Reply to this message with your answer.\n"
            f"{_ANSWER_MARKER.format(ticket_id=int(ticket_id), tg_id=int(tg_id))}"
        ),
        reply_markup=ForceReply(selective=False),
    )
    await callback.answer("Reply to the prompt to answer the user.")


@dp.message(F.reply_to_message)
async def handle_admin_reply(message: types.Message):
    """Relay an admin answer to the user and save it in ticket history."""
    if str(message.chat.id) != str(ADMIN_GROUP_ID):
        return
    replied_text = message.reply_to_message.text or ""
    match = _ANSWER_RE.search(replied_text)
    if not match or not message.text:
        return
    ticket_id = int(match.group(1))
    user_id = int(match.group(2))
    lang = await _user_lang(user_id)
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(SupportTicket).where(SupportTicket.id == ticket_id))
            ticket = result.scalars().first()
            if ticket:
                ticket.status = "answered"
                ticket.updated_at = get_naive_utc()
                db.add(SupportMessage(ticket_id=ticket_id, sender="admin", message=message.text))
                await db.commit()
        await _send_message(chat_id=user_id, text=_TRANSLATIONS[lang]["ticket_reply"].format(message.text))
        await message.reply("Sent to user")
    except Exception:
        await message.reply("Failed to deliver. User may have blocked the bot.")
