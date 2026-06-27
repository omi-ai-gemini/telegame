from flask import Blueprint, send_from_directory, jsonify
from pathlib import Path

from config import BASE_URL
from games.TLC.logic import generate_target_codes


# =========================
# TLC 遊戲設定
# 這裡才放 TLC 這個遊戲自己的資料
# =========================
TLC_GAME = {
    "id": "tlc",
    "title": "🪙 TeleCoin",
    "button_text": "開始 TLC",
    "path": "/games/tlc",
    "commands": [
        "/tlc",
        "TLC",
        "tlc",
        "TeleCoin",
        "telecoin",
        "開始TLC",
        "開始 TLC"
    ]
}


# =========================
# TLC Blueprint
# =========================
tlc_bp = Blueprint("tlc", __name__)

BASE_DIR = Path(__file__).resolve().parent


# =========================
# Telegram 指令流程
# 只屬於 TLC
# =========================
def handle_tlc_command(bot_id, chat_id, telegram_post):
    if not BASE_URL:
        telegram_post(
            bot_id,
            "sendMessage",
            {
                "chat_id": chat_id,
                "text": "BASE_URL 尚未設定"
            }
        )
        return

    game_url = f"{BASE_URL}{TLC_GAME['path']}"

    telegram_post(
        bot_id,
        "sendMessage",
        {
            "chat_id": chat_id,
            "text": "🪙 TeleCoin",
            "reply_markup": {
                "inline_keyboard": [
                    [
                        {
                            "text": TLC_GAME["button_text"],
                            "web_app": {
                                "url": game_url
                            }
                        }
                    ]
                ]
            }
        }
    )


# =========================
# TLC UI 首頁
# =========================
@tlc_bp.route("/games/tlc", methods=["GET"])
def tlc_home():
    return send_from_directory(BASE_DIR, "ui.html")


# =========================
# TLC CSS
# =========================
@tlc_bp.route("/games/tlc/ui.css", methods=["GET"])
def tlc_css():
    return send_from_directory(BASE_DIR, "ui.css")


# =========================
# TLC JS
# =========================
@tlc_bp.route("/games/tlc/ui.js", methods=["GET"])
def tlc_js():
    return send_from_directory(BASE_DIR, "ui.js")


# =========================
# TLC 目標碼 API
# 目前只給前端產生四組目標碼
# 尚未做產出、TLC 寫入、玩家資料
# =========================
@tlc_bp.route("/games/tlc/api/targets", methods=["GET"])
def tlc_targets():
    return jsonify({
        "target_codes": generate_target_codes()
    })