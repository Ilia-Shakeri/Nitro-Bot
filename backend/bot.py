import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from main import async_session
from models import User, Transaction

BOT_TOKEN = os.getenv("BOT_TOKEN", "8915255377:AAFaCAXBRklgb0vIAKP31QWPuCaCnC7-udc")
ADMIN_GROUP_ID = os.getenv("ADMIN_GROUP_ID", "-1000000000")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Translations could be loaded dynamically, hardcoded for brevity
TRANSLATIONS = {
    "en": {
        "welcome": "Welcome to Nitro Bot! Launch the Mini App to start.",
        "tx_approved": "Your receipt for {} Nitro has been approved! Credits added.",
        "tx_rejected": "Your receipt for {} Nitro was rejected. Please contact support."
    },
    "fa": {
        "welcome": "به ربات نیترو خوش آمدید! مینی‌اپ را باز کنید.",
        "tx_approved": "رسید شما برای {} نیترو تایید شد! اعتبار اضافه شد.",
        "tx_rejected": "رسید شما برای {} نیترو رد شد. لطفا با پشتیبانی تماس بگیرید."
    }
}

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    async with async_session() as db:
        result = await db.execute(select(User).where(User.telegram_id == message.from_user.id))
        user = result.scalars().first()
        if not user:
            user = User(
                telegram_id=message.from_user.id,
                username=message.from_user.username,
                first_name=message.from_user.first_name,
                language_preference="fa" # Default per instructions
            )
            db.add(user)
            await db.commit()

        lang = user.language_preference if user else "fa"

    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(
        text="Open Mini App",
        web_app=types.WebAppInfo(url=os.getenv("MINI_APP_URL", "https://example.com"))
    ))
    await message.answer(TRANSLATIONS[lang]["welcome"], reply_markup=builder.as_markup())

async def notify_admin_new_receipt(tx_id: int, amount: int, receipt_url: str):
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(text="Approve ✅", callback_data=f"tx_approve_{tx_id}"),
        types.InlineKeyboardButton(text="Reject ❌", callback_data=f"tx_reject_{tx_id}")
    )
    # Ideally send the actual photo using S3 presigned URL.
    # For simplicity, sending message with inline buttons.
    await bot.send_message(
        chat_id=ADMIN_GROUP_ID,
        text=f"New Payment Receipt!\nTransaction ID: {tx_id}\nAmount: {amount} Nitro\nReceipt: {receipt_url}",
        reply_markup=builder.as_markup()
    )

@dp.callback_query(F.data.startswith("tx_"))
async def handle_tx_decision(callback: types.CallbackQuery):
    action, tx_id_str = callback.data.split("_")[1:3]
    tx_id = int(tx_id_str)

    async with async_session() as db:
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
            await bot.send_message(tx.user_id, TRANSLATIONS[lang]["tx_approved"].format(tx.amount))
            await callback.message.edit_text(callback.message.text + "\n\nStatus: APPROVED ✅")

        elif action == "reject":
            tx.status = "rejected"
            await db.commit()
            await bot.send_message(tx.user_id, TRANSLATIONS[lang]["tx_rejected"].format(tx.amount))
            await callback.message.edit_text(callback.message.text + "\n\nStatus: REJECTED ❌")

    await callback.answer()
