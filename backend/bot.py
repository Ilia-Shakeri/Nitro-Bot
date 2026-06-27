import os

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.future import select

from database import AsyncSessionLocal
from models import User, Transaction

BOT_TOKEN    = os.getenv("BOT_TOKEN", "REPLACE_WITH_YOUR_TOKEN")
ADMIN_GROUP_ID = os.getenv("ADMIN_GROUP_ID", "-1000000000")

bot = Bot(token=BOT_TOKEN)
dp  = Dispatcher()

_TRANSLATIONS = {
    "en": {
        "welcome":     "Welcome to Nitro Bot!\nLaunch the Mini App to start.",
        "tx_approved": "Your receipt for {} Nitro has been approved!\nCredits added.",
        "tx_rejected": "Your receipt for {} Nitro was rejected.\nPlease contact support.",
    },
    "fa": {
        "welcome":     "به ربات نیترو خوش آمدید!\nمینی‌اپ را باز کنید.",
        "tx_approved": "رسید شما برای {} نیترو تایید شد!\nاعتبار اضافه شد.",
        "tx_rejected": "رسید شما برای {} نیترو رد شد.\nلطفا با پشتیبانی تماس بگیرید.",
    },
}


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.telegram_id == message.from_user.id))
        user = result.scalars().first()
        if not user:
            user = User(
                telegram_id=message.from_user.id,
                language_preference="fa",
                credits=0,
            )
            db.add(user)
            await db.commit()
        lang = user.language_preference

    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(
        text="Open Mini App",
        web_app=types.WebAppInfo(url=os.getenv("MINI_APP_URL", "https://example.com")),
    ))
    await message.answer(_TRANSLATIONS[lang]["welcome"], reply_markup=builder.as_markup())


async def notify_admin_new_receipt(tx_id: int, amount: int, payment_method: str, receipt_url: str):
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(text="Approve ✅", callback_data=f"tx_approve_{tx_id}"),
        types.InlineKeyboardButton(text="Reject ❌",  callback_data=f"tx_reject_{tx_id}"),
    )
    await bot.send_message(
        chat_id=ADMIN_GROUP_ID,
        text=(
            f"New Payment Receipt!\n"
            f"Transaction ID: {tx_id}\n"
            f"Method: {payment_method.upper()}\n"
            f"Amount: {amount} Nitro\n"
            f"Receipt: {receipt_url}"
        ),
        reply_markup=builder.as_markup(),
    )


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
            await callback.message.edit_text(callback.message.text + "\n\nStatus: APPROVED ✅")

        elif action == "reject":
            tx.status = "rejected"
            await db.commit()
            await bot.send_message(tx.user_id, _TRANSLATIONS[lang]["tx_rejected"].format(tx.amount))
            await callback.message.edit_text(callback.message.text + "\n\nStatus: REJECTED ❌")

    await callback.answer()
