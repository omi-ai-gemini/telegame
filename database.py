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
# database.py 只負責全域 DB 連線與建表
# 實際讀取 / 儲存資源交給 resource_service.py
# =========================
def init_db():
    conn = get_conn()

    try:
        cursor = conn.cursor()

        # =========================
        # Bot 設定表
        # 儲存每隻 Telegram Bot 的 token
        # =========================
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS bot_config (
            bot_id TEXT PRIMARY KEY,
            token TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # =========================
        # 全遊戲共用玩家資源表
        # 所有遊戲、所有資源都寫在這一張
        # 例：TLC、ENERGY、TICKET、SLOT_POINT
        # =========================
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS player_resources (
            id SERIAL PRIMARY KEY,

            bot_id TEXT NOT NULL,
            user_id TEXT NOT NULL,

            resource_key TEXT NOT NULL,
            amount BIGINT NOT NULL DEFAULT 0 CHECK (amount >= 0),

            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            UNIQUE (bot_id, user_id, resource_key)
        )
        """)

        # =========================
        # 全遊戲共用命中紀錄表
        # 只保留每個 bot / 玩家 / 遊戲最新 100 筆命中紀錄
        # 空包也會記錄 reward = 0
        # =========================
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS game_hit_logs (
            id SERIAL PRIMARY KEY,

            bot_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            game_id TEXT NOT NULL,

            resource_key TEXT NOT NULL,
            hit_code TEXT NOT NULL,
            reward BIGINT NOT NULL DEFAULT 0 CHECK (reward >= 0),
            amount_after BIGINT NOT NULL DEFAULT 0 CHECK (amount_after >= 0),
            try_count BIGINT,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_game_hit_logs_lookup
        ON game_hit_logs (
            bot_id,
            user_id,
            game_id,
            created_at DESC,
            id DESC
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