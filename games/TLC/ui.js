const tg = window.Telegram?.WebApp;

if (tg) {
  tg.ready();
  tg.expand();
}

const targetEls = [
  document.getElementById("target-0"),
  document.getElementById("target-1"),
  document.getElementById("target-2"),
  document.getElementById("target-3")
];

const currentCodeEl = document.getElementById("current-code");
const statusTextEl = document.getElementById("status-text");
const tlcAmountEl = document.getElementById("tlc-amount");
const tryCountEl = document.getElementById("try-count");

const startBtn = document.getElementById("start-btn");
const stopBtn = document.getElementById("stop-btn");

let targetCodes = [];
let timer = null;
let tryCount = 0;
let tlc = 0;


// =========================
// 產生四位數字
// 前端只負責嘗試碼
// 目標碼由後端 API 給
// =========================
function generateCode() {
  const number = Math.floor(Math.random() * 10000);

  return String(number).padStart(4, "0");
}


// =========================
// 讀取 TLC 目標碼
// =========================
async function loadTargetCodes() {
  try {
    const res = await fetch("/games/tlc/api/targets");
    const data = await res.json();

    targetCodes = data.target_codes;

    renderTargetCodes();

    statusTextEl.textContent = "目標碼已建立";
  } catch (error) {
    console.error(error);
    statusTextEl.textContent = "目標碼建立失敗";
  }
}


// =========================
// 顯示目標碼
// =========================
function renderTargetCodes() {
  targetCodes.forEach((code, index) => {
    targetEls[index].textContent = code;
    targetEls[index].classList.remove("target-hit");
  });
}


// =========================
// 更新畫面資料
// 目前 TLC 尚未寫 DB
// 這裡只是前端顯示用
// =========================
function renderPlayerState() {
  tlcAmountEl.textContent = `${tlc} TLC`;
  tryCountEl.textContent = tryCount;
}


// =========================
// 嘗試一次
// =========================
function tryOnce() {
  const code = generateCode();

  tryCount += 1;

  currentCodeEl.textContent = code;
  currentCodeEl.classList.remove("hit");

  if (targetCodes.includes(code)) {
    currentCodeEl.classList.add("hit");

    targetCodes.forEach((targetCode, index) => {
      if (targetCode === code) {
        targetEls[index].classList.add("target-hit");
      }
    });

    statusTextEl.textContent = `命中 ${code}，破解成功`;

    stopTlc();

    renderPlayerState();

    return;
  }

  statusTextEl.textContent = "破解中...";
  renderPlayerState();
}


// =========================
// 開始 TLC
// =========================
async function startTlc() {
  stopTlc();

  tryCount = 0;

  currentCodeEl.textContent = "0000";
  currentCodeEl.classList.remove("hit");

  await loadTargetCodes();

  renderPlayerState();

  statusTextEl.textContent = "破解中...";

  timer = setInterval(() => {
    tryOnce();
  }, 200);
}


// =========================
// 停止 TLC
// =========================
function stopTlc() {
  if (timer) {
    clearInterval(timer);
    timer = null;
  }
}


// =========================
// 按鈕事件
// =========================
startBtn.addEventListener("click", startTlc);

stopBtn.addEventListener("click", () => {
  stopTlc();
  statusTextEl.textContent = "已停止";
});


// =========================
// 初始化
// =========================
loadTargetCodes();
renderPlayerState();