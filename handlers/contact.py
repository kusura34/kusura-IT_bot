from aiogram import Router, F
from aiogram.types import CallbackQuery

from keyboards.contact import contact_keyboard

router = Router()


@router.callback_query(F.data == "menu:contact")
async def show_contact(callback: CallbackQuery, db):
    user_id = callback.from_user.id if callback.from_user else None
    await db.log_event(user_id, "contact_opened", {})

    tg = await db.get_setting("contact_telegram")
    wa = await db.get_setting("contact_whatsapp")
    email = await db.get_setting("contact_email")

    tg_url = f"https://t.me/{tg.lstrip('@')}"
    text = (
        "<b>Контакты:</b>\n"
        f"Telegram: {tg}\n"
        f"WhatsApp: {wa}\n"
        f"Email: {email}"
    )
    await callback.message.answer(text, reply_markup=contact_keyboard(tg_url))
    await callback.answer()
