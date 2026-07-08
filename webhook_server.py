"""
Bu server ikki vazifani bajaradi:

1) Click/Payme to'lov tizimlaridan keladigan tasdiqlash so'rovlarini qabul qiladi
   (/click/prepare, /click/complete, /payme)
2) Mini-app (Telegram WebApp) uchun statik fayllarni va API endpointlarini beradi
   (/  -> mini_app/index.html, /api/post/<id>, /api/comments/<id>, /api/donate)

Ishga tushirish: python bot.py (ikkalasi birga ko'tariladi) yoki alohida:
python webhook_server.py
"""
import hashlib
import hmac
import json
from pathlib import Path
from urllib.parse import parse_qsl

from aiohttp import web

import config
import database as db
from payments import click as click_pay
from payments import payme as payme_pay

MINI_APP_DIR = Path(__file__).parent / "mini_app"


# ---------------------------------------------------------------------------
# Click webhook
# ---------------------------------------------------------------------------

async def click_prepare(request: web.Request):
    data = await request.post()
    result = await click_pay.handle_prepare(dict(data))
    return web.json_response(result)


async def click_complete(request: web.Request):
    data = await request.post()
    result = await click_pay.handle_complete(dict(data))
    return web.json_response(result)


# ---------------------------------------------------------------------------
# Payme webhook
# ---------------------------------------------------------------------------

async def payme_handler(request: web.Request):
    auth = request.headers.get("Authorization", "")
    if not payme_pay.check_auth(auth):
        return web.json_response(
            {"error": {"code": payme_pay.PERM_DENIED, "message": "Auth failed"}}, status=200
        )

    body = await request.json()
    method = body.get("method")
    params = body.get("params", {})
    req_id = body.get("id")

    handlers = {
        "CheckPerformTransaction": payme_pay.check_perform_transaction,
        "CreateTransaction": payme_pay.create_transaction,
        "PerformTransaction": payme_pay.perform_transaction,
        "CancelTransaction": payme_pay.cancel_transaction,
    }

    handler = handlers.get(method)
    if not handler:
        return web.json_response(
            {"error": {"code": -32601, "message": "Method not found"}, "id": req_id}
        )

    result = await handler(params)
    result["id"] = req_id
    return web.json_response(result)


# ---------------------------------------------------------------------------
# Telegram WebApp initData tekshiruvi
# https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
# ---------------------------------------------------------------------------

def validate_init_data(init_data: str):
    if not init_data:
        return None
    try:
        pairs = dict(parse_qsl(init_data, strict_parsing=True))
        received_hash = pairs.pop("hash", None)
        if not received_hash:
            return None

        data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(pairs.items()))
        secret_key = hmac.new(b"WebAppData", config.BOT_TOKEN.encode(), hashlib.sha256).digest()
        computed_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

        if computed_hash != received_hash:
            return None

        user_raw = pairs.get("user")
        user = json.loads(user_raw) if user_raw else {}
        return {"user": user}
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Mini-app API
# ---------------------------------------------------------------------------

async def api_post_info(request: web.Request):
    post_id = int(request.match_info["post_id"])
    post = await db.get_post(post_id)
    if not post:
        return web.json_response({"error": "not found"}, status=404)

    channel = await db.get_channel_by_id(post["channel_id"])
    return web.json_response(
        {
            "post_title": post["title"],
            "channel_title": channel["title"] if channel else "",
            "channel_username": channel["username"] if channel else "",
            "channel_photo_url": None,  # ixtiyoriy: bot orqali get_chat().photo dan olib qo'shish mumkin
        }
    )


async def api_comments(request: web.Request):
    post_id = int(request.match_info["post_id"])
    post = await db.get_post(post_id)
    if not post:
        return web.json_response({"error": "not found"}, status=404)

    rows = await db.get_post_comments(post_id)
    comments = [
        {"donor_name": r["donor_name"], "comment": r["comment"], "amount": r["amount"]}
        for r in rows
    ]
    return web.json_response({"post_title": post["title"], "comments": comments})


async def api_donate(request: web.Request):
    body = await request.json()

    post_id = body.get("post_id")
    amount = body.get("amount")
    provider = body.get("provider")
    donor_name = (body.get("donor_name") or "Noma'lum")[:60]
    comment = (body.get("comment") or "")[:250]
    init_data = body.get("init_data", "")

    if provider not in ("click", "payme"):
        return web.json_response({"error": "Noto'g'ri to'lov usuli"}, status=400)
    if not isinstance(amount, (int, float)) or amount <= 0:
        return web.json_response({"error": "Noto'g'ri summa"}, status=400)
    if not post_id:
        return web.json_response({"error": "Post topilmadi"}, status=400)

    post = await db.get_post(int(post_id))
    if not post:
        return web.json_response({"error": "Post topilmadi"}, status=404)

    verified = validate_init_data(init_data)
    donor_tg_id = verified["user"].get("id") if verified and verified.get("user") else 0

    payment_id = await db.create_payment(
        channel_id=post["channel_id"],
        post_id=post["id"],
        donor_tg_id=donor_tg_id or 0,
        donor_name=donor_name,
        comment=comment,
        amount=int(amount),
        provider=provider,
    )

    if provider == "click":
        pay_url = click_pay.generate_pay_url(payment_id, int(amount))
    else:
        pay_url = payme_pay.generate_pay_url(payment_id, int(amount))

    return web.json_response({"pay_url": pay_url, "payment_id": payment_id})


# ---------------------------------------------------------------------------

def create_app() -> web.Application:
    app = web.Application()

    app.router.add_post("/click/prepare", click_prepare)
    app.router.add_post("/click/complete", click_complete)
    app.router.add_post("/payme", payme_handler)

    app.router.add_get("/api/post/{post_id}", api_post_info)
    app.router.add_get("/api/comments/{post_id}", api_comments)
    app.router.add_post("/api/donate", api_donate)

    # mini_app/ papkasidagi index.html, comments.html, style.css, app.js statik xizmat qiladi
    app.router.add_static("/", path=str(MINI_APP_DIR), show_index=False, name="mini_app")

    return app


if __name__ == "__main__":
    web.run_app(create_app(), host=config.WEBHOOK_HOST, port=config.WEBHOOK_PORT)
