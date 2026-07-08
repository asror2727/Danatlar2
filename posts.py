from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

import database as db
import keyboards as kb
from states import PostCreate

router = Router(name="posts")


def _extract_content(message: Message):
    """Kelgan xabardan (rasm/matn/video/fayl) content_type, file_id, text ni ajratib oladi."""
    if message.photo:
        return "photo", message.photo[-1].file_id, message.caption or ""
    if message.video:
        return "video", message.video.file_id, message.caption or ""
    if message.document:
        return "document", message.document.file_id, message.caption or ""
    if message.text:
        return "text", None, message.text
    return None, None, None


@router.callback_query(F.data == "post_new")
async def post_new(callback: CallbackQuery, state: FSMContext):
    channel = await db.get_channel_by_owner(callback.from_user.id)
    if not channel:
        await callback.answer("Avval kanalingizni ulang.", show_alert=True)
        return

    await state.set_state(PostCreate.waiting_content)
    await state.update_data(channel_id=channel["id"])
    await callback.message.answer(
        "Kanalingizga tashlanadigan postni yuboring (rasm, matn, fayl yoki video).",
        reply_markup=kb.post_content_confirm_kb(),
    )
    await callback.answer()


@router.message(PostCreate.waiting_content)
async def receive_content(message: Message, state: FSMContext):
    content_type, file_id, text = _extract_content(message)
    if content_type is None:
        await message.answer("Iltimos, rasm, matn, fayl yoki video yuboring.")
        return

    await state.update_data(content_type=content_type, file_id=file_id, text=text)
    await state.set_state(PostCreate.waiting_title)
    await message.answer("Post uchun nom toping (masalan: Nonga, Kommunal xarajatlar uchun va h.k.)")


@router.message(PostCreate.waiting_title)
async def receive_title(message: Message, state: FSMContext):
    title = message.text.strip() if message.text else "Nomsiz post"
    await state.update_data(title=title)
    await state.set_state(PostCreate.waiting_scope_choice)
    await message.answer(
        f"✅ Avto saqlandi: <b>{title}</b>\n\n"
        "Kanalingizga tashlangan postdan keladigan to'lovlarni qanday hisoblaymiz?",
        parse_mode="HTML",
        reply_markup=kb.payment_scope_kb(),
    )


@router.callback_query(F.data == "post_cancel")
async def post_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer("❌ Post joylash bekor qilindi.")
    await callback.answer()


@router.callback_query(PostCreate.waiting_scope_choice, F.data.startswith("scope_"))
async def choose_scope(callback: CallbackQuery, state: FSMContext, bot: Bot):
    scope = callback.data.replace("scope_", "")  # post | general | hidden
    await state.update_data(payment_scope=scope)

    if scope == "general":
        await state.set_state(PostCreate.waiting_general_visibility)
        await callback.message.answer(
            "Umumiy to'lovlar bo'yicha yozilayotgan xabarlar (izohlar) "
            "kanal obunachilariga ko'rinsinmi?",
            reply_markup=kb.yes_no_kb("genvis"),
        )
        await callback.answer()
        return

    show_to_subs = scope == "post"  # hidden -> False, post -> True
    await _finalize_post(callback.message, state, bot, show_to_subs)
    await callback.answer()


@router.callback_query(PostCreate.waiting_general_visibility, F.data.startswith("genvis_"))
async def choose_general_visibility(callback: CallbackQuery, state: FSMContext, bot: Bot):
    show_to_subs = callback.data.endswith("_yes")
    await _finalize_post(callback.message, state, bot, show_to_subs)
    await callback.answer()


async def _finalize_post(message: Message, state: FSMContext, bot: Bot, show_to_subscribers: bool):
    data = await state.get_data()
    channel = await db.get_channel_by_id(data["channel_id"])

    post_id = await db.create_post(
        channel_id=data["channel_id"],
        owner_tg_id=message.chat.id,
        content_type=data["content_type"],
        file_id=data.get("file_id"),
        text=data.get("text"),
        title=data["title"],
        payment_scope=data["payment_scope"],
        show_to_subscribers=show_to_subscribers,
    )

    markup = kb.channel_post_donate_kb(post_id)
    sent = await _send_to_channel(bot, channel["chat_id"], data, markup)
    await db.set_post_channel_message_id(post_id, sent.message_id)

    await state.clear()
    await message.answer(
        f"🎉 Post kanalingizga muvaffaqiyatli joylandi!\n"
        f"Post nomi: <b>{data['title']}</b>",
        parse_mode="HTML",
    )


async def _send_to_channel(bot: Bot, chat_id: int, data: dict, markup):
    content_type = data["content_type"]
    caption = data.get("text") or ""
    if content_type == "photo":
        return await bot.send_photo(chat_id, data["file_id"], caption=caption, reply_markup=markup)
    if content_type == "video":
        return await bot.send_video(chat_id, data["file_id"], caption=caption, reply_markup=markup)
    if content_type == "document":
        return await bot.send_document(chat_id, data["file_id"], caption=caption, reply_markup=markup)
    return await bot.send_message(chat_id, caption or "—", reply_markup=markup)
