import psycopg2

from config import DATABASE_URL


# =========================
# Bot Token 快取
# 避免每次訊息都查 DB
# =========================
_TOKEN_CACHE = {}


# =========================
# 建立 DB 連線
# =========================
def get_conn():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is missing")

    return psycopg2.connect(DATABASE_URL)


# =========================
# 初始化資料表
# 目前只建立 bot_config
# 之後玩家資料、TLC 餘額、遊戲紀錄再另外擴充
# =========================
def init_db():
    conn = get_conn()

    try:
        cursor = conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS bot_config (
            bot_id TEXT PRIMARY KEY,
            token TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


# =========================
# 新增 / 更新 bot token
# =========================
def save_bot(bot_id: str, token: str):
    bot_id = str(bot_id)

    conn = get_conn()

    try:
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO bot_config (
            bot_id,
            token,
            updated_at
        )
        VALUES (%s, %s, CURRENT_TIMESTAMP)

        ON CONFLICT (bot_id)

        DO UPDATE SET
            token = EXCLUDED.token,
            updated_at = CURRENT_TIMESTAMP
        """, (
            bot_id,
            token
        ))

        conn.commit()

        # 更新 token 後清掉快取
        _TOKEN_CACHE.pop(bot_id, None)

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


# =========================
# 用 bot_id 取得 token
# =========================
def get_bot_token(bot_id: str):
    bot_id = str(bot_id)

    if bot_id in _TOKEN_CACHE:
        return _TOKEN_CACHE[bot_id]

    conn = get_conn()

    try:
        cursor = conn.cursor()

        cursor.execute("""
        SELECT token
        FROM bot_config
        WHERE bot_id = %s
        """, (
            bot_id,
        ))

        row = cursor.fetchone()

        if not row:
            return None

        token = row[0]

        _TOKEN_CACHE[bot_id] = token

        return token

    finally:
        conn.close()