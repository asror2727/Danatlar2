"""
Payme (Paycom) integratsiyasi.
Hujjat: https://developer.help.paycom.uz/

1) generate_pay_url() - checkout havolasi (base64 kodlangan parametrlar)
2) JSON-RPC webhook metodlari: CheckPerformTransaction, CreateTransaction,
   PerformTransaction, CancelTransaction, CheckTransaction, GetStatement.
   Bular webhook_server.py orqali ulanadi.
"""
import base64
import time

import config
import database as db

CHECKOUT_BASE = "https://checkout.paycom.uz" if not config.PAYME_IS_TEST else "https://test.paycom.uz"

# Payme xatolik kodlari
PERM_DENIED = -32504
INVALID_AMOUNT = -31001
TRANSACTION_NOT_FOUND = -31003
UNABLE_TO_PERFORM = -31008
ORDER_NOT_FOUND = -31050

STATE_CREATED = 1
STATE_COMPLETED = 2
STATE_CANCELLED = -1
STATE_CANCELLED_AFTER_COMPLETE = -2


def generate_pay_url(payment_id: int, amount: int) -> str:
    """amount so'mda keladi -> Payme tiyinda kutadi (x100)."""
    if config.TEST_MODE or not config.PAYME_MERCHANT_ID:
        # Test rejimi: haqiqiy Payme kalitlari kerak emas, faqat oqimni sinash uchun soxta havola
        return f"https://example.com/test-payment?provider=payme&payment_id={payment_id}&amount={amount}"

    amount_tiyin = amount * 100
    raw = f"m={config.PAYME_MERCHANT_ID};ac.order_id={payment_id};a={amount_tiyin}"
    encoded = base64.b64encode(raw.encode()).decode()
    return f"{CHECKOUT_BASE}/{encoded}"


def check_auth(auth_header: str) -> bool:
    """Payme so'rovlari Basic Auth bilan keladi: login=Paycom, parol=PAYME_KEY."""
    if not auth_header or not auth_header.startswith("Basic "):
        return False
    try:
        decoded = base64.b64decode(auth_header.split(" ", 1)[1]).decode()
        login, password = decoded.split(":", 1)
    except Exception:
        return False
    return login == "Paycom" and password == config.PAYME_KEY


async def check_perform_transaction(params: dict) -> dict:
    order_id = int(params["account"]["order_id"])
    amount_tiyin = params["amount"]
    payment = await db.get_payment(order_id)
    if not payment:
        return {"error": {"code": ORDER_NOT_FOUND, "message": "Order not found"}}
    if payment["amount"] * 100 != amount_tiyin:
        return {"error": {"code": INVALID_AMOUNT, "message": "Incorrect amount"}}
    return {"result": {"allow": True}}


async def create_transaction(params: dict) -> dict:
    order_id = int(params["account"]["order_id"])
    payment = await db.get_payment(order_id)
    if not payment:
        return {"error": {"code": ORDER_NOT_FOUND, "message": "Order not found"}}
    if payment["status"] == "paid":
        return {"error": {"code": UNABLE_TO_PERFORM, "message": "Already paid"}}

    return {
        "result": {
            "create_time": int(time.time() * 1000),
            "transaction": str(order_id),
            "state": STATE_CREATED,
        }
    }


async def perform_transaction(params: dict) -> dict:
    payme_trans_id = params["id"]
    # transaction id sifatida biz order_id ni ishlatyapmiz (soddalashtirilgan yondashuv)
    order_id = int(params.get("account", {}).get("order_id", 0)) or None
    if order_id is None:
        return {"error": {"code": TRANSACTION_NOT_FOUND, "message": "Transaction not found"}}

    payment = await db.get_payment(order_id)
    if not payment:
        return {"error": {"code": TRANSACTION_NOT_FOUND, "message": "Transaction not found"}}

    if payment["status"] != "paid":
        await db.mark_payment_paid(order_id, payme_trans_id)

    return {
        "result": {
            "transaction": str(order_id),
            "perform_time": int(time.time() * 1000),
            "state": STATE_COMPLETED,
        }
    }


async def cancel_transaction(params: dict) -> dict:
    order_id = int(params.get("account", {}).get("order_id", 0)) or None
    if order_id:
        await db.mark_payment_cancelled(order_id)
    return {
        "result": {
            "transaction": str(order_id),
            "cancel_time": int(time.time() * 1000),
            "state": STATE_CANCELLED,
        }
    }
