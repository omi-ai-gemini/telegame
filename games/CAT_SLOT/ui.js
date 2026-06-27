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
const betButtons = Array.from(document.querySelectorAll(".bet-btn"));

const betNoteEl = document.getElementById("bet-note");
const statusTextEl = document.getElementById("status-text");

const spinOnceBtn = document.getElementById("spin-once-btn");
const spinTenBtn = document.getElementById("spin-ten-btn");
const autoSpinBtn = document.getElementById("auto-spin-btn");
const stopBtn = document.getElementById("stop-btn");

const leverEl = document.getElementById("machine-lever");

let selectedBet = 100;
let isSpinning = false;
let runMode = null;       // null | "single" | "ten" | "auto"
let stopRequested = false;


// =========================
// 從本地符號池公平隨機一個符號
// 只用於動畫
// =========================
function randomSymbol() {
  const index = Math.floor(Math.random() * SYMBOLS.length);

  return SYMBOLS[index];
}


// =========================
// 依 id 找符號
// =========================
function findSymbol(symbol) {
  return SYMBOLS.find((item) => item.id === symbol.id) || symbol;
}


// =========================
// 設定單格符號
// 若圖片不存在，退回 emoji
// =========================
function setSlotSymbol(index, symbol) {
  const normalizedSymbol = findSymbol(symbol);
  const imageEl = slotImageEls[index];
  const fallbackEl = slotFallbackEls[index];

  fallbackEl.textContent = normalizedSymbol.emoji || "❔";
  imageEl.alt = normalizedSymbol.name || "拉霸符號";

  imageEl.onload = () => {
    imageEl.style.display = "block";
    fallbackEl.style.display = "none";
  };

  imageEl.onerror = () => {
    imageEl.style.display = "none";
    fallbackEl.style.display = "inline";
  };

  imageEl.src = normalizedSymbol.image || "";
}


// =========================
// 更新下注顯示
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
// 呼叫後端取得公平結果
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
// 拉桿動畫
// =========================
function triggerLeverAnimation() {
  leverEl.classList.remove("pulling");

  void leverEl.offsetWidth;

  leverEl.classList.add("pulling");
}


// =========================
// 控制按鈕狀態
// 停止按鈕永遠保留最高權限
// =========================
function setRunningState(running) {
  betButtons.forEach((button) => {
    button.disabled = running;
  });

  spinOnceBtn.disabled = running;
  spinTenBtn.disabled = running;
  autoSpinBtn.disabled = running;
  stopBtn.disabled = false;
}


// =========================
// 單次轉動
// 若 stopRequested = true，也會先完成這一次
// 但不會再開始下一次
// =========================
async function performSingleSpin() {
  if (isSpinning) {
    return;
  }

  isSpinning = true;
  triggerLeverAnimation();
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

    await wait(620);
    clearInterval(animationTimer);

    for (let i = 0; i < 5; i += 1) {
      await wait(95);

      slotCellEls[i].classList.remove("spinning");
      slotCellEls[i].classList.add("stopped");
      setSlotSymbol(i, result[i]);
    }

    if (stopRequested) {
      statusTextEl.textContent = "已停止";
    } else {
      statusTextEl.textContent = `完成，下注額 ${selectedBet.toLocaleString()} 貓咪幣（測試版未扣幣）`;
    }
  } catch (error) {
    console.error(error);
    clearInterval(animationTimer);
    statusTextEl.textContent = "轉動失敗";
  } finally {
    isSpinning = false;
  }
}


// =========================
// 執行模式
// single / ten / auto
// 停止只會阻止下一次開始
// =========================
async function runSpinMode(mode) {
  if (runMode || isSpinning) {
    return;
  }

  runMode = mode;
  stopRequested = false;
  setRunningState(true);

  try {
    if (mode === "single") {
      await performSingleSpin();
      return;
    }

    if (mode === "ten") {
      for (let i = 0; i < 10; i += 1) {
        if (stopRequested) {
          break;
        }

        await performSingleSpin();

        if (stopRequested) {
          break;
        }

        if (i < 9) {
          await wait(110);
        }
      }

      if (!stopRequested) {
        statusTextEl.textContent = "十次轉動完成";
      }

      return;
    }

    if (mode === "auto") {
      while (!stopRequested) {
        await performSingleSpin();

        if (stopRequested) {
          break;
        }

        await wait(110);
      }

      statusTextEl.textContent = "已停止";
    }
  } finally {
    runMode = null;
    stopRequested = false;
    setRunningState(false);
  }
}


// =========================
// 停止優先權最高
// 當前轉動不打斷
// 但會阻止下一次開始
// =========================
function stopCurrentMode() {
  stopRequested = true;

  if (isSpinning) {
    statusTextEl.textContent = "停止中，將在本次轉動結束後停止";
  } else {
    statusTextEl.textContent = "已停止";
  }
}


function wait(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}


// =========================
// 事件綁定
// =========================
betButtons.forEach((button) => {
  button.addEventListener("click", () => {
    if (runMode || isSpinning) {
      return;
    }

    setSelectedBet(button.dataset.bet);
  });
});

spinOnceBtn.addEventListener("click", () => {
  runSpinMode("single");
});

spinTenBtn.addEventListener("click", () => {
  runSpinMode("ten");
});

autoSpinBtn.addEventListener("click", () => {
  runSpinMode("auto");
});

stopBtn.addEventListener("click", stopCurrentMode);


// =========================
// 初始化
// =========================
for (let i = 0; i < 5; i += 1) {
  setSlotSymbol(i, SYMBOLS[i]);
}

setSelectedBet(selectedBet);
setRunningState(false);