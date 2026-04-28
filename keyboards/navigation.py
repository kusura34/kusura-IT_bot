from aiogram.utils.keyboard import InlineKeyboardBuilder


def back_home_keyboard(back_to: str):
    kb = InlineKeyboardBuilder()
    kb.button(text="⬅ Назад", callback_data=f"nav:back:{back_to}")
    kb.button(text="🏠 Главное меню", callback_data="nav:home")
    kb.adjust(2)
    return kb.as_markup()
