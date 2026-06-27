import random


# =========================
# 貓咪拉霸符號池
# 目前每個符號出現機率完全公平
# 中獎機制尚未接入，只負責產生轉動結果
# =========================
CAT_SLOT_SYMBOLS = [
    {
        "id": "black_cat",
        "name": "黑貓",
        "emoji": "🐈‍⬛"
    },
    {
        "id": "orange_cat",
        "name": "橘貓",
        "emoji": "🐱"
    },
    {
        "id": "white_cat",
        "name": "白貓",
        "emoji": "🤍"
    },
    {
        "id": "calico_cat",
        "name": "三花",
        "emoji": "🌼"
    },
    {
        "id": "tabby_cat",
        "name": "虎斑",
        "emoji": "🐯"
    },
    {
        "id": "tlc",
        "name": "TLC",
        "emoji": "🪙"
    }
]


# =========================
# 公平產生五格結果
# 每格都從 6 種符號中等機率抽出
# =========================
def spin_once() -> list[dict]:
    result = []

    for _ in range(5):
        result.append(random.choice(CAT_SLOT_SYMBOLS))

    return result
