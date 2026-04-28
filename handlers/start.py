from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from keyboards.main_menu import get_main_menu_keyboard

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, db):
    if message.from_user:
        await db.create_or_ignore_user(message.from_user.id, message.from_user.username, message.from_user.full_name)
    welcome_text = await db.get_setting("text_welcome")
    await message.answer(welcome_text, reply_markup=get_main_menu_keyboard())
