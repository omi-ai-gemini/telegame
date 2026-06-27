from flask import Flask, request

from admin import admin_bp
from database import init_db
from telegram_service import telegram_post
from games.registry import register_game_routes, route_game_command


app = Flask(__name__)


# =========================
# 註冊全域管理路由
# 例如：/admin/add_bot
# =========================
app.register_blueprint(admin_bp)


# =========================
# 註冊所有遊戲路由
# main 不知道 TLC 細節
# 只叫 registry 統一註冊
# =========================
register_game_routes(app)


# =========================
# DB 初始化
# =========================
db_initialized = False


@app.before_request
def init_once():
    global db_initialized

    if not db_initialized:
        init_db()
        db_initialized = True


# =========================
# Telegram Webhook
# 所有 bot 共用格式：
# /webhook/<bot_id>
# =========================
@app.route("/webhook/<bot_id>", methods=["POST"])
def webhook(bot_id):
    data = request.json

    if not data:
        return "ok"

    message = data.get("message")

    if not message:
        return "ok"

    chat_id = message["chat"]["id"]
    text = message.get("text", "")

    # =========================
    # main 不判斷哪個遊戲
    # 統一交給 games/registry.py
    # =========================
    route_game_command(
        bot_id=bot_id,
        chat_id=chat_id,
        text=text,
        telegram_post=telegram_post
    )

    return "ok"


# =========================
# Render 健康檢查
# =========================
@app.route("/")
def home():
    return "OK"


# =========================
# 本機啟動
# =========================
if __name__ == "__main__":
    import os

    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=True
    )