import os
from dotenv import load_dotenv

load_dotenv()


def _get(name: str, default: str = "") -> str:
    return os.getenv(name, default)


BOT_TOKEN = _get("BOT_TOKEN")
BOT_USERNAME = _get("BOT_USERNAME", "DanatlarBot")
DB_PATH = _get("DB_PATH", "danat_bot.db")

# TEST_MODE=true bo'lsa: Click/Payme kalitlari to'ldirilmagan bo'lsa ham
# bot ishlab turadi, to'lov havolalari o'rniga test (soxta) havola qaytadi.
# Haqiqiy to'lovlarni tekshirish uchun TEST_MODE=false qiling va barcha
# CLICK_*/PAYME_* qiymatlarini to'ldiring.
TEST_MODE = _get("TEST_MODE", "true").lower() == "true"

# Click.uz
CLICK_SERVICE_ID = _get("CLICK_SERVICE_ID")
CLICK_MERCHANT_ID = _get("CLICK_MERCHANT_ID")
CLICK_MERCHANT_USER_ID = _get("CLICK_MERCHANT_USER_ID")
CLICK_SECRET_KEY = _get("CLICK_SECRET_KEY")
CLICK_RETURN_URL = _get("CLICK_RETURN_URL", "https://t.me/")

# Payme
PAYME_MERCHANT_ID = _get("PAYME_MERCHANT_ID")
PAYME_KEY = _get("PAYME_KEY")
PAYME_IS_TEST = _get("PAYME_IS_TEST", "true").lower() == "true"

# Webhook server (Click/Payme callbacklari uchun)
WEBHOOK_HOST = _get("WEBHOOK_HOST", "0.0.0.0")
WEBHOOK_PORT = int(_get("WEBHOOK_PORT", "8080"))

# Mini-app (WebApp) qaysi domenda joylashganini ko'rsatadi, masalan:
# https://sizning-domen.uz  (oxirida / bo'lmasin)
MINI_APP_BASE_URL = _get("MINI_APP_BASE_URL", "https://example.com")

# BotFather -> /newapp orqali botga biriktirilgan Mini App'larning "short name"lari.
# Bitta botga bir nechta Mini App biriktirish mumkin, har biri o'z URL manziliga ega bo'ladi.
# Masalan link https://t.me/DanatlarBot/donate bo'lsa, MINI_APP_DONATE_NAME="donate"
MINI_APP_DONATE_NAME = _get("MINI_APP_DONATE_NAME", "donate")
MINI_APP_COMMENTS_NAME = _get("MINI_APP_COMMENTS_NAME", "comments")

if not BOT_TOKEN:
    raise RuntimeError(
        "BOT_TOKEN topilmadi!\n"
        "Yechim: loyiha papkasida '.env' fayl yarating (.env.example dan nusxa oling) "
        "va ichiga @BotFather'dan olingan tokenni BOT_TOKEN=... qilib kiriting.\n"
        "Masalan: cp .env.example .env    (keyin .env faylini oching va tahrirlang)"
    )
