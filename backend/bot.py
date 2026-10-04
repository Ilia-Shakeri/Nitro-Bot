import os
import re
import logging
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from aiogram import Bot, Dispatcher, F, types
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandObject
from aiogram.types import BufferedInputFile, ForceReply
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.exc import IntegrityError
from sqlalchemy.future import select

from database import AsyncSessionLocal
from ledger import add_ledger_entry
from models import Release, StaffAuditLog, User, Transaction, SupportMessage, SupportTicket, get_naive_utc
from notification_jobs import enqueue_notification
from payment_stars import stars_payment_matches
from user_identity import sync_telegram_profile

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_GROUP_ID = os.getenv("ADMIN_GROUP_ID", "").strip()
APP_VERSION = os.getenv("APP_VERSION", "0.9.0-alpha.50")
logger = logging.getLogger("nitro.bot")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is required")
if os.getenv("ENVIRONMENT", "development").lower() == "production" and not ADMIN_GROUP_ID:
    raise RuntimeError("ADMIN_GROUP_ID is required in production")


def _parse_manager_ids(raw: str) -> set[int]:
    manager_ids: set[int] = set()
    for item in raw.split(","):
        value = item.strip()
        if not value:
            continue
        try:
            manager_ids.add(int(value))
        except ValueError:
            logger.warning("Ignoring invalid MANAGER_IDS entry: %s", value)
    return manager_ids


MANAGER_IDS = _parse_manager_ids(os.getenv("MANAGER_IDS", ""))
if os.getenv("ENVIRONMENT", "development").lower() == "production" and not MANAGER_IDS:
    raise RuntimeError("MANAGER_IDS is required in production")


def _topic(env_name: str) -> int | None:
    """Parse a forum topic id. Empty means the General topic."""
    raw = os.getenv(env_name, "").strip()
    return int(raw) if raw else None


ORDER_TOPIC_ID = _topic("ORDER_TOPIC_ID")
TICKET_TOPIC_ID = _topic("TICKET_TOPIC_ID")
PAYMENT_TOPIC_ID = _topic("PAYMENT_TOPIC_ID")
DMB_SUCCESS_TOPIC_ID = _topic("DMB_SUCCESS_TOPIC_ID")
DMB_ERROR_TOPIC_ID = _topic("DMB_ERROR_TOPIC_ID")
DMB_REVIEW_TOPIC_ID = _topic("DMB_REVIEW_TOPIC_ID")
DMB_MAX_ATTEMPTS = max(1, int(os.getenv("DMB_MAX_ATTEMPTS", "3")))
DMB_RECOVERY_ENABLED = os.getenv("DMB_RECOVERY_ENABLED", "false").lower() == "true"
DMB_RESULTS_ROOT = Path(os.getenv("DMB_RESULTS_ROOT", "/app/dmb-results")).resolve()
if os.getenv("ENVIRONMENT", "development").lower() == "production" and any(
    topic is None
    for topic in (DMB_SUCCESS_TOPIC_ID, DMB_ERROR_TOPIC_ID, DMB_REVIEW_TOPIC_ID)
):
    raise RuntimeError("DMB report topic IDs are required in production")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

_ANSWER_MARKER = "[answer:{ticket_id}:{tg_id}]"
_ANSWER_RE = re.compile(r"\[answer:(\d+):(\d+)\]")
_TX_ACTION_RE = re.compile(r"^tx_(approve|reject)_(\d+)$")
_TICKET_ACTION_RE = re.compile(r"^ticket_answer_(\d+)_(\d+)$")
_DMB_ACTION_RE = re.compile(r"^dmb_(retry|resume)_(\d+)_(\d+)$")

_TRANSLATIONS = {
    "en": {
        "welcome": "Welcome to Nitro Bot!\nLaunch the Mini App to start.",
        "tx_approved": "Your receipt for {} Nitro has been approved!\nCredits added.",
        "tx_rejected": "Your receipt for {} Nitro was rejected.\nPlease contact support.",
        "ticket_reply": "Support reply:\n\n{}",
        "open_app": "Open Mini App",
    },
    "fa": {
        "welcome": "به ربات نیترو خوش آمدید!\nمینی اپ را باز کنید.",
        "tx_approved": "رسید شما برای {} نیترو تایید شد!\nاعتبار اضافه شد.",
        "tx_rejected": "رسید شما برای {} نیترو رد شد.\nلطفا با پشتیبانی تماس بگیرید.",
        "ticket_reply": "پاسخ پشتیبانی:\n\n{}",
        "open_app": "باز کردن مینی‌اپ",
    },
    "ar": {
        "welcome": "مرحباً بك في Nitro Bot!\nافتح التطبيق المصغر للبدء.",
        "tx_approved": "تمت الموافقة على إيصال {} Nitro الخاص بك!\nتمت إضافة الرصيد.",
        "tx_rejected": "تم رفض إيصال {} Nitro الخاص بك.\nيرجى التواصل مع الدعم.",
        "ticket_reply": "رد فريق الدعم:\n\n{}",
        "open_app": "فتح التطبيق المصغر",
    },
    "ru": {
        "welcome": "Добро пожаловать в Nitro Bot!\nОткройте мини-приложение, чтобы начать.",
        "tx_approved": "Ваша квитанция на {} Nitro одобрена!\nСредства зачислены.",
        "tx_rejected": "Ваша квитанция на {} Nitro отклонена.\nОбратитесь в поддержку.",
        "ticket_reply": "Ответ поддержки:\n\n{}",
        "open_app": "Открыть мини-приложение",
    },
}


def _is_missing_message_thread(exc: TelegramBadRequest) -> bool:
    return "message thread not found" in str(exc).lower()


def _staff_action_allowed(message: types.Message | None, actor_id: int, topic_id: int | None) -> bool:
    return bool(
        message is not None
        and str(message.chat.id) == str(ADMIN_GROUP_ID)
        and actor_id in MANAGER_IDS
        and message.message_thread_id == topic_id
    )


async def _send_with_thread_fallback(
    method_name: str,
    *,
    strict_thread: bool = False,
    **kwargs: Any,
) -> Any:
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
        if strict_thread or not _is_missing_message_thread(exc) or message_thread_id is None:
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


async def _send_message(*, strict_thread: bool = False, **kwargs: Any) -> Any:
    return await _send_with_thread_fallback(
        "send_message", strict_thread=strict_thread, **kwargs
    )


async def _send_photo(*, strict_thread: bool = False, **kwargs: Any) -> Any:
    return await _send_with_thread_fallback(
        "send_photo", strict_thread=strict_thread, **kwargs
    )


async def _send_document(*, strict_thread: bool = False, **kwargs: Any) -> Any:
    return await _send_with_thread_fallback(
        "send_document", strict_thread=strict_thread, **kwargs
    )


async def _send_audio(**kwargs: Any) -> Any:
    return await _send_with_thread_fallback("send_audio", **kwargs)


async def _send_media_group(**kwargs: Any) -> Any:
    return await _send_with_thread_fallback("send_media_group", **kwargs)


def _mini_app_url() -> str:
    """Return the Mini App URL with a deploy version to bypass Telegram webview cache."""
    raw = os.getenv("MINI_APP_URL", "").strip()
    if not raw:
        raise RuntimeError("MINI_APP_URL is required")
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


def _referrer_from_args(args: str | None, current_tg_id: int) -> int | None:
    if not args:
        return None
    match = re.fullmatch(r"ref_(\d+)", args.strip())
    if not match:
        return None
    referrer_id = int(match.group(1))
    return referrer_id if referrer_id != current_tg_id else None


@dp.message(Command("start"))
async def cmd_start(message: types.Message, command: CommandObject):
    tg_id = message.from_user.id
    referrer_id = _referrer_from_args(command.args, tg_id)
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.telegram_id == tg_id))
        user = result.scalars().first()
        should_award_referral = False
        if not user:
            user = User(
                telegram_id=tg_id,
                username=message.from_user.username,
                first_name=message.from_user.first_name,
                last_name=message.from_user.last_name,
                language_preference="fa",
                credits=0,
                referred_by=referrer_id,
            )
            db.add(user)
            should_award_referral = referrer_id is not None
        elif referrer_id and user.referred_by is None:
            user.referred_by = referrer_id
            should_award_referral = True

        sync_telegram_profile(
            user,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
            username=message.from_user.username,
        )

        if referrer_id and should_award_referral:
            ref_result = await db.execute(select(User).where(User.telegram_id == referrer_id))
            referrer = ref_result.scalars().first()
            if referrer:
                referrer.referral_points = (referrer.referral_points or 0) + 1

        await db.commit()
        language = user.language_preference if user.language_preference in _TRANSLATIONS else "fa"

    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(
            text=_TRANSLATIONS[language]["open_app"],
            web_app=types.WebAppInfo(url=_mini_app_url()),
        )
    )
    await message.answer(_TRANSLATIONS[language]["welcome"], reply_markup=builder.as_markup())


@dp.message(Command("version"))
async def cmd_version(message: types.Message):
    await message.answer(f"Mini App version: {APP_VERSION}\n{_mini_app_url()}")


async def _valid_stars_transaction(
    *,
    payload: str,
    tg_id: int,
    currency: str,
    total_amount: int,
) -> bool:
    if currency != "XTR":
        return False
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Transaction)
            .where(Transaction.invoice_payload == payload)
            .with_for_update()
        )
        tx = result.scalars().first()
        valid = bool(tx and stars_payment_matches(tx, tg_id, currency, total_amount))
        await db.rollback()
        return valid


@dp.pre_checkout_query()
async def validate_stars_pre_checkout(query: types.PreCheckoutQuery):
    valid = await _valid_stars_transaction(
        payload=query.invoice_payload,
        tg_id=query.from_user.id,
        currency=query.currency,
        total_amount=query.total_amount,
    )
    await query.answer(
        ok=valid,
        error_message=None if valid else "Payment details are no longer valid.",
    )


@dp.message(F.successful_payment)
async def fulfill_stars_payment(message: types.Message):
    payment = message.successful_payment
    if payment is None:
        return
    charge_id = payment.telegram_payment_charge_id
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Transaction)
            .where(Transaction.invoice_payload == payment.invoice_payload)
            .with_for_update()
        )
        tx = result.scalars().first()
        if not tx:
            logger.error("Stars payment has unknown invoice payload")
            await db.rollback()
            return
        if tx.status == "approved" and tx.provider_charge_id == charge_id:
            await db.rollback()
            return
        if (
            not stars_payment_matches(
                tx,
                message.from_user.id,
                payment.currency,
                payment.total_amount,
            )
        ):
            logger.error("Stars payment validation failed for transaction %s", tx.id)
            await db.rollback()
            return
        duplicate = await db.execute(
            select(Transaction.id).where(Transaction.provider_charge_id == charge_id)
        )
        if duplicate.scalar_one_or_none() is not None:
            await db.rollback()
            return
        user_result = await db.execute(
            select(User)
            .where(User.telegram_id == tx.user_id)
            .with_for_update()
        )
        user = user_result.scalars().first()
        if not user:
            await db.rollback()
            return
        tx.provider_charge_id = charge_id
        tx.status = "approved"
        user.credits += tx.amount
        add_ledger_entry(
            db,
            user_id=user.telegram_id,
            amount=tx.amount,
            kind="topup",
            idempotency_key=f"transaction:{tx.id}:topup",
            transaction_id=tx.id,
            details={"payment_method": tx.payment_method},
        )
        if user.referred_by:
            referrer_result = await db.execute(
                select(User).where(User.telegram_id == user.referred_by).with_for_update()
            )
            referrer = referrer_result.scalars().first()
            if referrer:
                referrer.credits += 1
                add_ledger_entry(
                    db,
                    user_id=referrer.telegram_id,
                    amount=1,
                    kind="referral_reward",
                    idempotency_key=f"transaction:{tx.id}:referral:{referrer.telegram_id}",
                    transaction_id=tx.id,
                    details={"referred_user_id": user.telegram_id},
                )
        enqueue_notification(
            db,
            kind="user_payment_result",
            aggregate_id=tx.id,
            idempotency_key=f"transaction:{tx.id}:approved-user-notice",
        )
        try:
            await db.commit()
        except IntegrityError:
            await db.rollback()
            logger.warning("Duplicate Stars charge ignored")
            return


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
    receipt_bytes: bytes | None,
    receipt_filename: str | None,
    usd_amount_cents: int,
    toman_amount_cents: int | None,
    quote_asset: str | None = None,
    quote_network: str | None = None,
    quoted_amount: str | None = None,
):
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(text="✅ APPROVE", callback_data=f"tx_approve_{tx_id}"),
        types.InlineKeyboardButton(text="Reject", callback_data=f"tx_reject_{tx_id}"),
    )
    title = "New Crypto Payment Claim" if quote_asset else "New Payment Receipt"
    usd_amount = f"{usd_amount_cents // 100}.{usd_amount_cents % 100:02d}"
    toman_line = (
        f"\nQuoted Toman amount: {toman_amount_cents // 100:,}"
        f".{toman_amount_cents % 100:02d}"
        if toman_amount_cents is not None
        else ""
    )
    caption = (
        f"{title}\n"
        f"Transaction ID: {tx_id}\n"
        f"From: {submitter}\n"
        f"Method: {payment_method.upper()}\n"
        f"Amount: {amount} Nitro\n"
        f"USD value: {usd_amount}\n"
        f"Quoted payment: {quoted_amount or '-'} {quote_asset or '-'}\n"
        f"Network: {quote_network or '-'}"
        f"{toman_line}"
    )
    if receipt_bytes is None:
        await _send_message(
            chat_id=ADMIN_GROUP_ID,
            message_thread_id=PAYMENT_TOPIC_ID,
            text=caption,
            reply_markup=builder.as_markup(),
        )
        return

    receipt_name = receipt_filename or "receipt.jpg"
    photo = BufferedInputFile(receipt_bytes, filename=receipt_name)
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
                document=BufferedInputFile(receipt_bytes, filename=receipt_name),
                caption=caption,
                reply_markup=builder.as_markup(),
            )
        except Exception:
            logger.error("Failed to send receipt %s document to Telegram payment topic", tx_id, exc_info=True)
            raise


async def notify_admin_new_release(
    submitter_tg_id: int,
    release_id: int,
    song_name: str,
    artists: list[dict[str, str]],
    producers: list[str],
    legal_names: list[str],
    genre: str,
    sub_genre: str | None,
    release_date: str,
    is_rerelease: bool,
    original_release_date: str | None,
    mapping_spotify: str | None,
    mapping_apple: str | None,
    requires_new_profile: bool,
    profile_email: str | None,
    artist_mappings: list[dict],
    is_edit: bool,
    copyright_requested: bool,
    explicit_content: bool,
    cost: int,
    submitter: str,
    audio_bytes: bytes | None,
    audio_filename: str | None,
    cover_bytes: bytes | None,
    cover_filename: str | None,
):
    primary_artists = [
        artist["name"] for artist in artists if artist["role"] == "primary"
    ]
    featured_artists = [
        artist["name"] for artist in artists if artist["role"] == "featured"
    ]
    manager_prefix = "#MANAGER\n" if submitter_tg_id in MANAGER_IDS else ""
    mapping_lines = []
    roles_by_name = {
        artist["name"].casefold(): artist["role"] for artist in artists
    }
    for index, mapping in enumerate(artist_mappings, start=1):
        artist = mapping.get("artist_name", "-")
        role = roles_by_name.get(str(artist).casefold(), "featured")
        if mapping.get("requires_new_profile"):
            details = f"new profile; email: {mapping.get('profile_email') or '-'}"
        else:
            details = (
                f"Spotify: {mapping.get('spotify_url') or '-'}; "
                f"Apple Music: {mapping.get('apple_music_url') or '-'}"
            )
        dmb_account = "yes" if mapping.get("dmb_has_account") else "no"
        mapping_lines.append(
            f"{index}. {artist} ({role}): {details}; DMB account: {dmb_account}"
        )
    mappings_text = "\n".join(mapping_lines) or "-"
    caption = (
        f"{manager_prefix}"
        f"New Release (Staging)\n"
        f"Release ID: {release_id}\n"
        f"From: {submitter}\n"
        f"Song: {song_name}\n"
        f"Primary artists: {', '.join(primary_artists) or '-'}\n"
        f"Featured artists: {', '.join(featured_artists) or '-'}\n"
        f"Legal names: {', '.join(legal_names)}\n"
        f"Producers: {', '.join(producers) or '-'}\n"
        f"Genre: {genre}\n"
        f"Subgenre: {sub_genre or '-'}\n"
        f"Re-release: {'yes' if is_rerelease else 'no'}\n"
        f"{'Re-release' if is_rerelease else 'Release'} date: {release_date}\n"
        f"Original release date: {original_release_date or '-'}\n"
        f"Artist mappings:\n{mappings_text}\n"
        f"Edit order: {'yes' if is_edit else 'no'}\n"
        f"Copyright: {'yes' if copyright_requested else 'no'}\n"
        f"Explicit content: {'yes' if explicit_content else 'no'}\n"
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

    media_caption = caption
    if len(caption) > 1024:
        await _send_message(
            chat_id=ADMIN_GROUP_ID,
            message_thread_id=ORDER_TOPIC_ID,
            text=caption,
        )
        media_caption = f"Media for release ID: {release_id}"

    try:
        # Send a single audio message and attach the cover as a thumbnail
        if audio_bytes and audio_filename:
            await _send_audio(
                chat_id=ADMIN_GROUP_ID,
                message_thread_id=ORDER_TOPIC_ID,
                audio=BufferedInputFile(audio_bytes, filename=audio_filename),
                thumbnail=BufferedInputFile(cover_bytes, filename=cover_filename) if cover_bytes else None,
                caption=media_caption,
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
                caption=media_caption,
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
                    caption=media_caption + "\nMedia upload failed - files unavailable",
                )
            except Exception:
                logger.error("Fallback release %s document send failed", release_id, exc_info=True)
                raise

def _safe_dmb_error(value: object) -> str:
    text = re.sub(r"\s+", " ", str(value or "dmb_delivery_failed")).strip()
    text = re.sub(
        r"(?i)(password|token|secret|authorization)\s*[:=]\s*\S+",
        r"\1=[hidden]",
        text,
    )
    return text[:500]


def _dmb_evidence_image(
    evidence_path: object,
    release_id: int,
    event: str = "error",
) -> tuple[bytes, str] | None:
    raw = str(evidence_path or "").replace("\\", "/").strip("/")
    parts = [part for part in raw.split("/") if part]
    if parts[:1] == ["results"]:
        parts = parts[1:]
    if not parts or parts[0] != str(release_id) or any(part in {".", ".."} for part in parts):
        return None
    base = DMB_RESULTS_ROOT.joinpath(*parts).resolve()
    if not base.is_relative_to(DMB_RESULTS_ROOT):
        return None
    candidates = []
    if base.is_file():
        candidates.append(base)
    else:
        candidates.extend(
            [
                base / "recovery" / "final-page-full.png",
                base / "final-page-full.png",
                base / "recovery" / "published.png",
                base / "submitted.png",
                base / "final-state.png",
                base / "recovery" / "final-state.png",
            ]
        )
        try:
            candidates.extend(
                base.rglob("selenium-screenshot-*.png")
            )
        except OSError:
            pass
        def _mtime(item: Path) -> float:
            try:
                return item.stat().st_mtime
            except OSError:
                return -1
        if event == "success":
            priority = {
                "final-page-full.png": 3,
                "published.png": 2,
                "submitted.png": 1,
            }
            candidates = [item for item in candidates if item.name in priority]
            candidates = sorted(
                set(candidates),
                key=lambda item: (priority.get(item.name, 0), _mtime(item)),
                reverse=True,
            )
        else:
            candidates = sorted(set(candidates), key=_mtime, reverse=True)
    for candidate in candidates:
        try:
            resolved = candidate.resolve()
            size = resolved.stat().st_size
            header = resolved.read_bytes()[:12]
        except OSError:
            continue
        if (
            resolved.is_relative_to(DMB_RESULTS_ROOT)
            and 100 <= size <= 45 * 1024 * 1024
            and (
                header.startswith(b"\x89PNG\r\n\x1a\n")
                or header.startswith(b"\xff\xd8\xff")
            )
        ):
            return resolved.read_bytes(), resolved.name
    return None


def _dmb_report_keyboard(
    release: Release,
    event: str,
    attempt: int,
) -> types.InlineKeyboardMarkup | None:
    builder = InlineKeyboardBuilder()
    if (
        event == "error"
        and release.status == "dmb_retry_waiting"
        and release.dmb_attempts == attempt
        and attempt < DMB_MAX_ATTEMPTS
        and release.dmb_submission_started_at is None
    ):
        builder.button(
            text="🔄 تلاش دوباره",
            callback_data=f"dmb_retry_{release.id}_{attempt}",
        )
    elif (
        event == "review"
        and release.status == "dmb_verification_required"
        and release.dmb_attempts == attempt
        and not release.is_edit
        and release.dmb_release_id
        and release.dmb_ean_upc
        and release.dmb_isrcs
        and release.dmb_submission_fingerprint
        and attempt < DMB_MAX_ATTEMPTS
        and DMB_RECOVERY_ENABLED
    ):
        builder.button(
            text="🔁 تلاش مجدد امن",
            callback_data=f"dmb_resume_{release.id}_{attempt}",
        )
    return builder.as_markup() if list(builder.buttons) else None


def _short_report_value(value: object, limit: int = 160) -> str:
    text = re.sub(r"\s+", " ", str(value or "-")).strip()
    return text[:limit] or "-"


def _dmb_report_content(
    release: Release,
    event: str,
    payload: dict,
) -> tuple[int, str, types.InlineKeyboardMarkup | None]:
    if event not in {"success", "error", "review"}:
        raise RuntimeError("dmb_report_event_invalid")
    attempt = int(payload.get("attempt") or release.dmb_attempts or 0)
    mode = "ویرایش" if release.is_edit else "ساخت"
    error = _safe_dmb_error(payload.get("error") or release.dmb_last_error)[:260]
    reply_markup = _dmb_report_keyboard(release, event, attempt)
    title = _short_report_value(release.song_name)
    artist = _short_report_value(getattr(release, "artist_name", None))
    order_id = release.id
    dmb_id = _short_report_value(release.dmb_release_id)
    ean = _short_report_value(release.dmb_ean_upc)
    isrcs = _short_report_value(", ".join(release.dmb_isrcs or []), 240)
    if event == "success":
        topic_id = DMB_SUCCESS_TOPIC_ID
        text = (
            "✅ انتشار در DMB موفق شد\n\n"
            f"🎵 نام آهنگ: {title}\n"
            f"👤 هنرمند: {artist}\n"
            f"🆔 ID سفارش: {order_id}\n"
            f"🔗 ID در DMB: {dmb_id}\n"
            f"🏷 EAN/UPC: {ean}\n"
            f"🎧 ISRC: {isrcs}\n"
            f"🛠 نوع کار: {mode}\n"
            f"🔢 تعداد تلاش: {attempt}\n\n"
            "📸 تصویر کامل صفحه نهایی پیوست شد."
        )
    elif event == "review":
        topic_id = DMB_REVIEW_TOPIC_ID
        next_action = (
            "دکمه «تلاش مجدد امن» همان آلبوم ذخیره‌شده را ادامه می‌دهد."
            if reply_markup is not None
            else "تلاش مجدد قفل است؛ مدرک هویت آلبوم کامل نیست یا سقف تلاش پر است."
        )
        text = (
            "🟠 بررسی انسانی DMB لازم است\n\n"
            f"🎵 نام آهنگ: {title}\n"
            f"👤 هنرمند: {artist}\n"
            f"🆔 ID سفارش: {order_id}\n"
            f"👥 ID کاربر: {_short_report_value(release.user_id)}\n"
            f"🔗 ID ذخیره‌شده DMB: {dmb_id}\n"
            f"🏷 EAN/UPC: {ean}\n"
            f"🎧 ISRC: {isrcs}\n"
            f"🛠 نوع کار: {mode}\n"
            f"🔢 تلاش: {attempt}/{DMB_MAX_ATTEMPTS}\n"
            f"⚠️ علت: {error}\n\n"
            f"➡️ کار بعدی: {next_action}\n"
            "🛡 ساخت آلبوم تازه تا روشن‌شدن نتیجه قفل است."
        )
    else:
        topic_id = DMB_ERROR_TOPIC_ID
        stage = (
            "پس از شروع ثبت؛ ساخت دوباره قفل است"
            if release.dmb_submission_started_at is not None
            else "پیش از ثبت نهایی"
        )
        retry_line = (
            "دکمه تلاش مجدد آماده است."
            if reply_markup is not None
            else "تلاش مجدد خودکار قفل است."
        )
        text = (
            "❌ خطا در DMB\n\n"
            f"🎵 نام آهنگ: {title}\n"
            f"👤 هنرمند: {artist}\n"
            f"🆔 ID سفارش: {order_id}\n"
            f"🛠 نوع کار: {mode}\n"
            f"📍 مرحله: {stage}\n"
            f"🔢 تلاش: {attempt}/{DMB_MAX_ATTEMPTS}\n"
            f"⚠️ خطا: {error}\n\n"
            f"➡️ وضعیت: {retry_line}"
        )
    if topic_id is None:
        raise RuntimeError("dmb_report_topic_missing")
    if len(text) > 1000:
        raise RuntimeError("dmb_report_caption_too_long")
    return topic_id, text, reply_markup


async def _send_dmb_report_image(
    *,
    topic_id: int,
    text: str,
    reply_markup: types.InlineKeyboardMarkup | None,
    evidence: tuple[bytes, str],
) -> None:
    image_bytes, image_name = evidence
    try:
        await _send_photo(
            strict_thread=True,
            chat_id=ADMIN_GROUP_ID,
            message_thread_id=topic_id,
            photo=BufferedInputFile(image_bytes, filename=image_name),
            caption=text,
            reply_markup=reply_markup,
        )
    except TelegramBadRequest as exc:
        if _is_missing_message_thread(exc):
            raise
        await _send_document(
            strict_thread=True,
            chat_id=ADMIN_GROUP_ID,
            message_thread_id=topic_id,
            document=BufferedInputFile(image_bytes, filename=image_name),
            caption=text,
            reply_markup=reply_markup,
        )


async def notify_admin_dmb_report(
    release: Release,
    event: str,
    payload: dict,
) -> None:
    topic_id, text, reply_markup = _dmb_report_content(release, event, payload)
    evidence = _dmb_evidence_image(
        payload.get("evidence_path") or release.dmb_evidence_path,
        release.id,
        event,
    )
    if event == "success" and evidence is None:
        raise RuntimeError("dmb_success_evidence_missing")
    if evidence is not None:
        await _send_dmb_report_image(
            topic_id=topic_id,
            text=text,
            reply_markup=reply_markup,
            evidence=evidence,
        )
        return
    await _send_message(
        strict_thread=True,
        chat_id=ADMIN_GROUP_ID,
        message_thread_id=topic_id,
        text=text,
        reply_markup=reply_markup,
    )


async def _finish_dmb_action_message(message: types.Message, suffix: str) -> None:
    try:
        if message.caption is not None:
            await message.edit_caption(caption=message.caption + suffix, reply_markup=None)
        elif message.text is not None:
            await message.edit_text(message.text + suffix, reply_markup=None)
    except Exception:
        logger.warning("Could not close DMB report action", exc_info=True)


async def _append_status(message: types.Message, suffix: str) -> None:
    """Append a status line to a group message when Telegram allows editing."""
    try:
        if message.caption is not None:
            await message.edit_caption(caption=message.caption + suffix)
        elif message.text is not None:
            await message.edit_text(message.text + suffix)
    except Exception:
        logger.warning("Could not append Telegram status text", exc_info=True)


@dp.callback_query(F.data.startswith("tx_"))
async def handle_tx_decision(callback: types.CallbackQuery):
    actor_id = callback.from_user.id
    if not _staff_action_allowed(callback.message, actor_id, PAYMENT_TOPIC_ID):
        await callback.answer("Not allowed.", show_alert=True)
        return
    match = _TX_ACTION_RE.fullmatch(callback.data or "")
    if not match:
        await callback.answer("Invalid action.", show_alert=True)
        return
    action, tx_id_raw = match.groups()
    tx_id = int(tx_id_raw)

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Transaction).where(Transaction.id == tx_id).with_for_update())
        tx = result.scalars().first()

        if not tx or tx.status != "pending":
            await callback.answer("Transaction already processed or not found.")
            return

        user_res = await db.execute(
            select(User).where(User.telegram_id == tx.user_id).with_for_update()
        )
        user = user_res.scalars().first()
        if not user:
            await db.rollback()
            await callback.answer("Transaction user not found.", show_alert=True)
            return
        if action == "approve":
            tx.status = "approved"
            user.credits += tx.amount
            add_ledger_entry(
                db,
                user_id=user.telegram_id,
                amount=tx.amount,
                kind="topup",
                idempotency_key=f"transaction:{tx.id}:topup",
                transaction_id=tx.id,
                details={"payment_method": tx.payment_method},
            )
            if user.referred_by:
                referrer_result = await db.execute(
                    select(User).where(User.telegram_id == user.referred_by).with_for_update()
                )
                referrer = referrer_result.scalars().first()
                if referrer:
                    referrer.credits += 1
                    add_ledger_entry(
                        db,
                        user_id=referrer.telegram_id,
                        amount=1,
                        kind="referral_reward",
                        idempotency_key=f"transaction:{tx.id}:referral:{referrer.telegram_id}",
                        transaction_id=tx.id,
                        details={"referred_user_id": user.telegram_id},
                    )
            enqueue_notification(
                db,
                kind="user_payment_result",
                aggregate_id=tx.id,
                idempotency_key=f"transaction:{tx.id}:approved-user-notice",
            )
            db.add(StaffAuditLog(
                actor_id=actor_id,
                action="transaction_approve",
                target_type="transaction",
                target_id=str(tx.id),
                old_state="pending",
                new_state="approved",
            ))
            await db.commit()
            await _append_status(callback.message, "\n\nStatus: APPROVED")

        elif action == "reject":
            tx.status = "rejected"
            db.add(StaffAuditLog(
                actor_id=actor_id,
                action="transaction_reject",
                target_type="transaction",
                target_id=str(tx.id),
                old_state="pending",
                new_state="rejected",
            ))
            enqueue_notification(
                db,
                kind="user_payment_result",
                aggregate_id=tx.id,
                idempotency_key=f"transaction:{tx.id}:rejected-user-notice",
            )
            await db.commit()
            await _append_status(callback.message, "\n\nStatus: REJECTED")

    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        logger.warning("Could not remove processed transaction buttons", exc_info=True)
    await callback.answer()


@dp.callback_query(F.data.startswith("dmb_"))
async def handle_dmb_action(callback: types.CallbackQuery):
    match = _DMB_ACTION_RE.fullmatch(callback.data or "")
    if not match:
        await callback.answer("کار نامعتبر.", show_alert=True)
        return
    action, release_id_raw, attempt_raw = match.groups()
    topic_id = DMB_ERROR_TOPIC_ID if action == "retry" else DMB_REVIEW_TOPIC_ID
    actor_id = callback.from_user.id
    if not _staff_action_allowed(callback.message, actor_id, topic_id):
        await callback.answer("دسترسی نیست.", show_alert=True)
        return
    release_id = int(release_id_raw)
    expected_attempt = int(attempt_raw)
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Release).where(Release.id == release_id).with_for_update()
        )
        release = result.scalars().first()
        if release is None or release.dmb_attempts != expected_attempt:
            await db.rollback()
            await callback.answer("این دکمه قدیمی است.", show_alert=True)
            return
        if release.dmb_attempts >= DMB_MAX_ATTEMPTS:
            await db.rollback()
            await callback.answer("سقف تلاش پر است.", show_alert=True)
            return
        old_state = release.status
        if action == "retry":
            if (
                release.status != "dmb_retry_waiting"
                or release.dmb_submission_started_at is not None
                or release.dmb_submission_fingerprint is not None
            ):
                await db.rollback()
                await callback.answer("تلاش از اول امن نیست.", show_alert=True)
                return
            release.status = "manual_staging"
            audit_action = "dmb_retry_requested"
            suffix = f"\n\n🔄 تلاش دوباره را ادمین {actor_id} خواست."
        else:
            if not DMB_RECOVERY_ENABLED:
                await db.rollback()
                await callback.answer("ادامه امن خاموش است.", show_alert=True)
                return
            if (
                release.status != "dmb_verification_required"
                or release.is_edit
                or not release.dmb_release_id
                or not release.dmb_ean_upc
                or not release.dmb_isrcs
                or not release.dmb_submission_fingerprint
            ):
                await db.rollback()
                await callback.answer("مدرک ادامه امن کامل نیست.", show_alert=True)
                return
            release.status = "dmb_recovery_requested"
            audit_action = "dmb_recovery_requested"
            suffix = f"\n\n▶️ ادامه امن را ادمین {actor_id} خواست."
        release.dmb_reviewed_by = f"telegram:{actor_id}"
        release.dmb_reviewed_at = get_naive_utc()
        db.add(
            StaffAuditLog(
                actor_id=actor_id,
                action=audit_action,
                target_type="release",
                target_id=str(release.id),
                old_state=old_state,
                new_state=release.status,
                details={"attempt": expected_attempt},
            )
        )
        await db.commit()
    await callback.answer("ثبت شد.")
    await _finish_dmb_action_message(callback.message, suffix)


@dp.callback_query(F.data.startswith("ticket_answer_"))
async def handle_ticket_answer(callback: types.CallbackQuery):
    """Prompt an admin reply and tag the target ticket and user."""
    if not _staff_action_allowed(callback.message, callback.from_user.id, TICKET_TOPIC_ID):
        await callback.answer("Not allowed.", show_alert=True)
        return
    match = _TICKET_ACTION_RE.fullmatch(callback.data or "")
    if not match:
        await callback.answer("Invalid action.", show_alert=True)
        return
    ticket_id, tg_id = match.groups()
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
    if not _staff_action_allowed(message, message.from_user.id, TICKET_TOPIC_ID):
        return
    replied_text = message.reply_to_message.text or ""
    match = _ANSWER_RE.search(replied_text)
    if not match or not message.text:
        return
    ticket_id = int(match.group(1))
    user_id = int(match.group(2))
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(SupportTicket)
                .where(SupportTicket.id == ticket_id)
                .with_for_update()
            )
            ticket = result.scalars().first()
            if not ticket or ticket.user_id != user_id:
                await db.rollback()
                await message.reply("Ticket target mismatch.")
                return
            old_state = ticket.status
            ticket.status = "answered"
            ticket.updated_at = get_naive_utc()
            support_message = SupportMessage(ticket_id=ticket_id, sender="admin", message=message.text)
            db.add(support_message)
            await db.flush()
            db.add(StaffAuditLog(
                actor_id=message.from_user.id,
                action="ticket_answer",
                target_type="support_ticket",
                target_id=str(ticket_id),
                old_state=old_state,
                new_state="answered",
            ))
            enqueue_notification(
                db,
                kind="user_ticket_reply",
                aggregate_id=support_message.id,
                idempotency_key=f"support-message:{support_message.id}:user-notice",
            )
            await db.commit()
        await message.reply("Reply queued for delivery")
    except Exception:
        await message.reply("Failed to deliver. User may have blocked the bot.")
