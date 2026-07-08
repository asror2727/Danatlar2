"""
Click.uz integratsiyasi.
Hujjat: https://docs.click.uz/

1) generate_pay_url() - foydalanuvchiga yuboriladigan to'lov havolasi
2) Click serveri to'lovni tasdiqlash uchun bizning webhook manzilimizga
   ikki bosqichda POST yuboradi: action=0 (Prepare), action=1 (Complete).
   Bu handlerlar webhook_server.py da ulanadi.
"""
import hashlib
from urllib.parse import urlencode

import config
import database as db

CLICK_PAY_BASE = "https://my.click.uz/services/pay"

# Click javob kodlari
ERROR_SUCCESS = 0
ERROR_SIGN_CHECK_FAILED = -1
ERROR_TRANSACTION_NOT_FOUND = -6
ERROR_ALREADY_PAID = -4
ERROR_USER_NOT_FOUND = -5


def generate_pay_url(payment_id: int, amount: int) -> str:
    """payment_id -> bizning payments jadvalimizdagi id (merchant_trans_id sifatida yuboriladi)."""
    if config.TEST_MODE or not config.CLICK_SERVICE_ID or not config.CLICK_MERCHANT_ID:
        # Test rejimi: haqiqiy Click kalitlari kerak emas, faqat oqimni sinash uchun soxta havola
        return f"https://example.com/test-payment?provider=click&payment_id={payment_id}&amount={amount}"

    params = {
        "service_id": config.CLICK_SERVICE_ID,
        "merchant_id": config.CLICK_MERCHANT_ID,
        "amount": amount,
        "transaction_param": payment_id,
        "return_url": config.CLICK_RETURN_URL,
    }
    return f"{CLICK_PAY_BASE}?{urlencode(params)}"


def _check_signature(data: dict) -> bool:
    action = data.get("action")
    sign_string = data.get("sign_string", "")
    click_trans_id = data.get("click_trans_id", "")
    service_id = data.get("service_id", "")
    merchant_trans_id = data.get("merchant_trans_id", "")
    amount = data.get("amount", "")
    sign_time = data.get("sign_time", "")

    if str(action) == "0":
        raw = f"{click_trans_id}{service_id}{config.CLICK_SECRET_KEY}{merchant_trans_id}{amount}{action}{sign_time}"
    else:
        merchant_prepare_id = data.get("merchant_prepare_id", "")
        raw = (
            f"{click_trans_id}{service_id}{config.CLICK_SECRET_KEY}{merchant_trans_id}"
            f"{merchant_prepare_id}{amount}{action}{sign_time}"
        )

    expected = hashlib.md5(raw.encode()).hexdigest()
    return expected == sign_string


async def handle_prepare(data: dict) -> dict:
    """Click 'Prepare' (action=0) so'roviga javob."""
    if not _check_signature(data):
        return {"error": ERROR_SIGN_CHECK_FAILED, "error_note": "Sign check failed"}

    payment_id = int(data.get("merchant_trans_id"))
    payment = await db.get_payment(payment_id)
    if not payment:
        return {"error": ERROR_TRANSACTION_NOT_FOUND, "error_note": "Payment not found"}
    if payment["status"] == "paid":
        return {"error": ERROR_ALREADY_PAID, "error_note": "Already paid"}

    return {
        "click_trans_id": data.get("click_trans_id"),
        "merchant_trans_id": payment_id,
        "merchant_prepare_id": payment_id,
        "error": ERROR_SUCCESS,
        "error_note": "Success",
    }


async def handle_complete(data: dict) -> dict:
    """Click 'Complete' (action=1) so'roviga javob."""
    if not _check_signature(data):
        return {"error": ERROR_SIGN_CHECK_FAILED, "error_note": "Sign check failed"}

    payment_id = int(data.get("merchant_trans_id"))
    payment = await db.get_payment(payment_id)
    if not payment:
        return {"error": ERROR_TRANSACTION_NOT_FOUND, "error_note": "Payment not found"}

    error = int(data.get("error", 0))
    if error < 0:
        await db.mark_payment_cancelled(payment_id)
        return {
            "click_trans_id": data.get("click_trans_id"),
            "merchant_trans_id": payment_id,
            "merchant_confirm_id": payment_id,
            "error": ERROR_SUCCESS,
            "error_note": "Cancelled",
        }

    if payment["status"] != "paid":
        await db.mark_payment_paid(payment_id, str(data.get("click_trans_id")))

    return {
        "click_trans_id": data.get("click_trans_id"),
        "merchant_trans_id": payment_id,
        "merchant_confirm_id": payment_id,
        "error": ERROR_SUCCESS,
        "error_note": "Success",
    }
