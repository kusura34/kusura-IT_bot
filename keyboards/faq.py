from aiogram.utils.keyboard import InlineKeyboardBuilder


def faq_keyboard(items: list[tuple[int, str]]):
    kb = InlineKeyboardBuilder()
    for faq_id, question in items:
        kb.button(text=question, callback_data=f"faq:item:{faq_id}")
    kb.button(text="⬅ Назад", callback_data="nav:back:main")
    kb.button(text="🏠 Главное меню", callback_data="nav:home")
    kb.adjust(1)
    return kb.as_markup()
