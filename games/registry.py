from config import BASE_URL
from games.TLC.flow import (
    tlc_bp,
    TLC_GAME,
    handle_tlc_command
)


# =========================
# 所有遊戲 Blueprint
# 之後新增遊戲只加在這裡
# =========================
GAME_BLUEPRINTS = [
    tlc_bp
]


# =========================
# 所有遊戲資料
# 之後 slot、其他遊戲也加在這裡
# =========================
GAMES = [
    {
        "id": TLC_GAME["id"],
        "title": TLC_GAME["title"],
        "button_text": TLC_GAME["button_text"],
        "path": TLC_GAME["path"],
        "commands": TLC_GAME["commands"],
        "handler": handle_tlc_command
    }
]


# =========================
# 註冊所有遊戲網頁路由
# =========================
def register_game_routes(app):
    for blueprint in GAME_BLUEPRINTS:
        app.register_blueprint(blueprint)


# =========================
# 發送遊戲選單
# /start、/game 走這裡
# =========================
def send_game_menu(bot_id, chat_id, telegram_post):
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

    keyboard = []

    for game in GAMES:
        # =========================
        # WebApp 帶入 bot_id
        # 前端才能把同一個 Telegram user 的資源分 bot 儲存
        # =========================
        keyboard.append([
            {
                "text": game["button_text"],
                "web_app": {
                    "url": f"{BASE_URL}{game['path']}?bot_id={bot_id}"
                }
            }
        ])

    telegram_post(
        bot_id,
        "sendMessage",
        {
            "chat_id": chat_id,
            "text": "選擇遊戲",
            "reply_markup": {
                "inline_keyboard": keyboard
            }
        }
    )


# =========================
# Telegram 指令分流
# main 只會呼叫這裡
# =========================
def route_game_command(bot_id, chat_id, text, telegram_post):
    # =========================
    # 全遊戲共用入口
    # =========================
    if text in [
        "/start",
        "/game",
        "遊戲",
        "開始遊戲"
    ]:
        send_game_menu(
            bot_id=bot_id,
            chat_id=chat_id,
            telegram_post=telegram_post
        )
        return True

    # =========================
    # 單一遊戲指令
    # =========================
    for game in GAMES:
        if text in game["commands"]:
            game["handler"](
                bot_id=bot_id,
                chat_id=chat_id,
                telegram_post=telegram_post
            )
            return True

    return False