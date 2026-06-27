import random


# =========================
# 產生四位數字
# 例：0007、1284、9051
# =========================
def generate_code() -> str:
    number = random.randint(0, 9999)

    return str(number).zfill(4)


# =========================
# 產生四組不重複目標碼
# =========================
def generate_target_codes() -> list[str]:
    codes = set()

    while len(codes) < 4:
        codes.add(generate_code())

    return list(codes)


# =========================
# TLC 命中後產出數量
# 0 代表空包
# 目前規則：30% 空包，70% 產出 1～10 TLC
# =========================
def generate_tlc_reward() -> int:
    is_empty = random.random() < 0.3

    if is_empty:
        return 0

    return random.randint(1, 10)
