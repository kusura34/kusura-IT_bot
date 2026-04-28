# Telegram бот-визитка (aiogram + Firestore)

Личный Telegram-бот веб-разработчика для:
- показа портфолио
- сбора заявок
- демонстрации автоматизации через webhook
- ответов на FAQ

## Быстрый старт

1. Создайте виртуальное окружение и установите зависимости:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Создайте `.env` из примера:

```bash
cp .env.example .env
```

3. Заполните `.env` и запустите:

```bash
python bot.py
```

## Webhook endpoint для демо-заказов

Бот поднимает HTTP endpoint:

`POST /demo-webhook`

По умолчанию адрес:

`http://127.0.0.1:8081/demo-webhook`

Пример payload:

```json
{
  "user_id": 123456789,
  "order_id": "A-1001",
  "amount": 2490,
  "status": "paid"
}
```

Если в payload есть `user_id`, бот отправит пользователю уведомление о мгновенной обработке заказа.

## Firestore

Бот использует Firebase Firestore как основное хранилище.
Коллекции:
- users
- projects
- leads
- faq
- demo_logs
- settings
- ready_solutions
