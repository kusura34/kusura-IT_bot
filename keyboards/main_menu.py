from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_main_menu_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="Мои работы", callback_data="menu:portfolio")
    kb.button(text="Рассчитать стоимость", callback_data="menu:brief")
    kb.button(text="Живая демонстрация", callback_data="menu:demo")
    kb.button(text="FAQ", callback_data="menu:faq")
    kb.button(text="Готовые решения", callback_data="menu:solutions")
    kb.button(text="Связаться", callback_data="menu:contact")
    kb.adjust(1)
    return kb.as_markup()
