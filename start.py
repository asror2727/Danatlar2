from aiogram import Router, F
from aiogram.filters import CommandStart, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

import database as db
import keyboards as kb

router = Router(name="start")

WELCOME_TEXT = (
    "Aslomu alaykum! 👋\n\n"
    "Bu bot orqali kanalingizga donat (qo'llab-quvvatlash to'lovi) tizimini ulashingiz mumkin.\n\n"
    "Pastdagi tugmalar orqali botni boshqarishingiz mumkin:\n"
    "📡 Kanalim — kanalingizni ulash va postlar joylash\n"
    "👤 Hisobim — yig'ilgan to'lovlar statistikasi\n"
    "📄 Xizmat shartlari — foydalanish qoidalari\n"
    "💳 To'lovlar — to'lov usullari haqida\n"
    "🆘 Support — yordam"
)


@router.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject, state: FSMContext):
    await db.upsert_user(message.from_user.id, message.from_user.username or "", message.from_user.full_name)

    payload = command.args
    if payload:
        # Deep-link orqali kelgan: donate_<post_id> yoki comments_<post_id>
        if payload.startswith("donate_"):
            from handlers.payments import start_donate_flow
            post_id = int(payload.replace("donate_", ""))
            await start_donate_flow(message, state, post_id)
            return
        if payload.startswith("comments_"):
            from handlers.payments import show_comments
            post_id = int(payload.replace("comments_", ""))
            await show_comments(message, post_id)
            return

    await message.answer(WELCOME_TEXT, reply_markup=kb.main_menu_kb())


@router.message(F.text == "📄 Xizmat shartlari")
async def terms(message: Message):
    await message.answer(
        "📄 <b>Xizmat shartlari va qoidalari</b>\n\n"
        "1. Bot orqali kanalingizga donat tizimini ulaysiz.\n"
        "2. Yig'ilgan mablag'lar Click/Payme orqali to'g'ridan-to'g'ri sizga tegishli hisobga o'tadi.\n"
        "3. Bot suiiste'mol qilinganda (firibgarlik, noqonuniy kontent) xizmatdan foydalanish "
        "to'xtatilishi mumkin.\n"
        "4. Batafsil shartlar bilan tanishish uchun @support bilan bog'laning.",
        parse_mode="HTML",
    )


@router.message(F.text == "🆘 Support")
async def support(message: Message):
    await message.answer(
        "🆘 Savolingiz bo'lsa, quyidagi manzilga yozing: @your_support_username\n"
        "Ish vaqti: har kuni 09:00 — 22:00"
    )


@router.message(F.text == "💳 To'lovlar")
async def payments_info(message: Message):
    await message.answer(
        "💳 <b>To'lov usullari</b>\n\n"
        "Bot orqali Click va Payme orqali to'lov qabul qilinadi.\n"
        "Donatorlar postdagi \"💚 Donat qilish\" tugmasi orqali to'lov qiladi.",
        parse_mode="HTML",
    )
