import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@localhost/nitrodb")
engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

from models import User, Transaction

BOT_TOKEN = os.getenv("BOT_TOKEN", "REPLACE_WITH_YOUR_TOKEN")
ADMIN_GROUP_ID = os.getenv("ADMIN_GROUP_ID", "-1000000000")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

TRANSLATIONS = {
    "en": {
        "welcome": "Welcome to Nitro Bot!\nLaunch the Mini App to start.",
        "tx_approved": "Your receipt for {} Nitro has been approved!\nCredits added.",
        "tx_rejected": "Your receipt for {} Nitro was rejected.\nPlease contact support."
    },
    "fa": {
        "welcome": "به ربات نیترو خوش آمدید!\nمینی‌اپ را باز کنید.",
        "tx_approved": "رسید شما برای {} نیترو تایید شد!\nاعتبار اضافه شد.",
        "tx_rejected": "رسید شما برای {} نیترو رد شد.\nلطفا با پشتیبانی تماس بگیرید."
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
                language_preference="fa"
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

async def notify_admin_new_receipt(tx_id: int, amount: int, payment_method: str, receipt_url: str):
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(text="Approve ✅", callback_data=f"tx_approve_{tx_id}"),
        types.InlineKeyboardButton(text="Reject ❌", callback_data=f"tx_reject_{tx_id}")
    )
    
    await bot.send_message(
        chat_id=ADMIN_GROUP_ID,
        text=f"New Payment Receipt!\nTransaction ID: {tx_id}\nMethod: {payment_method.upper()}\nAmount: {amount} Nitro\nReceipt Link: {receipt_url}",
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