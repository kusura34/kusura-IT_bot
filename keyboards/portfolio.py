from aiogram.utils.keyboard import InlineKeyboardBuilder


def project_card_keyboard(demo_url: str, github_url: str | None = None):
    kb = InlineKeyboardBuilder()
    kb.button(text="Открыть демо", url=demo_url)
    if github_url:
        kb.button(text="GitHub", url=github_url)
    kb.button(text="⬅ Назад", callback_data="nav:back:main")
    kb.button(text="🏠 Главное меню", callback_data="nav:home")
    kb.adjust(2, 2)
    return kb.as_markup()


def solutions_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="⬅ Назад", callback_data="nav:back:main")
    kb.button(text="🏠 Главное меню", callback_data="nav:home")
    kb.adjust(2)
    return kb.as_markup()
