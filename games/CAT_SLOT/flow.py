from flask import Blueprint, send_from_directory, jsonify
from pathlib import Path

from config import BASE_URL
from games.CAT_SLOT.logic import CAT_SLOT_SYMBOLS, spin_once


# =========================
# 貓咪拉霸機遊戲設定
# 目前只做轉動測試，不做扣幣與中獎
# =========================
CAT_SLOT_GAME = {
    "id": "cat_slot",
    "title": "🐱 貓咪拉霸機",
    "button_text": "貓咪拉霸機",
    "path": "/games/cat-slot",
    "commands": [
        "/cat_slot",
        "/catslot",
        "/slot",
        "貓咪拉霸",
        "貓咪拉霸機",
        "拉霸",
        "slot",
        "cat_slot"
    ]
}


# =========================
# Cat Slot Blueprint
# =========================
cat_slot_bp = Blueprint("cat_slot", __name__)

BASE_DIR = Path(__file__).resolve().parent


# =========================
# Telegram 指令流程
# 只屬於貓咪拉霸機
# =========================
def handle_cat_slot_command(bot_id, chat_id, telegram_post):
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

    game_url = f"{BASE_URL}{CAT_SLOT_GAME['path']}?bot_id={bot_id}"

    telegram_post(
        bot_id,
        "sendMessage",
        {
            "chat_id": chat_id,
            "text": "🐱 貓咪拉霸機",
            "reply_markup": {
                "inline_keyboard": [
                    [
                        {
                            "text": CAT_SLOT_GAME["button_text"],
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
# 貓咪拉霸 UI 首頁
# =========================
@cat_slot_bp.route("/games/cat-slot", methods=["GET"])
def cat_slot_home():
    return send_from_directory(BASE_DIR, "ui.html")


# =========================
# 貓咪拉霸 CSS
# =========================
@cat_slot_bp.route("/games/cat-slot/ui.css", methods=["GET"])
def cat_slot_css():
    return send_from_directory(BASE_DIR, "ui.css")


# =========================
# 貓咪拉霸 JS
# =========================
@cat_slot_bp.route("/games/cat-slot/ui.js", methods=["GET"])
def cat_slot_js():
    return send_from_directory(BASE_DIR, "ui.js")


# =========================
# 貓咪拉霸素材
# 之後把去背圖片放進 assets 就能直接讀取
# =========================
@cat_slot_bp.route("/games/cat-slot/assets/<path:filename>", methods=["GET"])
def cat_slot_assets(filename):
    return send_from_directory(BASE_DIR / "assets", filename)


# =========================
# 符號清單 API
# 前端用來建立初始畫面與測試素材
# =========================
@cat_slot_bp.route("/games/cat-slot/api/symbols", methods=["GET"])
def cat_slot_symbols():
    return jsonify({
        "ok": True,
        "symbols": CAT_SLOT_SYMBOLS
    })


# =========================
# 公平轉動 API
# 目前不做扣幣、不做中獎，只回傳五格結果
# =========================
@cat_slot_bp.route("/games/cat-slot/api/spin", methods=["POST"])
def cat_slot_spin():
    return jsonify({
        "ok": True,
        "result": spin_once()
    })
