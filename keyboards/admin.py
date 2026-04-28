from aiogram.utils.keyboard import InlineKeyboardBuilder


def admin_menu_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="Портфолио", callback_data="admin:portfolio")
    kb.button(text="FAQ", callback_data="admin:faq")
    kb.button(text="Контакты", callback_data="admin:contacts")
    kb.button(text="Тексты", callback_data="admin:texts")
    kb.button(text="Настройки", callback_data="admin:settings")
    kb.button(text="Заявки", callback_data="admin:leads")
    kb.button(text="Готовые решения", callback_data="admin:solutions")
    kb.button(text="Статистика", callback_data="admin:stats")
    kb.button(text="Экспорт заявок CSV", callback_data="admin:leads:csv")
    kb.button(text="🏠 Главное меню", callback_data="nav:home")
    kb.adjust(1)
    return kb.as_markup()


def portfolio_cms_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="Добавить проект", callback_data="admin:projects:add")
    kb.button(text="Редактировать проект", callback_data="admin:projects:edit")
    kb.button(text="Удалить проект", callback_data="admin:projects:delete")
    kb.button(text="Скрыть/Показать", callback_data="admin:projects:toggle")
    kb.button(text="Порядок отображения", callback_data="admin:projects:order")
    kb.button(text="⬅ Назад", callback_data="admin:back")
    kb.adjust(1)
    return kb.as_markup()


def faq_cms_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="Добавить вопрос", callback_data="admin:faq:add")
    kb.button(text="Редактировать вопрос", callback_data="admin:faq:edit")
    kb.button(text="Удалить вопрос", callback_data="admin:faq:delete")
    kb.button(text="⬅ Назад", callback_data="admin:back")
    kb.adjust(1)
    return kb.as_markup()


def leads_cms_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="Список всех заявок", callback_data="admin:leads:list")
    kb.button(text="Firestore заказы", callback_data="admin:leads:firestore")
    kb.button(text="Просмотр детали", callback_data="admin:leads:view")
    kb.button(text="Пометить обработано", callback_data="admin:leads:process")
    kb.button(text="Удалить заявку", callback_data="admin:leads:delete")
    kb.button(text="⬅ Назад", callback_data="admin:back")
    kb.adjust(1)
    return kb.as_markup()


def solutions_cms_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="Добавить решение", callback_data="admin:solutions:add")
    kb.button(text="Редактировать решение", callback_data="admin:solutions:edit")
    kb.button(text="Удалить решение", callback_data="admin:solutions:delete")
    kb.button(text="⬅ Назад", callback_data="admin:back")
    kb.adjust(1)
    return kb.as_markup()


def id_select_keyboard(prefix: str, ids: list[int]):
    kb = InlineKeyboardBuilder()
    for item_id in ids:
        kb.button(text=f"#{item_id}", callback_data=f"{prefix}:{item_id}")
    kb.button(text="⬅ Назад", callback_data="admin:back")
    kb.adjust(4)
    return kb.as_markup()


def yes_no_toggle_keyboard(prefix: str):
    kb = InlineKeyboardBuilder()
    kb.button(text="Вкл", callback_data=f"{prefix}:on")
    kb.button(text="Выкл", callback_data=f"{prefix}:off")
    kb.button(text="⬅ Назад", callback_data="admin:back")
    kb.adjust(2, 1)
    return kb.as_markup()


def settings_cms_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="Изменить ссылку демо", callback_data="admin:setting:edit_demo_url")
    kb.button(text="Включить демо", callback_data="admin:setting:demo:on")
    kb.button(text="Отключить демо", callback_data="admin:setting:demo:off")
    kb.button(text="⬅ Назад", callback_data="admin:back")
    kb.adjust(1)
    return kb.as_markup()


def project_edit_select_keyboard(items: list[tuple[int, str]]):
    kb = InlineKeyboardBuilder()
    for project_id, title in items:
        kb.button(text=f"#{project_id} {title}", callback_data=f"admin:project:editpick:{project_id}")
    kb.button(text="⬅ Назад", callback_data="admin:back")
    kb.adjust(1)
    return kb.as_markup()


def project_edit_field_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="Название", callback_data="admin:project:field:title")
    kb.button(text="Описание", callback_data="admin:project:field:description")
    kb.button(text="Стек", callback_data="admin:project:field:stack")
    kb.button(text="Фото (путь)", callback_data="admin:project:field:image")
    kb.button(text="Demo URL", callback_data="admin:project:field:demo_url")
    kb.button(text="GitHub URL", callback_data="admin:project:field:github_url")
    kb.button(text="⬅ Назад", callback_data="admin:back")
    kb.adjust(1)
    return kb.as_markup()


def contacts_edit_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="Telegram", callback_data="admin:contact:pick:telegram")
    kb.button(text="WhatsApp", callback_data="admin:contact:pick:whatsapp")
    kb.button(text="Email", callback_data="admin:contact:pick:email")
    kb.button(text="⬅ Назад", callback_data="admin:back")
    kb.adjust(1)
    return kb.as_markup()


def texts_edit_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="Приветствие", callback_data="admin:text:pick:welcome")
    kb.button(text="После заявки", callback_data="admin:text:pick:thanks_after_brief")
    kb.button(text="Текст демо", callback_data="admin:text:pick:demo_intro")
    kb.button(text="Успех демо", callback_data="admin:text:pick:demo_success")
    kb.button(text="Напоминание", callback_data="admin:text:pick:reminder")
    kb.button(text="⬅ Назад", callback_data="admin:back")
    kb.adjust(1)
    return kb.as_markup()


def faq_select_keyboard(items: list[tuple[int, str]], prefix: str):
    kb = InlineKeyboardBuilder()
    for faq_id, question in items:
        kb.button(text=f"#{faq_id} {question[:40]}", callback_data=f"{prefix}:{faq_id}")
    kb.button(text="⬅ Назад", callback_data="admin:back")
    kb.adjust(1)
    return kb.as_markup()
