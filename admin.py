import requests
from flask import Blueprint, request

from config import ADMIN_PASSWORD, BASE_URL, TELEGRAM_API_BASE
from database import save_bot


admin_bp = Blueprint("admin", __name__)


# =========================
# 新增 / 更新 Bot
# 同時寫入 DB 並設定 webhook
# =========================
@admin_bp.route("/admin/add_bot", methods=["POST"])
def add_bot():
    data = request.get_json(silent=True) or request.form

    password = data.get("password")
    bot_id = data.get("bot_id")
    token = data.get("token")

    if password != ADMIN_PASSWORD:
        return "密碼錯誤", 403

    if not bot_id:
        return "缺少 bot_id", 400

    if not token:
        return "缺少 token", 400

    if not BASE_URL:
        return "BASE_URL 尚未設定", 500

    # =========================
    # 儲存 token 到 DB
    # =========================
    save_bot(
        bot_id=bot_id,
        token=token
    )

    # =========================
    # 設定 Telegram webhook
    # 每一隻 bot 用自己的 bot_id 路徑
    # =========================
    webhook_url = f"{BASE_URL}/webhook/{bot_id}"
    telegram_url = f"{TELEGRAM_API_BASE}/bot{token}/setWebhook"

    res = requests.post(
        telegram_url,
        data={
            "url": webhook_url
        },
        timeout=30
    )

    if not res.ok:
        return res.text, 400

    return f"bot 已儲存，webhook 已設定：{webhook_url}"