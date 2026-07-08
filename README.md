# DanatlarBot (Click + Payme)

Telegram kanal egalari uchun donat (qo'llab-quvvatlash to'lovi) yig'ish boti.

## Imkoniyatlari

- `/start` — asosiy menyu (Kanalim, Hisobim, Xizmat shartlari, To'lovlar, Support)
- **Kanalim** — kanalni botga admin qilib ulash (forward orqali tasdiqlash)
- **Post joylash** — rasm/matn/video/fayl qabul qiladi, nom so'raydi, to'lov turini
  tanlashni taklif qiladi (shu post uchun / umumiy / ko'rsatilmasin), so'ng kanalga
  "💚 Donat qilish" va "💬 Izohlar" tugmalari bilan chop etadi
- **Donat qilish** — donator ismi, izohi, summasi so'raladi, Click yoki Payme
  orqali to'lov havolasi generatsiya qilinadi
- **Webhook server** — Click (Prepare/Complete) va Payme (JSON-RPC) to'lov
  tasdiqlarini qabul qiladi va bazada to'lovni "paid" deb belgilaydi

## Render.com'ga joylash

1. GitHub repo'ni Render'ga ulang, **Web Service** yarating.
2. **Build Command:** `pip install -r requirements.txt`
3. **Start Command:** `python bot.py`
4. **Environment** bo'limida `.env.example`dagi barcha o'zgaruvchilarni
   (BOT_TOKEN, BOT_USERNAME va h.k.) qo'lda kiriting (Render `.env` faylini
   o'qimaydi, har birini alohida Environment Variable sifatida qo'shish kerak).
5. Repo ichida `runtime.txt` fayli bor — bu Render'ga aniq Python 3.11.9
   versiyasidan foydalanishni buyuradi. **Bu faylni o'chirmang** — aks holda
   Render eng yangi Python (masalan 3.14) tanlab, `pydantic-core` kabi
   kutubxonalar qurilishda xatolik berishi mumkin (chunki ularning tayyor
   paketi hali yangi Python uchun chiqmagan bo'ladi).

## Talablar

- Python 3.8 yoki undan yuqori
- `pip install -r requirements.txt`

## Test qilish (haqiqiy Click/Payme kalitlarisiz)

`.env` faylida `TEST_MODE=true` qoldiring (standart holat). Bu holatda:
- Bot to'liq ishlaydi: kanal ulash, post joylash, donat oqimi
- Click/Payme kalitlari bo'sh bo'lsa ham xatolik bermaydi
- "Donat qilish" bosilganda haqiqiy to'lov o'rniga test havola qaytadi

Haqiqiy to'lovlarni ulash vaqti kelganda `.env`da `TEST_MODE=false` qiling
va barcha `CLICK_*`/`PAYME_*` qiymatlarini to'ldiring.

## O'rnatish

```bash
cd danat_bot
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

`.env` faylini oching va quyidagilarni to'ldiring:

- `BOT_TOKEN` — @BotFather'dan olingan token
- `BOT_USERNAME` — botingiz username'i (deep-link uchun kerak)
- `CLICK_*` — https://merchant.click.uz dagi merchant kabinetdan
- `PAYME_*` — https://business.payme.uz dagi merchant kabinetdan

## Ishga tushirish

```bash
python bot.py
```

Bu buyruq bitta jarayonda ikkalasini ham ishga tushiradi:
1. Telegram botni (polling rejimida)
2. Click/Payme webhook serverini (`webhook_server.py`, standart port: 8080)

## Muhim: Webhook serverni tashqi dunyoga ochish

Click va Payme to'lov natijasini tasdiqlash uchun sizning serveringizga
**HTTPS orqali ochiq (public)** manzildan POST so'rov yuboradi. Shuning
uchun productionda:

1. Serveringizda domen va SSL sertifikat bo'lishi kerak (masalan nginx + certbot)
2. nginx orqali `https://sizning-domen.uz/click/prepare`,
   `https://sizning-domen.uz/click/complete`, `https://sizning-domen.uz/payme`
   manzillarini `webhook_server.py`dagi 8080-portga proxy qiling
3. Click merchant kabinetida "Complete/Prepare URL", Payme kabinetida
   "Callback URL" sifatida shu manzillarni ko'rsating

Lokal test qilish uchun `ngrok` yoki shunga o'xshash tunnel xizmatidan
foydalanishingiz mumkin.

## Mini App (WebApp) sozlash

`mini_app/` papkasida donat formasi (`index.html`) va izohlar sahifasi
(`comments.html`) bor. Ular `webhook_server.py` orqali statik fayl sifatida
xizmat qiladi (`/`, `/api/post/<id>`, `/api/comments/<id>`, `/api/donate`
bilan bir xil serverda, bir xil portda).

1. Serveringizni HTTPS domenga chiqaring (masalan `https://sizning-domen.uz`),
   nginx orqali `webhook_server.py`ning portiga (standart 8080) proxy qiling.
2. @BotFather'ga o'ting → botingizni tanlang → **Bot Settings → Mini App**
   → **Configure Mini App** yoki `/newapp` buyrug'i orqali **ikkita** Mini App yarating:
   - short name: `donate` → App URL: `https://sizning-domen.uz/index.html`
   - short name: `comments` → App URL: `https://sizning-domen.uz/comments.html`
3. `.env` faylida `MINI_APP_DONATE_NAME` va `MINI_APP_COMMENTS_NAME`
   qiymatlarini shu short name'lar bilan bir xil qilib qo'ying.

Shundan so'ng post joylanganda kanaldagi "💚 Donat qilish" va "💬 Izohlar"
tugmalari `https://t.me/BotUsername/donate?startapp=<post_id>` formatidagi
havolalar bo'lib, bosilganda to'g'ridan-to'g'ri Mini App'ni ochadi — bot
chatiga chiqmaydi.



```
danat_bot/
├── bot.py                 # asosiy ishga tushirish nuqtasi
├── config.py               # .env dan sozlamalarni o'qish
├── database.py              # SQLite (aiosqlite) bilan ishlash
├── states.py                # FSM holatlari
├── keyboards.py              # reply/inline klaviaturalar
├── webhook_server.py         # Click/Payme uchun aiohttp server
├── handlers/
│   ├── start.py             # /start, asosiy menyu
│   ├── channel.py           # kanal ulash
│   ├── posts.py              # post joylash oqimi
│   ├── payments.py           # donat qilish oqimi (bot ichida, zaxira variant), izohlar
│   └── account.py            # hisobim
├── payments/
│   ├── click.py               # Click.uz integratsiyasi
│   └── payme.py                # Payme integratsiyasi
└── mini_app/
    ├── index.html               # donat qilish Mini App sahifasi
    ├── comments.html             # izohlar Mini App sahifasi
    ├── terms.html                 # xizmat shartlari
    ├── style.css                   # Telegram theme'ga moslashgan uslub
    └── app.js                      # donat formasi mantiqi
```

## Diqqat — nima keyingi bosqichda kerak bo'ladi

- `payments/payme.py` dagi `perform_transaction`/`cancel_transaction`
  soddalashtirilgan holatda — productionda Payme o'z ichki `transaction id`
  (params["id"]) bilan sizning `order_id` orasida alohida mapping jadvali
  saqlash tavsiya etiladi (hozir ular bir xil deb faraz qilingan).
- Hozircha "izohlar" va "hisobot" botning o'zida oddiy matn ko'rinishida.
  Agar to'liq WebApp (mini-app) frontend kerak bo'lsa, buni alohida
  loyihada (masalan React + Telegram WebApp SDK) qurish tavsiya etiladi —
  bot backend endpointlarini shu bazaga ulash mumkin.
- Real muhitda xatoliklarni ushlash (try/except), loglash va rate-limit
  qo'shishni unutmang.
