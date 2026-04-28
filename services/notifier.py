from aiogram import Bot


async def notify_admin_new_lead(bot: Bot, admin_id: int, lead: dict) -> None:
    text = (
        "<b>Новая заявка:</b>\n\n"
        f"ID: #{lead['id']}\n"
        f"Тип проекта: {lead['project_type']}\n"
        f"Оплата: {lead['payment']}\n"
        f"Дизайн: {lead['design']}\n"
        f"Админка: {lead['admin_panel']}\n"
        f"Бюджет: {lead['budget']}\n"
        f"Тег: {lead['tag']}\n"
        f"Контакт: {lead['contact']}"
    )
    await bot.send_message(admin_id, text)
