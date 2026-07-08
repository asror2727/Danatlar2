from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.exceptions import TelegramBadRequest

import database as db
import keyboards as kb
from states import ChannelLink

router = Router(name="channel")

ASK_FORWARD_TEXT = (
    "Kanalingizni tizimga ulash uchun:\n\n"
    "1️⃣ Ushbu botni kanalingizga <b>to'liq admin</b> qilib qo'shing.\n"
    "2️⃣ Shundan so'ng kanalingizdagi <b>istalgan bitta post</b>ni (video, rasm yoki matn) "
    "shu chatga forward qiling yoki kanal havolasini yuboring.\n\n"
    "Bot avtomatik tekshirib, kanalni ulaydi."
)


@router.message(F.text == "📡 Kanalim")
async def channel_menu(message: Message, state: FSMContext):
    channel = await db.get_channel_by_owner(message.from_user.id)
    if channel and channel["is_verified"]:
        await message.answer(
            f"✅ Kanalingiz ulangan: <b>{channel['title']}</b>\n\n"
            "Quyidagi amallardan birini tanlang:",
            parse_mode="HTML",
            reply_markup=kb.channel_connected_kb(),
        )
        return

    await state.set_state(ChannelLink.waiting_forward)
    await message.answer(ASK_FORWARD_TEXT, parse_mode="HTML")


@router.message(ChannelLink.waiting_forward)
async def handle_channel_proof(message: Message, state: FSMContext, bot: Bot):
    chat_id = None

    if message.forward_from_chat and message.forward_from_chat.type == "channel":
        chat_id = message.forward_from_chat.id
    elif message.text and message.text.strip().startswith(("https://t.me/", "@")):
        raw = message.text.strip()
        chat_id = raw if raw.startswith("@") else "@" + raw.split("t.me/")[-1].strip("/")
    else:
        await message.answer(
            "Iltimos, kanalingizdagi biror postni forward qiling yoki kanal "
            "username/havolasini yuboring (masalan @mening_kanalim)."
        )
        return

    try:
        member = await bot.get_chat_member(chat_id, bot.id)
    except TelegramBadRequest:
        await message.answer(
            "Botni bu kanalda topa olmadim. Botni kanalingizga to'liq admin qilib "
            "qo'shganingizga ishonch hosil qiling va qayta yuboring."
        )
        return

    if member.status not in ("administrator", "creator"):
        await message.answer(
            "Bot hali kanalingizda admin emas. Iltimos, botga to'liq admin huquqini bering "
            "va shu yerga qaytadan biror post yuboring."
        )
        return

    chat = await bot.get_chat(chat_id)
    await db.add_channel(message.from_user.id, chat.id, chat.title or "", chat.username or "")

    await state.clear()
    channel = await db.get_channel_by_owner(message.from_user.id)
    await message.answer(
        f"✅ Kanalingiz tasdiqlandi!\n\n"
        f"Kanalingiz ulandi: <b>{chat.title}</b>\n\n"
        "Endi quyidagilardan birini tanlashingiz mumkin:",
        parse_mode="HTML",
        reply_markup=kb.channel_connected_kb(),
    )


@router.callback_query(F.data == "channel_info")
async def channel_info(callback: CallbackQuery):
    channel = await db.get_channel_by_owner(callback.from_user.id)
    if not channel:
        await callback.answer("Kanal topilmadi", show_alert=True)
        return
    total = await db.get_channel_total(channel["id"])
    await callback.message.answer(
        f"ℹ️ <b>{channel['title']}</b>\n"
        f"Username: @{channel['username'] or '—'}\n"
        f"Jami yig'ilgan: {total:,} so'm".replace(",", " "),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "back_main")
async def back_main(callback: CallbackQuery):
    await callback.message.answer("Asosiy menyu:", reply_markup=kb.main_menu_kb())
    await callback.answer()
