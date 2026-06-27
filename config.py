import os

# =========================
# Telegram API
# =========================
TELEGRAM_API_BASE = "https://api.telegram.org"

# =========================
# Render / Web URL
# 例：https://telegame-xxxx.onrender.com
# 不要加最後的 /
# =========================
BASE_URL = os.getenv("BASE_URL")

# =========================
# PostgreSQL / Supabase
# =========================
DATABASE_URL = os.getenv("DATABASE_URL")

# =========================
# 管理新增 bot 用
# =========================
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")