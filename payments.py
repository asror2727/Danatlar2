from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

import database as db
import keyboards as kb
from states import DonateFlow
from payments import click as click_pay
from payments import payme as payme_pay

router = Router(name="payments")


async def start_donate_flow(message: Message, state: FSMContext, post_id: int):
    post = await db.get_post(post_id)
    if not post:
        await message.answer("Bu post topilmadi yoki o'chirilgan.")
        return

    await state.set_state(DonateFlow.waiting_name)
    await state.update_data(post_id=post_id, channel_id=post["channel_id"])
    await message.answer(
        f"💚 <b>{post['title']}</b> uchun donat qilyapsiz.\n\n"
        "Ismingizni kiriting (yoki 'Noma'lum' deb yozing):",
        parse_mode="HTML",
    )


async def show_comments(message: Message, post_id: int):
    post = await db.get_post(post_id)
    if not post:
        await message.answer("Bu post topilmadi.")
        return

    comments = await db.get_post_comments(post_id)
    if not comments:
        await message.answer("Bu post ostida hali izohlar yo'q.")
        return

    lines = [f"💬 <b>{post['title']}</b> — izohlar:\n"]
    for c in comments:
        lines.append(f"• {c['donor_name']} ({c['amount']:,} so'm): {c['comment']}".replace(",", " "))
    await message.answer("\n".join(lines), parse_mode="HTML")


@router.message(DonateFlow.waiting_name)
async def receive_name(message: Message, state: FSMContext):
    await state.update_data(donor_name=message.text.strip())
    await state.set_state(DonateFlow.waiting_comment)
    await message.answer("Izohingizni kiriting (bo'lmasa '-' deb yuboring):")


@router.message(DonateFlow.waiting_comment)
async def receive_comment(message: Message, state: FSMContext):
    comment = message.text.strip()
    await state.update_data(comment="" if comment == "-" else comment)
    await state.set_state(DonateFlow.waiting_amount)
    await message.answer("To'lov miqdorini kiriting (so'mda, faqat raqam. Masalan: 20000):")


@router.message(DonateFlow.waiting_amount)
async def receive_amount(message: Message, state: FSMContext):
    raw = message.text.strip().replace(" ", "")
    if not raw.isdigit() or int(raw) <= 0:
        await message.answer("Iltimos, to'g'ri summa kiriting. Masalan: 20000")
        return

    await state.update_data(amount=int(raw))
    await state.set_state(DonateFlow.waiting_provider)
    await message.answer("To'lov usulini tanlang:", reply_markup=kb.provider_choice_kb())


@router.callback_query(DonateFlow.waiting_provider, F.data.in_(["pay_click", "pay_payme"]))
async def choose_provider(callback: CallbackQuery, state: FSMContext):
    provider = "click" if callback.data == "pay_click" else "payme"
    data = await state.get_data()

    payment_id = await db.create_payment(
        channel_id=data["channel_id"],
        post_id=data["post_id"],
        donor_tg_id=callback.from_user.id,
        donor_name=data.get("donor_name", "Noma'lum"),
        comment=data.get("comment", ""),
        amount=data["amount"],
        provider=provider,
    )

    if provider == "click":
        url = click_pay.generate_pay_url(payment_id, data["amount"])
    else:
        url = payme_pay.generate_pay_url(payment_id, data["amount"])

    await callback.message.answer(
        f"💳 {data['amount']:,} so'm to'lov uchun havola tayyor:".replace(",", " "),
        reply_markup=kb.pay_link_kb(url, provider),
    )
    await state.clear()
    await callback.answer()
