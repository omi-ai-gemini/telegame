from database import get_conn


# =========================
# 全遊戲共用資源服務
# 所有遊戲的資源都寫入同一張 player_resources
# 例：TLC、ENERGY、TICKET、SLOT_POINT
# =========================


# =========================
# 統一轉字串
# 避免 Telegram 傳來 int / str 混用導致查不到同一筆資料
# =========================
def _normalize_key(value) -> str:
    return str(value).strip()


# =========================
# 取得玩家某項資源
# 沒資料視為 0
# =========================
def get_resource(bot_id, user_id, resource_key: str) -> int:
    bot_id = _normalize_key(bot_id)
    user_id = _normalize_key(user_id)
    resource_key = _normalize_key(resource_key).upper()

    conn = get_conn()

    try:
        cursor = conn.cursor()

        cursor.execute("""
        SELECT amount
        FROM player_resources
        WHERE bot_id = %s
          AND user_id = %s
          AND resource_key = %s
        """, (
            bot_id,
            user_id,
            resource_key
        ))

        row = cursor.fetchone()

        if not row:
            return 0

        return int(row[0])

    finally:
        conn.close()


# =========================
# 直接設定玩家某項資源
# 通常用於管理、修正、初始化
# 一般遊戲流程優先用 add_resource / spend_resource
# =========================
def set_resource(bot_id, user_id, resource_key: str, amount: int) -> int:
    bot_id = _normalize_key(bot_id)
    user_id = _normalize_key(user_id)
    resource_key = _normalize_key(resource_key).upper()
    amount = int(amount)

    if amount < 0:
        raise ValueError("resource amount can not be negative")

    conn = get_conn()

    try:
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO player_resources (
            bot_id,
            user_id,
            resource_key,
            amount,
            updated_at
        )
        VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)

        ON CONFLICT (bot_id, user_id, resource_key)

        DO UPDATE SET
            amount = EXCLUDED.amount,
            updated_at = CURRENT_TIMESTAMP

        RETURNING amount
        """, (
            bot_id,
            user_id,
            resource_key,
            amount
        ))

        new_amount = int(cursor.fetchone()[0])

        conn.commit()

        return new_amount

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


# =========================
# 增加玩家某項資源
# amount 可以是 0；0 代表空包或無變動，會回傳目前持有量
# =========================
def add_resource(bot_id, user_id, resource_key: str, amount: int) -> int:
    bot_id = _normalize_key(bot_id)
    user_id = _normalize_key(user_id)
    resource_key = _normalize_key(resource_key).upper()
    amount = int(amount)

    if amount < 0:
        raise ValueError("add_resource amount must be >= 0")

    conn = get_conn()

    try:
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO player_resources (
            bot_id,
            user_id,
            resource_key,
            amount,
            updated_at
        )
        VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)

        ON CONFLICT (bot_id, user_id, resource_key)

        DO UPDATE SET
            amount = player_resources.amount + EXCLUDED.amount,
            updated_at = CURRENT_TIMESTAMP

        RETURNING amount
        """, (
            bot_id,
            user_id,
            resource_key,
            amount
        ))

        new_amount = int(cursor.fetchone()[0])

        conn.commit()

        return new_amount

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


# =========================
# 扣除玩家某項資源
# 餘額不足時回傳 False，不會讓資源變負數
# 成功時回傳 True 與扣除後餘額
# =========================
def spend_resource(bot_id, user_id, resource_key: str, amount: int):
    bot_id = _normalize_key(bot_id)
    user_id = _normalize_key(user_id)
    resource_key = _normalize_key(resource_key).upper()
    amount = int(amount)

    if amount <= 0:
        raise ValueError("spend_resource amount must be > 0")

    conn = get_conn()

    try:
        cursor = conn.cursor()

        cursor.execute("""
        SELECT amount
        FROM player_resources
        WHERE bot_id = %s
          AND user_id = %s
          AND resource_key = %s
        FOR UPDATE
        """, (
            bot_id,
            user_id,
            resource_key
        ))

        row = cursor.fetchone()
        current_amount = int(row[0]) if row else 0

        if current_amount < amount:
            conn.rollback()

            return {
                "ok": False,
                "amount": current_amount
            }

        new_amount = current_amount - amount

        cursor.execute("""
        INSERT INTO player_resources (
            bot_id,
            user_id,
            resource_key,
            amount,
            updated_at
        )
        VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)

        ON CONFLICT (bot_id, user_id, resource_key)

        DO UPDATE SET
            amount = EXCLUDED.amount,
            updated_at = CURRENT_TIMESTAMP
        """, (
            bot_id,
            user_id,
            resource_key,
            new_amount
        ))

        conn.commit()

        return {
            "ok": True,
            "amount": new_amount
        }

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


# =========================
# 增加資源並寫入命中紀錄
# 這個函式會在同一個 DB transaction 內完成：
# 1. 增加資源，amount 可以是 0
# 2. 新增命中紀錄，空包也會記錄 reward = 0
# 3. 只保留同 bot / 同玩家 / 同遊戲最新 100 筆紀錄
# =========================
def add_resource_with_hit_log(
    bot_id,
    user_id,
    resource_key: str,
    amount: int,
    game_id: str,
    hit_code: str,
    try_count=None,
    keep_limit: int = 100
):
    bot_id = _normalize_key(bot_id)
    user_id = _normalize_key(user_id)
    resource_key = _normalize_key(resource_key).upper()
    game_id = _normalize_key(game_id).lower()
    hit_code = _normalize_key(hit_code)
    amount = int(amount)
    keep_limit = int(keep_limit)

    if amount < 0:
        raise ValueError("add_resource_with_hit_log amount must be >= 0")

    if keep_limit <= 0:
        raise ValueError("keep_limit must be > 0")

    if try_count is not None:
        try_count = int(try_count)

    conn = get_conn()

    try:
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO player_resources (
            bot_id,
            user_id,
            resource_key,
            amount,
            updated_at
        )
        VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)

        ON CONFLICT (bot_id, user_id, resource_key)

        DO UPDATE SET
            amount = player_resources.amount + EXCLUDED.amount,
            updated_at = CURRENT_TIMESTAMP

        RETURNING amount
        """, (
            bot_id,
            user_id,
            resource_key,
            amount
        ))

        new_amount = int(cursor.fetchone()[0])

        cursor.execute("""
        INSERT INTO game_hit_logs (
            bot_id,
            user_id,
            game_id,
            resource_key,
            hit_code,
            reward,
            amount_after,
            try_count
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        """, (
            bot_id,
            user_id,
            game_id,
            resource_key,
            hit_code,
            amount,
            new_amount,
            try_count
        ))

        log_id = int(cursor.fetchone()[0])

        cursor.execute("""
        DELETE FROM game_hit_logs
        WHERE id IN (
            SELECT id
            FROM (
                SELECT id
                FROM game_hit_logs
                WHERE bot_id = %s
                  AND user_id = %s
                  AND game_id = %s
                ORDER BY created_at DESC, id DESC
                OFFSET %s
            ) AS old_logs
        )
        """, (
            bot_id,
            user_id,
            game_id,
            keep_limit
        ))

        conn.commit()

        return {
            "amount": new_amount,
            "log_id": log_id
        }

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()
