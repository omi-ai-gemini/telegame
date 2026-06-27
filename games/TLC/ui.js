const tg = window.Telegram?.WebApp;

if (tg) {
  tg.ready();
  tg.expand();
}

const currentCodeEl = document.getElementById("current-code");
const statusTextEl = document.getElementById("status-text");
const tlcAmountEl = document.getElementById("tlc-amount");
const tryCountEl = document.getElementById("try-count");
const historyListEl = document.getElementById("history-list");

const startBtn = document.getElementById("start-btn");
const stopBtn = document.getElementById("stop-btn");

let targetCodes = [];
let timer = null;
let tryCount = 0;
let hitCount = 0;
let tlc = 0;
let historyRecords = [];
let targetLoading = false;


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
// 命中後產出 TLC
// 目前只用前端亂數，不寫 DB
// 0 代表空包
// =========================
function generateTlcReward() {
  const isEmpty = Math.random() < 0.3;

  if (isEmpty) {
    return 0;
  }

  return Math.floor(Math.random() * 10) + 1;
}


// =========================
// 讀取 TLC 目標碼
// 目標碼只保留在前端記憶體內判定
// 不再顯示於畫面
// =========================
async function loadTargetCodes() {
  targetLoading = true;
  targetCodes = [];

  try {
    const res = await fetch("/games/tlc/api/targets");
    const data = await res.json();

    targetCodes = data.target_codes;

    statusTextEl.textContent = "破譯資料已建立";
  } catch (error) {
    console.error(error);
    statusTextEl.textContent = "破譯資料建立失敗";
  } finally {
    targetLoading = false;
  }
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
// 顯示本次遊玩歷史紀錄
// 新紀錄永遠放第一筆
// CSS 限制三行高度，超過後用垂直卷軸查看
// =========================
function renderHistoryRecords() {
  if (historyRecords.length === 0) {
    historyListEl.innerHTML = '<div class="history-empty">尚無命中紀錄</div>';
    return;
  }

  historyListEl.innerHTML = historyRecords
    .map((record) => {
      return `
        <div class="history-row">
          <span class="history-code">#${record.hitCount}｜${record.code}</span>
          <span class="history-reward">${record.reward} TLC</span>
        </div>
      `;
    })
    .join("");
}


// =========================
// 新增命中紀錄
// =========================
function addHistoryRecord(code, reward) {
  hitCount += 1;

  historyRecords.unshift({
    hitCount,
    code,
    reward
  });

  renderHistoryRecords();
}


// =========================
// 命中後刷新下一輪目標碼
// 不停止遊戲，讓破譯繼續跑
// =========================
async function continueAfterHit() {
  await loadTargetCodes();

  if (timer) {
    statusTextEl.textContent = "命中完成，繼續破譯中...";
  }
}


// =========================
// 嘗試一次
// =========================
function tryOnce() {
  if (targetLoading || targetCodes.length === 0) {
    statusTextEl.textContent = "等待破譯資料...";
    return;
  }

  const code = generateCode();

  tryCount += 1;

  currentCodeEl.textContent = code;
  currentCodeEl.classList.remove("hit");

  if (targetCodes.includes(code)) {
    const reward = generateTlcReward();

    tlc += reward;

    currentCodeEl.classList.add("hit");
    statusTextEl.textContent = `命中 ${code}，產出 ${reward} TLC`;

    addHistoryRecord(code, reward);
    renderPlayerState();

    continueAfterHit();

    return;
  }

  statusTextEl.textContent = "破譯中...";
  renderPlayerState();
}


// =========================
// 開始 TLC
// =========================
async function startTlc() {
  stopTlc();

  tryCount = 0;
  hitCount = 0;
  historyRecords = [];

  currentCodeEl.textContent = "0000";
  currentCodeEl.classList.remove("hit");

  renderHistoryRecords();

  await loadTargetCodes();

  renderPlayerState();

  statusTextEl.textContent = "破譯中...";

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
renderHistoryRecords();
