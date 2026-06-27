import requests

from config import TELEGRAM_API_BASE
from database import get_bot_token


# =========================
# Telegram API POST
# 全遊戲共用
# main / registry / TLC 都不直接碰 token
# token 統一從 DB 依 bot_id 取得
# =========================
def telegram_post(bot_id: str, method: str, payload: dict):
    token = get_bot_token(bot_id)

    if not token:
        print("ERROR: bot token not found:", bot_id, flush=True)
        return None

    url = f"{TELEGRAM_API_BASE}/bot{token}/{method}"

    try:
        res = requests.post(
            url,
            json=payload,
            timeout=30
        )

        if not res.ok:
            print("TELEGRAM ERROR:", res.text, flush=True)

        return res

    except Exception as e:
        print("TELEGRAM REQUEST ERROR:", e, flush=True)
        return None