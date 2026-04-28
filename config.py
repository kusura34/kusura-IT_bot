import os
from dataclasses import dataclass


@dataclass
class Config:
    bot_token: str
    admin_id: int
    firebase_credentials: str
    demo_url: str
    contact_telegram: str
    contact_whatsapp: str
    contact_email: str
    webhook_host: str
    webhook_port: int


def _required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"{name} is not set")
    return value


def load_config() -> Config:
    token = _required_env("BOT_TOKEN")
    admin_id = int(_required_env("ADMIN_ID"))
    firebase_credentials = _required_env("FIREBASE_CREDENTIALS")

    return Config(
        bot_token=token,
        admin_id=admin_id,
        firebase_credentials=firebase_credentials,
        demo_url=os.getenv("DEMO_URL", "https://dar34116600211--dar-al-halwa-925db.europe-west4.hosted.app/"),
        contact_telegram=os.getenv("CONTACT_TELEGRAM", "@rekurt6011"),
        contact_whatsapp=os.getenv("CONTACT_WHATSAPP", "+79081546937"),
        contact_email=os.getenv("CONTACT_EMAIL", "litetsabr@gmail.com"),
        webhook_host=os.getenv("WEBHOOK_HOST", "0.0.0.0"),
        webhook_port=int(os.getenv("PORT", os.getenv("WEBHOOK_PORT", "8081"))),
    )
