from aiogram import Router, F
from aiogram.types import CallbackQuery

from keyboards.faq import faq_keyboard
from keyboards.navigation import back_home_keyboard

router = Router()


@router.callback_query(F.data == "menu:faq")
async def show_faq(callback: CallbackQuery, db):
    items = await db.list_faq_items()
    data = [(item["id"], item["question"]) for item in items]
    await callback.message.answer("Выберите вопрос:", reply_markup=faq_keyboard(data))
    await callback.answer()


@router.callback_query(F.data.startswith("faq:item:"))
async def faq_item(callback: CallbackQuery, db):
    faq_id = int(callback.data.split(":")[-1])
    item = await db.get_faq(faq_id)
    if not item:
        await callback.answer("Вопрос не найден", show_alert=True)
        return
    await callback.message.answer(f"<b>{item['question']}</b>\n\n{item['answer']}", reply_markup=back_home_keyboard("main"))
    await callback.answer()
