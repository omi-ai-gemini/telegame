from flask import Blueprint, send_from_directory, jsonify, request
from pathlib import Path

from config import BASE_URL
from games.TLC.logic import generate_target_codes, generate_tlc_reward
from resource_service import add_resource_with_hit_log, get_resource


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
TLC_RESOURCE_KEY = "TLC"


# =========================
# 檢查前端傳來的玩家資料
# bot_id 來自 WebApp URL 參數
# user_id 來自 Telegram WebApp initDataUnsafe.user.id
# =========================
def _read_player_payload(data=None):
    data = data or {}

    bot_id = str(data.get("bot_id") or request.args.get("bot_id") or "").strip()
    user_id = str(data.get("user_id") or request.args.get("user_id") or "").strip()

    if not bot_id:
        return None, None, (jsonify({
            "ok": False,
            "error": "missing_bot_id"
        }), 400)

    if not user_id:
        return None, None, (jsonify({
            "ok": False,
            "error": "missing_user_id"
        }), 400)

    return bot_id, user_id, None


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

    # =========================
    # WebApp 要帶 bot_id
    # 否則前端只知道 user_id，無法分辨是哪隻 bot 的資源
    # =========================
    game_url = f"{BASE_URL}{TLC_GAME['path']}?bot_id={bot_id}"

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
# 目前只給前端取得四組目標碼
# 目標碼不顯示在畫面，只用於前端判定命中
# =========================
@tlc_bp.route("/games/tlc/api/targets", methods=["GET"])
def tlc_targets():
    return jsonify({
        "target_codes": generate_target_codes()
    })


# =========================
# TLC 餘額 API
# 從全遊戲共用 player_resources 讀取目前持有 TLC
# =========================
@tlc_bp.route("/games/tlc/api/balance", methods=["GET"])
def tlc_balance():
    bot_id, user_id, error_response = _read_player_payload()

    if error_response:
        return error_response

    amount = get_resource(
        bot_id=bot_id,
        user_id=user_id,
        resource_key=TLC_RESOURCE_KEY
    )

    return jsonify({
        "ok": True,
        "resource_key": TLC_RESOURCE_KEY,
        "amount": amount
    })


# =========================
# TLC 命中產出 API
# 產出由後端判定，並寫入全遊戲共用 player_resources
# 前端只負責顯示回傳結果
# =========================
@tlc_bp.route("/games/tlc/api/reward", methods=["POST"])
def tlc_reward():
    data = request.get_json(silent=True) or {}

    bot_id, user_id, error_response = _read_player_payload(data)

    if error_response:
        return error_response

    hit_code = str(data.get("hit_code") or "").strip()
    try_count = data.get("try_count")

    reward = generate_tlc_reward()

    result = add_resource_with_hit_log(
        bot_id=bot_id,
        user_id=user_id,
        resource_key=TLC_RESOURCE_KEY,
        amount=reward,
        game_id=TLC_GAME["id"],
        hit_code=hit_code,
        try_count=try_count,
        keep_limit=100
    )

    return jsonify({
        "ok": True,
        "resource_key": TLC_RESOURCE_KEY,
        "reward": reward,
        "amount": result["amount"],
        "log_id": result["log_id"]
    })
