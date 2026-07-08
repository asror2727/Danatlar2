from aiogram import Router, F
from aiogram.types import Message

import database as db

router = Router(name="account")


@router.message(F.text == "👤 Hisobim")
async def account(message: Message):
    channel = await db.get_channel_by_owner(message.from_user.id)
    if not channel:
        await message.answer("Hozircha kanalingiz ulanmagan. Avval 📡 Kanalim bo'limidan kanalingizni ulang.")
        return

    total = await db.get_channel_total(channel["id"])
    await message.answer(
        f"👤 <b>Hisobingiz</b>\n\n"
        f"Kanal: {channel['title']}\n"
        f"Jami yig'ilgan mablag': {total:,} so'm".replace(",", " "),
        parse_mode="HTML",
    )
