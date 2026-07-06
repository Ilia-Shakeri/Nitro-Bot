import os
import re

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, ForceReply, InputMediaAudio, InputMediaPhoto
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.future import select

from database import AsyncSessionLocal
from models import User, Transaction, SupportMessage, SupportTicket, get_naive_utc

BOT_TOKEN = os.getenv("BOT_TOKEN", "REPLACE_WITH_YOUR_TOKEN")
ADMIN_GROUP_ID = os.getenv("ADMIN_GROUP_ID", "-1000000000")


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


async def _user_lang(tg_id: int) -> str:
    """Look up a user's language preference, defaulting to Farsi."""
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(User).where(User.telegram_id == tg_id))
        user = res.scalars().first()
    return user.language_preference if user else "fa"


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
            web_app=types.WebAppInfo(url=os.getenv("MINI_APP_URL", "https://example.com")),
        )
    )
    await message.answer(_TRANSLATIONS[lang]["welcome"], reply_markup=builder.as_markup())


async def notify_admin_new_ticket(ticket_id: int, tg_id: int, name: str, username: str, subject: str, message: str):
    subj_line = f"Subject: {subject}\n" if subject else ""
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(text="Answer", callback_data=f"ticket_answer_{ticket_id}_{tg_id}"),
    )
    await bot.send_message(
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
        await bot.send_photo(
            chat_id=ADMIN_GROUP_ID,
            message_thread_id=PAYMENT_TOPIC_ID,
            photo=photo,
            caption=caption,
            reply_markup=builder.as_markup(),
        )
    except Exception:
        await bot.send_document(
            chat_id=ADMIN_GROUP_ID,
            message_thread_id=PAYMENT_TOPIC_ID,
            document=BufferedInputFile(receipt_bytes, filename=receipt_filename),
            caption=caption,
            reply_markup=builder.as_markup(),
        )


async def notify_admin_new_release(
    release_id: int,
    song_name: str,
    artist_name: str,
    genre: str,
    release_date: str,
    cost: int,
    submitter: str,
    audio_bytes: bytes,
    audio_filename: str,
    cover_bytes: bytes,
    cover_filename: str,
):
    """Post a staged release as one media group in the Order topic."""
    caption = (
        f"New Release (Staging)\n"
        f"Release ID: {release_id}\n"
        f"From: {submitter}\n"
        f"Song: {song_name}\n"
        f"Artist: {artist_name}\n"
        f"Genre: {genre}\n"
        f"Release date: {release_date}\n"
        f"Cost: {cost} Nitro"
    )
    try:
        await bot.send_media_group(
            chat_id=ADMIN_GROUP_ID,
            message_thread_id=ORDER_TOPIC_ID,
            media=[
                InputMediaAudio(media=BufferedInputFile(audio_bytes, filename=audio_filename), caption=caption),
                InputMediaPhoto(media=BufferedInputFile(cover_bytes, filename=cover_filename)),
            ],
        )
    except Exception:
        await bot.send_document(
            chat_id=ADMIN_GROUP_ID,
            message_thread_id=ORDER_TOPIC_ID,
            document=BufferedInputFile(audio_bytes, filename=audio_filename),
            caption=caption,
        )


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
            await bot.send_message(tx.user_id, _TRANSLATIONS[lang]["tx_approved"].format(tx.amount))
            await _append_status(callback.message, "\n\nStatus: APPROVED")

        elif action == "reject":
            tx.status = "rejected"
            await db.commit()
            await bot.send_message(tx.user_id, _TRANSLATIONS[lang]["tx_rejected"].format(tx.amount))
            await _append_status(callback.message, "\n\nStatus: REJECTED")

    await callback.answer()


@dp.callback_query(F.data.startswith("ticket_answer_"))
async def handle_ticket_answer(callback: types.CallbackQuery):
    """Prompt an admin reply and tag the target ticket and user."""
    _, _, ticket_id, tg_id = callback.data.split("_")
    await bot.send_message(
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
        await bot.send_message(user_id, _TRANSLATIONS[lang]["ticket_reply"].format(message.text))
        await message.reply("Sent to user")
    except Exception:
        await message.reply("Failed to deliver. User may have blocked the bot.")
