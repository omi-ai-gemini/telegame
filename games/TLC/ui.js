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

const urlParams = new URLSearchParams(window.location.search);
const botId = urlParams.get("bot_id") || "";
const userId = tg?.initDataUnsafe?.user?.id
  ? String(tg.initDataUnsafe.user.id)
  : "";

let targetCodes = [];
let timer = null;
let tryCount = 0;
let hitCount = 0;
let tlc = 0;
let historyRecords = [];
let targetLoading = false;
let resolvingHit = false;


// =========================
// 確認是否能使用後端資源 API
// bot_id 由 WebApp URL 帶入
// user_id 由 Telegram WebApp 提供
// =========================
function hasPlayerIdentity() {
  return botId && userId;
}


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
// 從 DB 讀取目前 TLC 持有量
// =========================
async function loadBalance() {
  if (!hasPlayerIdentity()) {
    console.warn("missing player identity", { botId, userId });
    return;
  }

  try {
    const query = new URLSearchParams({
      bot_id: botId,
      user_id: userId
    });

    const res = await fetch(`/games/tlc/api/balance?${query.toString()}`);
    const data = await res.json();

    if (!res.ok || !data.ok) {
      throw new Error(data.error || "balance_load_failed");
    }

    tlc = Number(data.amount || 0);

    renderPlayerState();
  } catch (error) {
    console.error(error);
    statusTextEl.textContent = "TLC 餘額讀取失敗";
  }
}


// =========================
// 命中後向後端領取 TLC
// 產出數量由後端判定，並寫入 DB
// =========================
async function claimTlcReward() {
  if (!hasPlayerIdentity()) {
    throw new Error("missing_player_identity");
  }

  const res = await fetch("/games/tlc/api/reward", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      bot_id: botId,
      user_id: userId
    })
  });

  const data = await res.json();

  if (!res.ok || !data.ok) {
    throw new Error(data.error || "reward_claim_failed");
  }

  return data;
}


// =========================
// 更新畫面資料
// TLC 持有量來自 DB 回傳
// 嘗試次數只記錄本次遊玩
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
// 歷史紀錄只存在本次前端 RAM，不寫 DB
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
// 命中後結算 TLC，再刷新下一輪目標碼
// 不停止遊戲，讓破譯繼續跑
// =========================
async function handleHit(code) {
  resolvingHit = true;

  try {
    statusTextEl.textContent = `命中 ${code}，結算中...`;

    const result = await claimTlcReward();
    const reward = Number(result.reward || 0);

    tlc = Number(result.amount || 0);

    addHistoryRecord(code, reward);
    renderPlayerState();

    statusTextEl.textContent = `命中 ${code}，產出 ${reward} TLC`;

    await loadTargetCodes();

    if (timer) {
      statusTextEl.textContent = "命中完成，繼續破譯中...";
    }
  } catch (error) {
    console.error(error);

    stopTlc();
    statusTextEl.textContent = "產出寫入失敗，已停止";
  } finally {
    resolvingHit = false;
  }
}


// =========================
// 嘗試一次
// =========================
function tryOnce() {
  if (targetLoading || resolvingHit || targetCodes.length === 0) {
    statusTextEl.textContent = "等待破譯資料...";
    return;
  }

  const code = generateCode();

  tryCount += 1;

  currentCodeEl.textContent = code;
  currentCodeEl.classList.remove("hit");

  if (targetCodes.includes(code)) {
    currentCodeEl.classList.add("hit");

    renderPlayerState();
    handleHit(code);

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

  await loadBalance();
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
loadBalance();
loadTargetCodes();
renderPlayerState();
renderHistoryRecords();
