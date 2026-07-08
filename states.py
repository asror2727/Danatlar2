from aiogram.fsm.state import State, StatesGroup


class ChannelLink(StatesGroup):
    waiting_forward = State()          # kanaldan video/hovola/forward kutilmoqda


class PostCreate(StatesGroup):
    waiting_content = State()          # rasm/matn/video/fayl kutilmoqda
    waiting_title = State()            # post nomi kutilmoqda
    waiting_scope_choice = State()     # shu post / umumiy / korsatilmasin
    waiting_general_visibility = State()  # umumiy tanlansa - obunachilarga korinsinmi


class DonateFlow(StatesGroup):
    waiting_name = State()             # donat qiluvchi ismi (agar toggle yoqilgan bo'lsa)
    waiting_comment = State()          # izoh
    waiting_amount = State()           # to'lov miqdori
    waiting_provider = State()         # click / payme tanlash
