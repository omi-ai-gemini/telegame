const tg = window.Telegram?.WebApp;

if (tg) {
  tg.ready();
  tg.expand();
}

const SYMBOLS = [
  {
    id: "black_cat",
    name: "黑貓",
    emoji: "🐈‍⬛",
    image: "/games/cat-slot/assets/black_cat.png"
  },
  {
    id: "orange_cat",
    name: "橘貓",
    emoji: "🐱",
    image: "/games/cat-slot/assets/orange_cat.png"
  },
  {
    id: "white_cat",
    name: "白貓",
    emoji: "🤍",
    image: "/games/cat-slot/assets/white_cat.png"
  },
  {
    id: "calico_cat",
    name: "三花",
    emoji: "🌼",
    image: "/games/cat-slot/assets/calico_cat.png"
  },
  {
    id: "tabby_cat",
    name: "虎斑",
    emoji: "🐯",
    image: "/games/cat-slot/assets/tabby_cat.png"
  },
  {
    id: "tlc",
    name: "TLC",
    emoji: "🪙",
    image: "/games/cat-slot/assets/tlc_coin.png"
  }
];

const slotImageEls = [
  document.getElementById("slot-0"),
  document.getElementById("slot-1"),
  document.getElementById("slot-2"),
  document.getElementById("slot-3"),
  document.getElementById("slot-4")
];

const slotFallbackEls = [
  document.getElementById("slot-fallback-0"),
  document.getElementById("slot-fallback-1"),
  document.getElementById("slot-fallback-2"),
  document.getElementById("slot-fallback-3"),
  document.getElementById("slot-fallback-4")
];

const slotCellEls = Array.from(document.querySelectorAll(".slot-cell"));
const statusTextEl = document.getElementById("status-text");
const spinCountEl = document.getElementById("spin-count");
const lastResultEl = document.getElementById("last-result");
const betNoteEl = document.getElementById("bet-note");
const betButtons = Array.from(document.querySelectorAll(".bet-btn"));

const spinOnceBtn = document.getElementById("spin-once-btn");
const spinTenBtn = document.getElementById("spin-ten-btn");
const autoSpinBtn = document.getElementById("auto-spin-btn");
const stopBtn = document.getElementById("stop-btn");

let selectedBet = 100;
let spinCount = 0;
let spinning = false;
let autoTimer = null;


// =========================
// 從本地符號池公平隨機一個符號
// 只用於轉動動畫，不當作最終結果
// 最終結果仍以後端 API 回傳為準
// =========================
function randomSymbol() {
  const index = Math.floor(Math.random() * SYMBOLS.length);

  return SYMBOLS[index];
}


// =========================
// 依 id 找符號資料
// 後端回傳同樣的 id，前端補上圖片路徑
// =========================
function findSymbol(symbol) {
  return SYMBOLS.find((item) => item.id === symbol.id) || symbol;
}


// =========================
// 設定單格符號
// 如果未來圖片還沒放進 assets，會自動退回 emoji 顯示
// =========================
function setSlotSymbol(index, symbol) {
  const normalizedSymbol = findSymbol(symbol);
  const imageEl = slotImageEls[index];
  const fallbackEl = slotFallbackEls[index];

  fallbackEl.textContent = normalizedSymbol.emoji || "❔";
  imageEl.alt = normalizedSymbol.name || "拉霸符號";
  imageEl.src = normalizedSymbol.image || "";

  imageEl.onload = () => {
    imageEl.style.display = "block";
    fallbackEl.style.display = "none";
  };

  imageEl.onerror = () => {
    imageEl.style.display = "none";
    fallbackEl.style.display = "inline";
  };
}


// =========================
// 更新下注 UI
// 目前只做顯示，不扣幣
// =========================
function setSelectedBet(amount) {
  selectedBet = Number(amount);

  betButtons.forEach((button) => {
    const buttonBet = Number(button.dataset.bet);

    button.classList.toggle("active", buttonBet === selectedBet);
  });

  betNoteEl.textContent = `目前選擇：${selectedBet.toLocaleString()} 貓咪幣`;
}


// =========================
// 呼叫後端取得公平五格結果
// =========================
async function requestSpinResult() {
  const res = await fetch("/games/cat-slot/api/spin", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      bet_amount: selectedBet
    })
  });

  const data = await res.json();

  if (!res.ok || !data.ok) {
    throw new Error(data.error || "spin_failed");
  }

  return data.result;
}


// =========================
// 播放一次假轉動動畫，再停到後端結果
// =========================
async function spinOnce() {
  if (spinning) {
    return;
  }

  spinning = true;
  setButtonsDisabled(true);
  statusTextEl.textContent = "轉動中...";

  slotCellEls.forEach((cell) => {
    cell.classList.remove("stopped");
    cell.classList.add("spinning");
  });

  const animationTimer = setInterval(() => {
    for (let i = 0; i < 5; i += 1) {
      setSlotSymbol(i, randomSymbol());
    }
  }, 85);

  try {
    const result = await requestSpinResult();

    await wait(650);
    clearInterval(animationTimer);

    for (let i = 0; i < 5; i += 1) {
      await wait(110);

      slotCellEls[i].classList.remove("spinning");
      slotCellEls[i].classList.add("stopped");
      setSlotSymbol(i, result[i]);
    }

    spinCount += 1;
    spinCountEl.textContent = spinCount;
    lastResultEl.textContent = result.map((symbol) => symbol.name).join("｜");
    statusTextEl.textContent = `完成，下注額 ${selectedBet.toLocaleString()} 貓咪幣（測試版未扣幣）`;
  } catch (error) {
    console.error(error);
    clearInterval(animationTimer);
    statusTextEl.textContent = "轉動失敗";
  } finally {
    spinning = false;
    setButtonsDisabled(false);
  }
}


// =========================
// 連續轉十次
// 中獎與扣幣尚未接入，只測轉動流程
// =========================
async function spinTen() {
  stopAutoSpin();

  for (let i = 0; i < 10; i += 1) {
    await spinOnce();
  }

  statusTextEl.textContent = "十次轉動完成（測試版未結算）";
}


// =========================
// 無限轉
// 目前不檢查餘額，正式版會改成直到貓咪幣不足
// =========================
function startAutoSpin() {
  if (autoTimer) {
    return;
  }

  statusTextEl.textContent = "無限轉測試中，按停止可中斷";

  autoTimer = setInterval(async () => {
    if (!spinning) {
      await spinOnce();
    }
  }, 950);
}


// =========================
// 停止無限轉
// =========================
function stopAutoSpin() {
  if (autoTimer) {
    clearInterval(autoTimer);
    autoTimer = null;
    statusTextEl.textContent = "已停止";
  }
}


// =========================
// 控制按鈕狀態
// 無限轉期間允許按停止
// =========================
function setButtonsDisabled(disabled) {
  spinOnceBtn.disabled = disabled;
  spinTenBtn.disabled = disabled;
  autoSpinBtn.disabled = disabled;
}


function wait(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}


// =========================
// 事件綁定
// =========================
betButtons.forEach((button) => {
  button.addEventListener("click", () => {
    setSelectedBet(button.dataset.bet);
  });
});

spinOnceBtn.addEventListener("click", () => {
  stopAutoSpin();
  spinOnce();
});

spinTenBtn.addEventListener("click", spinTen);

autoSpinBtn.addEventListener("click", startAutoSpin);

stopBtn.addEventListener("click", stopAutoSpin);


// =========================
// 初始化五格畫面
// =========================
for (let i = 0; i < 5; i += 1) {
  setSlotSymbol(i, SYMBOLS[i]);
}

setSelectedBet(selectedBet);
