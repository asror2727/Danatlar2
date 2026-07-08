from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton,
)
from config import BOT_USERNAME, MINI_APP_DONATE_NAME, MINI_APP_COMMENTS_NAME


def main_menu_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📡 Kanalim")],
            [KeyboardButton(text="👤 Hisobim"), KeyboardButton(text="💳 To'lovlar")],
            [KeyboardButton(text="📄 Xizmat shartlari"), KeyboardButton(text="🆘 Support")],
        ],
        resize_keyboard=True,
    )


def channel_connected_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📝 Post joylash", callback_data="post_new")],
            [InlineKeyboardButton(text="ℹ️ Kanal haqida", callback_data="channel_info")],
            [InlineKeyboardButton(text="⬅️ Ortga qaytish", callback_data="back_main")],
        ]
    )


def post_content_confirm_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="❌ Bekor qilish", callback_data="post_cancel")]]
    )


def payment_scope_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="1️⃣ Shu post uchun", callback_data="scope_post")],
            [InlineKeyboardButton(text="2️⃣ Umumiy to'lovlar", callback_data="scope_general")],
            [InlineKeyboardButton(text="3️⃣ Ko'rsatilmasin", callback_data="scope_hidden")],
            [InlineKeyboardButton(text="4️⃣ Bekor qilish", callback_data="post_cancel")],
        ]
    )


def yes_no_kb(prefix: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Ha", callback_data=f"{prefix}_yes"),
                InlineKeyboardButton(text="Yo'q", callback_data=f"{prefix}_no"),
            ]
        ]
    )


def channel_post_donate_kb(post_id: int) -> InlineKeyboardMarkup:
    """Kanaldagi postga qo'shiladigan 'Donat qilish' va 'Izohlar' tugmalari.
    Bular Telegram'ning 'Direct link Mini App' formatida (t.me/bot/appname?startapp=...)
    — bu format oddiy URL bo'lgani uchun kanal postlarida ham ishlaydi va
    bosilganda Mini App'ni to'g'ridan-to'g'ri ochadi."""
    donate_url = f"https://t.me/{BOT_USERNAME}/{MINI_APP_DONATE_NAME}?startapp={post_id}"
    comments_url = f"https://t.me/{BOT_USERNAME}/{MINI_APP_COMMENTS_NAME}?startapp={post_id}"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💚 Donat qilish", url=donate_url)],
            [InlineKeyboardButton(text="💬 Izohlar", url=comments_url)],
        ]
    )


def provider_choice_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💠 Click", callback_data="pay_click")],
            [InlineKeyboardButton(text="💠 Payme", callback_data="pay_payme")],
        ]
    )


def pay_link_kb(url: str, provider: str) -> InlineKeyboardMarkup:
    label = "Click orqali to'lash" if provider == "click" else "Payme orqali to'lash"
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=f"💳 {label}", url=url)]]
    )


def terms_agree_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="✅ Roziman", callback_data="terms_ok")]]
    )
