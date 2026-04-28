from aiogram import Router, F
from aiogram.types import CallbackQuery

from keyboards.main_menu import get_main_menu_keyboard

router = Router()


@router.callback_query(F.data == "nav:home")
async def nav_home(callback: CallbackQuery, db):
    text = await db.get_setting("text_welcome")
    await callback.message.answer(text, reply_markup=get_main_menu_keyboard())
    await callback.answer()


@router.callback_query(F.data.startswith("nav:back:"))
async def nav_back(callback: CallbackQuery, db):
    target = callback.data.split(":", 2)[2]
    if target == "main":
        text = await db.get_setting("text_welcome")
        await callback.message.answer(text, reply_markup=get_main_menu_keyboard())
    else:
        await callback.message.answer("Возврат выполнен", reply_markup=get_main_menu_keyboard())
    await callback.answer()
