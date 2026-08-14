/**
 * QUANTUM PRO — FULL FRONTEND CONTROLLER & INTERACTIVE ENGINES
 * Complete Migration of all 4-Systems, Harvester, AI Planner, Presets, Charts, & Backtest
 */

const STATE = {
  activeSymbol: "BTC-USD",
  activePeriod: "3mo",
  activeInterval: "1d",
  chartData: [],
  tickers: [],
  strategies: [],
  positions: [],
  systemsData: {},
  systemsChartData: [],
  systemsChartPeriod: "3mo",
  systemsChartMode: "PCT",
  visibleSystems: { unified: true, us: true, gold: true, crypto: true, forex: true },
  harvesterData: {},
  aiPlan: null,
  robotEnabled: true,
  activeStrategyKey: "TREND_FOLLOWING",
  pollingTimer: null
};

// ----------------- DOM ELEMENTS -----------------
const DOM = {
  botPulse: document.getElementById("bot-pulse"),
  botStatusText: document.getElementById("bot-status-text"),
  masterRobotToggle: document.getElementById("master-robot-toggle"),
  hudNetWorth: document.getElementById("hud-net-worth"),
  hudNetPnl: document.getElementById("hud-net-pnl"),
  hudRealizedPnl: document.getElementById("hud-realized-pnl"),
  hudClosedTrades: document.getElementById("hud-closed-trades"),
  hudVaultLocked: document.getElementById("hud-vault-locked"),
  hudWinRate: document.getElementById("hud-win-rate"),
  hudWinBar: document.getElementById("hud-win-bar"),
  hudMarketUs: document.getElementById("hud-market-us"),
  hudMarketForex: document.getElementById("hud-market-forex"),
  tickerRibbon: document.getElementById("ticker-ribbon"),
  navTabs: document.querySelectorAll(".nav-tab"),
  viewPanels: document.querySelectorAll(".view-panel"),
  btnPanicAll: document.getElementById("btn-panic-all"),
  toastContainer: document.getElementById("toast-container"),

  // Systems Overview & Unified Chart
  systemsCardsGrid: document.getElementById("systems-cards-grid"),
  btnApplyAllAiStrats: document.getElementById("btn-apply-all-ai-strats"),
  masterHoldingsTbody: document.getElementById("master-holdings-tbody"),
  masterPositionsCount: document.getElementById("master-positions-count"),
  unifiedSystemsCanvas: document.getElementById("unified-systems-chart"),
  sysChartTooltip: document.getElementById("sys-chart-tooltip"),
  sysChartModeBtns: document.getElementById("sys-chart-mode-btns"),
  sysChartPeriodBtns: document.getElementById("sys-chart-period-btns"),
  legendItems: document.querySelectorAll(".u-legend-item"),
  ulUnifiedVal: document.getElementById("ul-unified-val"),
  ulUsVal: document.getElementById("ul-us-val"),
  ulGoldVal: document.getElementById("ul-gold-val"),
  ulCryptoVal: document.getElementById("ul-crypto-val"),
  ulForexVal: document.getElementById("ul-forex-val"),

  // Terminal & Chart
  chartSymbolTitle: document.getElementById("chart-symbol-title"),
  chartLatestPrice: document.getElementById("chart-latest-price"),
  chartSignalTag: document.getElementById("chart-signal-tag"),
  chartPeriodBtns: document.getElementById("chart-period-btns"),
  canvas: document.getElementById("trading-chart"),
  chartTooltip: document.getElementById("chart-tooltip"),
  mtfConfluenceBadge: document.getElementById("mtf-confluence-badge"),
  mtfGridContainer: document.getElementById("mtf-grid-container"),
  orderSymbolSelect: document.getElementById("order-symbol-select"),
  orderQty: document.getElementById("order-qty"),
  btnStepMinus: document.getElementById("btn-step-minus"),
  btnStepPlus: document.getElementById("btn-step-plus"),
  btnQuickBuy: document.getElementById("btn-quick-buy"),
  btnQuickSell: document.getElementById("btn-quick-sell"),
  positionsList: document.getElementById("positions-list"),
  positionsCount: document.getElementById("positions-count"),

  // Harvester
  harvestUnrealizedVal: document.getElementById("harvest-unrealized-val"),
  harvestVaultVal: document.getElementById("harvest-vault-val"),
  btnTriggerHarvest: document.getElementById("btn-trigger-harvest"),
  hmTodayThb: document.getElementById("hm-today-thb"),
  hmYesterdayThb: document.getElementById("hm-yesterday-thb"),
  hmAlltimeThb: document.getElementById("hm-alltime-thb"),
  hmDaysCount: document.getElementById("hm-days-count"),
  hmPctVsYesterday: document.getElementById("hm-pct-vs-yesterday"),
  harvestHistoryCanvas: document.getElementById("harvest-history-chart"),

  // AI Planner
  btnScanAiNow: document.getElementById("btn-scan-ai-now"),
  aiPlansContainer: document.getElementById("ai-plans-container"),

  // Strategies & Presets
  presetCards: document.querySelectorAll(".preset-mode-card"),
  strategyGrid: document.getElementById("strategy-grid"),

  // Backtest
  btnRunBacktest: document.getElementById("btn-run-backtest"),
  equityCanvas: document.getElementById("equity-chart"),

  // Logs
  logsTbody: document.getElementById("logs-tbody"),
  btnRefreshLogs: document.getElementById("btn-refresh-logs"),

  // Settings
  btnSaveBrokerKeys: document.getElementById("btn-save-broker-keys"),
  btnTestTg: document.getElementById("btn-test-tg"),
  btnTestDiscord: document.getElementById("btn-test-discord")
};

// ----------------- TOAST HELPER -----------------
function showToast(message, type = "info") {
  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.textContent = message;
  DOM.toastContainer.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = "0";
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

// ----------------- INITIALIZATION -----------------
document.addEventListener("DOMContentLoaded", () => {
  setupNavigation();
  setupEventListeners();
  initCanvas();
  initUnifiedCanvas();
  fetchInitialData();
  startRealtimePolling();
});

// ----------------- NAVIGATION -----------------
function setupNavigation() {
  DOM.navTabs.forEach(tab => {
    tab.addEventListener("click", () => {
      DOM.navTabs.forEach(t => t.classList.remove("active"));
      DOM.viewPanels.forEach(p => p.classList.remove("active"));

      tab.classList.add("active");
      const targetId = tab.getAttribute("data-view");
      const panel = document.getElementById(targetId);
      if (panel) panel.classList.add("active");

      // Redraw charts or trigger tab specific fetchers
      if (targetId === "view-systems") { fetchSystemsChart(STATE.systemsChartPeriod); renderUnifiedSystemsChart(); }
      if (targetId === "view-terminal") renderChart();
      if (targetId === "view-harvester") { fetchHarvester(); renderHarvestChart(); }
      if (targetId === "view-ai-planner") fetchAiPlannerQueue();
      if (targetId === "view-logs") fetchTradeLogs();
    });
  });
}

// ----------------- EVENT LISTENERS -----------------
function setupEventListeners() {
  // Unified Systems Chart Controls (Mode: PCT vs VAL)
  if (DOM.sysChartModeBtns) {
    DOM.sysChartModeBtns.querySelectorAll("button").forEach(btn => {
      btn.addEventListener("click", () => {
        DOM.sysChartModeBtns.querySelectorAll("button").forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        STATE.systemsChartMode = btn.getAttribute("data-mode");
        renderUnifiedSystemsChart();
      });
    });
  }

  // Unified Systems Chart Timeframes (1M, 3M, 6M, 1Y)
  if (DOM.sysChartPeriodBtns) {
    DOM.sysChartPeriodBtns.querySelectorAll("button").forEach(btn => {
      btn.addEventListener("click", () => {
        DOM.sysChartPeriodBtns.querySelectorAll("button").forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        STATE.systemsChartPeriod = btn.getAttribute("data-period");
        fetchSystemsChart(STATE.systemsChartPeriod);
      });
    });
  }

  // Unified Systems Legend Toggles
  if (DOM.legendItems) {
    DOM.legendItems.forEach(item => {
      item.addEventListener("click", () => {
        const asset = item.getAttribute("data-asset");
        STATE.visibleSystems[asset] = !STATE.visibleSystems[asset];
        item.classList.toggle("dimmed", !STATE.visibleSystems[asset]);
        renderUnifiedSystemsChart();
      });
    });
  }
  // Master Switch
  DOM.masterRobotToggle.addEventListener("change", async (e) => {
    const enabled = e.target.checked;
    updateRobotStateUI(enabled);
    try {
      const res = await fetch("/api/robot/toggle", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ enabled })
      });
      const data = await res.json();
      showToast(data.message || (enabled ? "🟢 Robot Started" : "🔴 Robot Paused"), "success");
    } catch (err) {
      showToast("Error updating robot state", "error");
    }
  });

  // Panic Button
  DOM.btnPanicAll.addEventListener("click", async () => {
    if (!confirm("🚨 ยืนยันการปิดทุกออเดอร์ฉุกเฉิน (Emergency Liquidate All)?")) return;
    try {
      const res = await fetch("/api/robot/panic-close", { method: "POST" });
      const data = await res.json();
      showToast(data.message, "success");
      fetchStatus();
      fetchPositions();
    } catch (err) {
      showToast("Panic close failed: " + err, "error");
    }
  });

  // Bulk Apply AI Strategies
  DOM.btnApplyAllAiStrats.addEventListener("click", async () => {
    try {
      DOM.btnApplyAllAiStrats.textContent = "⏳ กำลังปรับกลยุทธ์ตาม AI...";
      const res = await fetch("/api/ai-planner/apply-all", { method: "POST" });
      const data = await res.json();
      DOM.btnApplyAllAiStrats.innerHTML = `<span>🤖 ⚡ ปรับกลยุทธ์ทั้ง 4 สินทรัพย์ตาม AI แนะนำ</span>`;
      showToast(data.message, "success");
      fetchStatus();
      fetchStrategies();
    } catch (err) {
      DOM.btnApplyAllAiStrats.innerHTML = `<span>🤖 ⚡ ปรับกลยุทธ์ทั้ง 4 สินทรัพย์ตาม AI แนะนำ</span>`;
      showToast("AI strategy apply failed: " + err, "error");
    }
  });

  // Chart Period Buttons
  DOM.chartPeriodBtns.querySelectorAll("button").forEach(btn => {
    btn.addEventListener("click", () => {
      DOM.chartPeriodBtns.querySelectorAll("button").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      STATE.activePeriod = btn.getAttribute("data-period");
      fetchMarketChart(STATE.activeSymbol, STATE.activePeriod);
    });
  });

  // Order Stepper
  DOM.btnStepMinus.addEventListener("click", () => {
    let val = parseFloat(DOM.orderQty.value) || 0.1;
    val = Math.max(0.01, val - 0.05);
    DOM.orderQty.value = val.toFixed(2);
  });

  DOM.btnStepPlus.addEventListener("click", () => {
    let val = parseFloat(DOM.orderQty.value) || 0.1;
    val += 0.05;
    DOM.orderQty.value = val.toFixed(2);
  });

  // Quick Buy / Sell
  DOM.btnQuickBuy.addEventListener("click", () => handleQuickOrder("BUY"));
  DOM.btnQuickSell.addEventListener("click", () => handleQuickOrder("SELL"));

  // Order Symbol Change
  DOM.orderSymbolSelect.addEventListener("change", (e) => {
    STATE.activeSymbol = e.target.value;
    DOM.chartSymbolTitle.textContent = `${STATE.activeSymbol}`;
    fetchMarketChart(STATE.activeSymbol, STATE.activePeriod);
  });

  // Trigger Daily Harvest
  DOM.btnTriggerHarvest.addEventListener("click", async () => {
    try {
      const res = await fetch("/api/harvester/execute", { method: "POST" });
      const data = await res.json();
      if (data.success) {
        showToast(`🎉 ล็อกกำไรสำเร็จ: +฿${data.harvested_thb.toFixed(2)} ย้ายเข้าตู้เซฟแล้ว!`, "success");
      } else {
        showToast(data.message || "ยอดกำไรยังไม่ถึงเกณฑ์ขั้นต่ำ ฿300", "info");
      }
      fetchHarvester();
      fetchStatus();
    } catch (err) {
      showToast("Harvest error: " + err, "error");
    }
  });

  // Trigger AI Scan
  DOM.btnScanAiNow.addEventListener("click", async () => {
    DOM.btnScanAiNow.textContent = "⏳ Scanning 24/7 Global Intelligence...";
    await fetchAiPlannerQueue();
    DOM.btnScanAiNow.innerHTML = `<span>⚡ สแกนข่าวและวิเคราะห์ตลาดใหม่ทันที</span>`;
    showToast("สแกนข่าวและอัปเดตแผน AI เรียบร้อย!", "success");
  });

  // Preset Risk Buttons
  DOM.presetCards.forEach(card => {
    const btn = card.querySelector(".btn-preset-apply");
    btn.addEventListener("click", async () => {
      const mode = card.getAttribute("data-mode");
      DOM.presetCards.forEach(c => c.classList.remove("active-preset"));
      card.classList.add("active-preset");
      try {
        const res = await fetch("/api/strategy-presets/apply", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ mode })
        });
        const d = await res.json();
        showToast(d.message, "success");
      } catch (err) {
        showToast("Error applying preset", "error");
      }
    });
  });

  // Run Backtest
  DOM.btnRunBacktest.addEventListener("click", handleRunBacktest);

  // Refresh Logs
  DOM.btnRefreshLogs.addEventListener("click", fetchTradeLogs);

  // Broker Keys Save
  DOM.btnSaveBrokerKeys.addEventListener("click", async () => {
    const alpacaKey = document.getElementById("cfg-alpaca-key").value;
    const alpacaSecret = document.getElementById("cfg-alpaca-secret").value;
    const settradeId = document.getElementById("cfg-settrade-id").value;
    const settradeSecret = document.getElementById("cfg-settrade-secret").value;

    const payload = {
      credentials: {
        alpaca: { api_key: alpacaKey, secret_key: alpacaSecret },
        settrade: { app_id: settradeId, app_secret: settradeSecret }
      }
    };

    try {
      const res = await fetch("/api/broker-credentials/save", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const d = await res.json();
      showToast(d.message, "success");
    } catch (err) {
      showToast("Error saving credentials: " + err, "error");
    }
  });

  // Notification Test Buttons
  DOM.btnTestTg.addEventListener("click", async () => {
    const token = document.getElementById("cfg-tg-token").value;
    const chatId = document.getElementById("cfg-tg-chat").value;
    try {
      const res = await fetch("/api/test-notification", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ channel: "telegram", token, chat_id: chatId })
      });
      const d = await res.json();
      showToast(d.message, d.success ? "success" : "error");
    } catch (err) {
      showToast("Telegram test failed: " + err, "error");
    }
  });

  DOM.btnTestDiscord.addEventListener("click", async () => {
    const url = document.getElementById("cfg-discord-url").value;
    try {
      const res = await fetch("/api/test-notification", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ channel: "discord", webhook_url: url })
      });
      const d = await res.json();
      showToast(d.message, d.success ? "success" : "error");
    } catch (err) {
      showToast("Discord test failed: " + err, "error");
    }
  });
}

// ----------------- POLLING & DATA -----------------
function startRealtimePolling() {
  fetchStatus();
  fetchTickers();
  fetchMarketChart(STATE.activeSymbol, STATE.activePeriod);
  fetchStrategies();
  fetchPositions();
  fetchHarvester();
  fetchAiPlannerQueue();

  STATE.pollingTimer = setInterval(() => {
    fetchStatus();
    fetchTickers();
    fetchPositions();
    fetchHarvester();
  }, 3500);
}

async function fetchInitialData() {
  await fetchStatus();
  await fetchTickers();
  await fetchStrategies();
  await fetchMarketChart(STATE.activeSymbol, STATE.activePeriod);
  await fetchSystemsChart(STATE.systemsChartPeriod);
}

async function fetchStatus() {
  try {
    const res = await fetch("/api/status");
    const data = await res.json();
    if (!data.success) return;

    STATE.robotEnabled = data.robot_enabled;
    DOM.masterRobotToggle.checked = data.robot_enabled;
    updateRobotStateUI(data.robot_enabled);

    DOM.hudNetWorth.textContent = `฿${data.total_portfolio_value_thb.toLocaleString('en-US', { minimumFractionDigits: 2 })}`;
    DOM.hudNetPnl.textContent = `${data.net_pnl_pct >= 0 ? '+' : ''}${data.net_pnl_pct.toFixed(2)}%`;
    DOM.hudNetPnl.className = `metric-sub ${data.net_pnl_pct >= 0 ? 'positive' : 'negative'}`;

    DOM.hudRealizedPnl.textContent = `${data.total_realized_pnl_thb >= 0 ? '+' : ''}฿${data.total_realized_pnl_thb.toLocaleString('en-US', { minimumFractionDigits: 2 })}`;
    DOM.hudRealizedPnl.className = `metric-val mono ${data.total_realized_pnl_thb >= 0 ? 'positive' : 'negative'}`;

    DOM.hudVaultLocked.textContent = `฿${data.total_vault_locked_thb.toLocaleString('en-US', { minimumFractionDigits: 2 })}`;
    DOM.hudClosedTrades.textContent = `${data.total_trades} Closed Trades`;
    DOM.hudWinRate.textContent = `${data.win_rate_pct.toFixed(1)}%`;
    DOM.hudWinBar.style.width = `${data.win_rate_pct}%`;

    // Market badges
    if (data.market_statuses) {
      const ms = data.market_statuses;
      DOM.hudMarketUs.className = `status-pill ${ms.us.open ? 'open' : ''}`;
      DOM.hudMarketUs.textContent = ms.us.open ? "🟢 US OPEN" : "🔴 US CLOSED";
      DOM.hudMarketForex.className = `status-pill ${ms.forex.open ? 'open' : ''}`;
      DOM.hudMarketForex.textContent = ms.forex.open ? "🟢 FOREX OPEN" : "🔴 FOREX CLOSED";
    }

    // 4 Systems Grid
    if (data.systems) {
      STATE.systemsData = data.systems;
      render4SystemsCards(data.systems);
    }
  } catch (err) {
    console.error("Status fetch error", err);
  }
}

function updateRobotStateUI(enabled) {
  if (enabled) {
    DOM.botPulse.className = "pulse-dot active";
    DOM.botStatusText.textContent = "AI ENGINE: ONLINE (24/7)";
    DOM.botStatusText.style.color = "var(--accent-emerald)";
  } else {
    DOM.botPulse.className = "pulse-dot";
    DOM.botStatusText.textContent = "AI ENGINE: PAUSED";
    DOM.botStatusText.style.color = "var(--accent-coral)";
  }
}

function render4SystemsCards(systems) {
  DOM.systemsCardsGrid.innerHTML = "";
  for (const [key, sys] of Object.entries(systems)) {
    const card = document.createElement("div");
    card.className = "system-card";

    const pnlSign = sys.net_pnl_thb >= 0 ? '+' : '';
    const pnlClass = sys.net_pnl_thb >= 0 ? 'positive' : 'negative';

    card.innerHTML = `
      <div class="sys-card-header">
        <div class="sys-title-group">
          <h3>${sys.name}</h3>
          <span class="sys-alloc-badge">Alloc: ฿${sys.allocation_thb.toLocaleString()} (฿${sys.portfolio_val_thb.toLocaleString()})</span>
        </div>
        <span class="signal-tag ${sys.net_pnl_pct >= 0 ? 'buy' : 'sell'}">${pnlSign}${sys.net_pnl_pct.toFixed(2)}%</span>
      </div>

      <div class="sys-pnl-banner">
        <div>
          <span class="metric-label">กำไร/ขาดทุนสุทธิ (Net P&L)</span>
          <div class="sys-pnl-val mono ${pnlClass}">${pnlSign}฿${sys.net_pnl_thb.toLocaleString('en-US', { minimumFractionDigits: 2 })}</div>
        </div>
        <div style="text-align: right;">
          <span class="metric-label">Win Rate</span>
          <div class="mono" style="font-weight: 700;">${sys.win_rate_pct.toFixed(1)}%</div>
        </div>
      </div>

      <div class="sys-stats-row">
        <div class="stat-item"><span>สะสม Take Profit:</span> <strong class="positive">+฿${sys.cumulative_take_profit_thb.toLocaleString()}</strong></div>
        <div class="stat-item"><span>สะสม Cut Loss:</span> <strong class="negative">-฿${sys.cumulative_cut_loss_thb.toLocaleString()}</strong></div>
        <div class="stat-item"><span>จำนวนไม้ปิดแล้ว:</span> <strong>${sys.closed_trades_count} ไม้</strong></div>
        <div class="stat-item"><span>กำลังถือครอง:</span> <strong>${sys.active_holdings_count} ไม้</strong></div>
      </div>

      <div class="sys-strategy-selector">
        <label>Active Strategy for ${key}:</label>
        <select class="cyber-select sys-strat-dropdown" data-system="${key}">
          <option value="TREND_FOLLOWING" ${sys.active_strategy === 'TREND_FOLLOWING' ? 'selected' : ''}>Trend Following (EMA/RSI)</option>
          <option value="GRID_TRADING" ${sys.active_strategy === 'GRID_TRADING' ? 'selected' : ''}>Grid Trading</option>
          <option value="MEAN_REVERSION" ${sys.active_strategy === 'MEAN_REVERSION' ? 'selected' : ''}>Mean Reversion</option>
          <option value="VOLATILITY_BREAKOUT" ${sys.active_strategy === 'VOLATILITY_BREAKOUT' ? 'selected' : ''}>Volatility Breakout</option>
          <option value="DCA_REBALANCE" ${sys.active_strategy === 'DCA_REBALANCE' ? 'selected' : ''}>DCA & Rebalance</option>
          <option value="NLP_SENTIMENT" ${sys.active_strategy === 'NLP_SENTIMENT' ? 'selected' : ''}>AI NLP Sentiment</option>
        </select>
      </div>
    `;

    card.querySelector(".sys-strat-dropdown").addEventListener("change", async (e) => {
      const newStrat = e.target.value;
      try {
        const r = await fetch("/api/strategy/set-active", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ strategy_key: newStrat, system: key })
        });
        const d = await r.json();
        showToast(d.message, "success");
        fetchStatus();
      } catch (err) {
        showToast("Strategy switch failed", "error");
      }
    });

    DOM.systemsCardsGrid.appendChild(card);
  }
}

async function fetchTickers() {
  try {
    const res = await fetch("/api/tickers");
    const data = await res.json();
    if (!data.success || !data.tickers) return;

    STATE.tickers = data.tickers;
    renderTickerRibbon(data.tickers);
  } catch (err) {
    console.error("Tickers fetch error", err);
  }
}

function renderTickerRibbon(tickers) {
  DOM.tickerRibbon.innerHTML = "";
  tickers.forEach(t => {
    const card = document.createElement("div");
    card.className = `ticker-card ${t.symbol === STATE.activeSymbol ? 'active-ticker' : ''}`;
    const changeClass = t.change_pct >= 0 ? 'positive' : 'negative';
    const sign = t.change_pct >= 0 ? '+' : '';

    card.innerHTML = `
      <span class="t-icon">${t.icon}</span>
      <div class="t-details">
        <span class="t-symbol">${t.symbol}</span>
        <span class="t-price mono">$${t.price.toLocaleString('en-US', { minimumFractionDigits: 2 })}</span>
        <span class="t-change mono ${changeClass}">${sign}${t.change_pct.toFixed(2)}%</span>
      </div>
    `;

    card.addEventListener("click", () => {
      STATE.activeSymbol = t.symbol;
      DOM.orderSymbolSelect.value = t.symbol;
      DOM.chartSymbolTitle.textContent = `${t.name} (${t.symbol})`;
      fetchMarketChart(t.symbol, STATE.activePeriod);
      renderTickerRibbon(STATE.tickers);
    });

    DOM.tickerRibbon.appendChild(card);
  });
}

async function fetchMarketChart(symbol, period = "3mo") {
  try {
    const res = await fetch(`/api/market-chart?symbol=${symbol}&period=${period}`);
    const data = await res.json();
    if (!data.success) return;

    STATE.chartData = data.candles;
    DOM.chartLatestPrice.textContent = `$${data.latest_price.toLocaleString('en-US', { minimumFractionDigits: 2 })}`;

    DOM.chartSignalTag.textContent = data.latest_signal_text;
    DOM.chartSignalTag.className = `signal-tag ${data.latest_signal === 1 ? 'buy' : data.latest_signal === -1 ? 'sell' : 'hold'}`;

    if (data.mtf_analysis) {
      renderMtfConfluence(data.mtf_analysis);
    }

    renderChart();
  } catch (err) {
    console.error("Market chart fetch error", err);
  }
}

function renderMtfConfluence(mtf) {
  DOM.mtfGridContainer.innerHTML = "";
  const tfs = ["15m", "1h", "4h", "1d"];
  tfs.forEach(tf => {
    const tInfo = mtf.timeframes ? mtf.timeframes[tf] : null;
    const trend = tInfo ? tInfo.trend : "SIDEWAY";
    const isBull = trend.includes("UP") || trend.includes("BULL");
    const isBear = trend.includes("DOWN") || trend.includes("BEAR");

    const cell = document.createElement("div");
    cell.className = "mtf-cell";
    cell.innerHTML = `
      <span class="tf-name">${tf.toUpperCase()}</span>
      <span class="tf-trend ${isBull ? 'positive' : isBear ? 'negative' : 'neutral'}">
        ${isBull ? '🟢 BULLISH' : isBear ? '🔴 BEARISH' : '⚪ SIDEWAY'}
      </span>
    `;
    DOM.mtfGridContainer.appendChild(cell);
  });

  const confScore = mtf.confluence_score || 85;
  DOM.mtfConfluenceBadge.textContent = `CONFLUENCE: ${confScore}% ALIGNMENT`;
}

async function fetchHarvester() {
  try {
    const res = await fetch("/api/harvester/status");
    const data = await res.json();
    if (!data.success) return;

    STATE.harvesterData = data;
    DOM.harvestUnrealizedVal.textContent = `+฿${data.unrealized_profit_thb.toLocaleString('en-US', { minimumFractionDigits: 2 })}`;
    DOM.harvestVaultVal.textContent = `฿${data.vault_locked_total_thb.toLocaleString('en-US', { minimumFractionDigits: 2 })}`;
    DOM.hmTodayThb.textContent = `฿${data.today_thb.toLocaleString('en-US', { minimumFractionDigits: 2 })}`;
    DOM.hmYesterdayThb.textContent = `฿${data.yesterday_thb.toLocaleString('en-US', { minimumFractionDigits: 2 })}`;
    DOM.hmAlltimeThb.textContent = `฿${data.all_time_vault_thb.toLocaleString('en-US', { minimumFractionDigits: 2 })}`;
    DOM.hmDaysCount.textContent = `${data.harvest_days_count} วัน`;
    DOM.hmPctVsYesterday.textContent = `${data.pct_vs_yesterday >= 0 ? '+' : ''}${data.pct_vs_yesterday.toFixed(1)}% vs เมื่อวาน`;

    if (data.can_harvest_now) {
      DOM.btnTriggerHarvest.style.animation = "pulseGlow 1.5s infinite";
      DOM.btnTriggerHarvest.innerHTML = `<span>🎯 กดเก็บกำไร ( ฿${data.unrealized_profit_thb.toFixed(0)} ) เข้าตู้เซฟ</span>`;
    } else {
      DOM.btnTriggerHarvest.style.animation = "none";
      DOM.btnTriggerHarvest.innerHTML = `<span>🔒 รอครบเป้า ฿300 (มี +฿${data.unrealized_profit_thb.toFixed(0)})</span>`;
    }

    renderHarvestChart();
  } catch (err) {
    console.error("Harvester fetch error", err);
  }
}

function renderHarvestChart() {
  const canvas = DOM.harvestHistoryCanvas;
  if (!canvas || !STATE.harvesterData || !STATE.harvesterData.chart_history) return;

  const records = STATE.harvesterData.chart_history;
  if (records.length === 0) return;

  const dpr = window.devicePixelRatio || 1;
  const rect = canvas.getBoundingClientRect();
  canvas.width = rect.width * dpr;
  canvas.height = rect.height * dpr;
  const hCtx = canvas.getContext("2d");
  hCtx.scale(dpr, dpr);

  const w = rect.width;
  const h = rect.height;
  hCtx.clearRect(0, 0, w, h);

  const pad = { top: 20, right: 50, bottom: 30, left: 20 };
  const cW = w - pad.left - pad.right;
  const cH = h - pad.top - pad.bottom;

  const barW = Math.max(8, (cW / records.length) * 0.5);
  const maxV = Math.max(...records.map(r => r.cumulative_vault), 1000);

  records.forEach((r, i) => {
    const x = pad.left + (i / records.length) * cW + barW;
    const barH = (r.harvested_thb / maxV) * cH;
    const y = h - pad.bottom - barH;

    // Draw Bar
    hCtx.fillStyle = "#ffb703";
    hCtx.fillRect(x, y, barW, barH);

    // Label
    if (i % 3 === 0) {
      hCtx.fillStyle = "#64748b";
      hCtx.font = "9px 'JetBrains Mono'";
      hCtx.fillText(r.date.slice(5), x - 6, h - 10);
    }
  });
}

async function fetchAiPlannerQueue() {
  try {
    const res = await fetch("/api/ai-planner/queue");
    const data = await res.json();
    if (!data.success || !data.plan) return;

    STATE.aiPlan = data.plan;
    renderAiPlanCards(data.plan);
  } catch (err) {
    console.error("AI Planner fetch error", err);
  }
}

function renderAiPlanCards(plan) {
  DOM.aiPlansContainer.innerHTML = "";
  const systems = plan.systems || {};

  for (const [sysKey, sysData] of Object.entries(systems)) {
    const plans = sysData.candidate_plans || [];
    plans.forEach(cp => {
      const card = document.createElement("div");
      card.className = "ai-plan-card";

      const stagesHtml = (cp.pipeline_steps || []).map(st => `
        <span class="stage-pill ${st.status === 'COMPLETED' ? 'done' : ''}">${st.name}</span>
      `).join("");

      card.innerHTML = `
        <div class="ai-plan-top">
          <div>
            <span class="ai-plan-sym">${cp.symbol}</span>
            <span class="strat-pill">${sysKey}</span>
          </div>
          <div class="ai-win-prob mono">โอกาสชนะ (Win Prob): ${cp.win_probability_pct}%</div>
        </div>

        <div class="ai-thought-box">
          <strong>🧠 AI Thought Breakdown:</strong> ${cp.ai_thought_rationale || cp.ai_summary}
        </div>

        <div class="ai-pipeline-stages">
          ${stagesHtml}
        </div>
      `;

      DOM.aiPlansContainer.appendChild(card);
    });
  }
}

async function fetchStrategies() {
  try {
    const res = await fetch("/api/strategies");
    const data = await res.json();
    if (!data.success || !data.strategies) return;

    STATE.strategies = data.strategies;
    STATE.activeStrategyKey = data.active_strategy;
    renderStrategiesGrid(data.strategies);
  } catch (err) {
    console.error("Strategies fetch error", err);
  }
}

function renderStrategiesGrid(strategies) {
  DOM.strategyGrid.innerHTML = "";
  strategies.forEach(s => {
    const card = document.createElement("div");
    card.className = `strategy-card ${s.is_active ? 'active-strategy' : ''}`;

    card.innerHTML = `
      ${s.is_active ? '<span class="strat-badge-active">ACTIVE ENGINE</span>' : ''}
      <div>
        <div class="strat-header">
          <span class="strat-icon">${s.icon}</span>
          <span class="strat-name">${s.name}</span>
        </div>
        <p class="strat-desc">${s.desc}</p>
      </div>
      <div>
        <div class="strat-meta">
          <span>ความเสี่ยง: <strong>${s.risk_level}</strong></span>
          <span>${s.level_label.split(" ")[0]}</span>
        </div>
        <button class="btn-activate-strat" data-key="${s.key}">
          ${s.is_active ? '✅ ใช้งานอยู่นี้' : '⚡ เปิดใช้งานกลยุทธ์นี้'}
        </button>
      </div>
    `;

    const btn = card.querySelector(".btn-activate-strat");
    btn.addEventListener("click", async () => {
      if (s.is_active) return;
      try {
        const res = await fetch("/api/strategy/set-active", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ strategy_key: s.key })
        });
        const resData = await res.json();
        showToast(resData.message, "success");
        fetchStrategies();
        fetchStatus();
      } catch (err) {
        showToast("Error switching strategy", "error");
      }
    });

    DOM.strategyGrid.appendChild(card);
  });
}

async function fetchPositions() {
  try {
    const res = await fetch("/api/positions");
    const data = await res.json();
    if (!data.success) return;

    DOM.positionsCount.textContent = `${data.positions.length} Open`;
    DOM.masterPositionsCount.textContent = `${data.positions.length} Positions`;

    if (data.positions.length === 0) {
      DOM.positionsList.innerHTML = `<div class="empty-state">ไม่มีสถานะถือครองในขณะนี้</div>`;
      DOM.masterHoldingsTbody.innerHTML = `<tr><td colspan="8" class="text-center" style="padding:24px;">No active positions currently.</td></tr>`;
      return;
    }

    // Side list
    DOM.positionsList.innerHTML = "";
    data.positions.forEach(p => {
      const item = document.createElement("div");
      item.className = "pos-item";
      const pnlClass = p.unrealized_pnl_thb >= 0 ? 'positive' : 'negative';
      const sign = p.unrealized_pnl_thb >= 0 ? '+' : '';

      item.innerHTML = `
        <div>
          <div class="pos-sym">${p.symbol}</div>
          <div class="pos-qty mono">${p.shares} units @ $${p.avg_price.toFixed(2)}</div>
        </div>
        <div style="display: flex; align-items: center;">
          <div class="pos-pnl mono ${pnlClass}">
            ${sign}฿${p.unrealized_pnl_thb.toLocaleString('en-US', { minimumFractionDigits: 2 })}
            <div style="font-size: 10px;">${sign}${p.pnl_pct.toFixed(2)}%</div>
          </div>
          <button class="btn-close-pos" data-sym="${p.symbol}" data-shares="${p.shares}" data-price="${p.current_price}">
            ปิดไม้
          </button>
        </div>
      `;
      DOM.positionsList.appendChild(item);
    });

    // Master Table
    DOM.masterHoldingsTbody.innerHTML = "";
    data.positions.forEach(p => {
      const tr = document.createElement("tr");
      const pnlClass = p.unrealized_pnl_thb >= 0 ? 'positive' : 'negative';
      const sign = p.unrealized_pnl_thb >= 0 ? '+' : '';

      tr.innerHTML = `
        <td><strong>${p.symbol}</strong></td>
        <td><span class="strat-pill">${p.category}</span></td>
        <td>${p.shares}</td>
        <td>$${p.avg_price.toFixed(2)}</td>
        <td>$${p.current_price.toFixed(2)}</td>
        <td class="${pnlClass}">${sign}฿${p.unrealized_pnl_thb.toLocaleString('en-US', { minimumFractionDigits: 2 })}</td>
        <td class="${pnlClass}">${sign}${p.pnl_pct.toFixed(2)}%</td>
        <td>
          <button class="btn-close-pos" data-sym="${p.symbol}" data-shares="${p.shares}" data-price="${p.current_price}">
            🚨 Force Sell
          </button>
        </td>
      `;
      DOM.masterHoldingsTbody.appendChild(tr);
    });

    // Bind Close Buttons
    document.querySelectorAll(".btn-close-pos").forEach(b => {
      b.addEventListener("click", async (e) => {
        const sym = e.target.getAttribute("data-sym");
        const shares = parseFloat(e.target.getAttribute("data-shares"));
        const price = parseFloat(e.target.getAttribute("data-price"));
        try {
          const r = await fetch("/api/manual-order", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ symbol: sym, action: "SELL", shares, price })
          });
          const d = await r.json();
          showToast(d.message, "success");
          fetchPositions();
          fetchStatus();
        } catch (err) {
          showToast("Close position failed", "error");
        }
      });
    });

  } catch (err) {
    console.error("Positions fetch error", err);
  }
}

async function handleQuickOrder(action) {
  const sym = DOM.orderSymbolSelect.value;
  const qty = parseFloat(DOM.orderQty.value) || 0.1;
  try {
    const res = await fetch("/api/manual-order", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ symbol: sym, action, shares: qty })
    });
    const data = await res.json();
    showToast(data.message, "success");
    fetchPositions();
    fetchStatus();
  } catch (err) {
    showToast(`Order failed: ${err}`, "error");
  }
}

async function handleRunBacktest() {
  DOM.btnRunBacktest.textContent = "⏳ Running Simulation...";
  const sym = document.getElementById("bt-symbol").value;
  const strat = document.getElementById("bt-strategy").value;
  const period = document.getElementById("bt-period").value;
  const tp = parseFloat(document.getElementById("bt-tp").value) || 8.0;
  const sl = parseFloat(document.getElementById("bt-sl").value) || -3.5;

  try {
    const res = await fetch("/api/backtest", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ symbol: sym, strategy_key: strat, period, tp_pct: tp, sl_pct: sl })
    });
    const data = await res.json();
    DOM.btnRunBacktest.textContent = "🚀 RUN BACKTEST";

    if (!data.success) {
      showToast(data.error || "Backtest failed", "error");
      return;
    }

    document.getElementById("bt-winrate").textContent = `${data.win_rate_pct.toFixed(1)}%`;
    document.getElementById("bt-trades-count").textContent = `${data.total_trades} Trades`;

    const netProfitEl = document.getElementById("bt-netprofit");
    const netThb = data.net_profit_thb || 0;
    netProfitEl.textContent = `${netThb >= 0 ? '+' : ''}฿${netThb.toLocaleString('en-US', { minimumFractionDigits: 2 })}`;
    netProfitEl.className = `bt-val mono ${netThb >= 0 ? 'positive' : 'negative'}`;

    document.getElementById("bt-return-pct").textContent = `${data.return_pct.toFixed(2)}% Return`;
    document.getElementById("bt-profitfactor").textContent = data.profit_factor.toFixed(2);
    document.getElementById("bt-maxdd").textContent = `${data.max_drawdown_pct.toFixed(2)}%`;

    renderEquityChart(data.equity_curve || []);
    showToast("Backtest simulation completed successfully!", "success");
  } catch (err) {
    DOM.btnRunBacktest.textContent = "🚀 RUN BACKTEST";
    showToast("Backtest failed: " + err, "error");
  }
}

async function fetchTradeLogs() {
  try {
    const res = await fetch("/api/trade-logs");
    const data = await res.json();
    if (!data.success || !data.logs) return;

    if (data.logs.length === 0) {
      DOM.logsTbody.innerHTML = `<tr><td colspan="8" class="text-center" style="padding:24px;">No execution logs found.</td></tr>`;
      return;
    }

    DOM.logsTbody.innerHTML = "";
    data.logs.forEach(log => {
      const tr = document.createElement("tr");
      const action = log.action || "BUY";
      tr.innerHTML = `
        <td>${log.timestamp || "-"}</td>
        <td><span class="badge-action ${action}">${action}</span></td>
        <td><strong>${log.symbol}</strong></td>
        <td>${log.shares}</td>
        <td>$${(log.price || 0).toLocaleString('en-US', { minimumFractionDigits: 2 })}</td>
        <td>฿${(log.total_thb || 0).toLocaleString('en-US', { minimumFractionDigits: 2 })}</td>
        <td style="color:var(--text-secondary); max-width:300px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">${log.reason || log.ai_summary || "-"}</td>
        <td><span class="positive">● EXECUTED</span></td>
      `;
      DOM.logsTbody.appendChild(tr);
    });
  } catch (err) {
    console.error("Logs fetch error", err);
  }
}

// ----------------- HIGH-PERFORMANCE 2D CANVAS CHARTS -----------------
let ctx, width, height;

function initCanvas() {
  const canvas = DOM.canvas;
  if (!canvas) return;
  const dpr = window.devicePixelRatio || 1;
  const rect = canvas.getBoundingClientRect();

  canvas.width = rect.width * dpr;
  canvas.height = rect.height * dpr;
  ctx = canvas.getContext("2d");
  ctx.scale(dpr, dpr);
  width = rect.width;
  height = rect.height;

  window.addEventListener("resize", () => {
    const r = canvas.getBoundingClientRect();
    canvas.width = r.width * dpr;
    canvas.height = r.height * dpr;
    ctx = canvas.getContext("2d");
    ctx.scale(dpr, dpr);
    width = r.width;
    height = r.height;
    renderChart();
  });
}

function renderChart() {
  if (!ctx || !STATE.chartData || STATE.chartData.length === 0) return;
  const data = STATE.chartData;
  ctx.clearRect(0, 0, width, height);

  const padding = { top: 20, right: 60, bottom: 30, left: 10 };
  const chartW = width - padding.left - padding.right;
  const chartH = height - padding.top - padding.bottom;

  let minP = Math.min(...data.map(d => d.low));
  let maxP = Math.max(...data.map(d => d.high));
  const rangeP = (maxP - minP) || 1;
  minP -= rangeP * 0.05;
  maxP += rangeP * 0.05;

  const getY = (p) => padding.top + chartH - ((p - minP) / (maxP - minP)) * chartH;
  const getX = (i) => padding.left + (i / (data.length - 1)) * chartW;

  // Grid
  ctx.strokeStyle = "rgba(255, 255, 255, 0.04)";
  ctx.lineWidth = 1;
  for (let i = 0; i <= 4; i++) {
    const y = padding.top + (chartH / 4) * i;
    ctx.beginPath();
    ctx.moveTo(padding.left, y);
    ctx.lineTo(width - padding.right, y);
    ctx.stroke();

    const pVal = maxP - (i / 4) * (maxP - minP);
    ctx.fillStyle = "#64748b";
    ctx.font = "10px 'JetBrains Mono'";
    ctx.fillText(`$${pVal.toFixed(1)}`, width - padding.right + 8, y + 3);
  }

  // EMA 50
  ctx.strokeStyle = "#ffb703";
  ctx.lineWidth = 1.5;
  ctx.beginPath();
  let firstEma50 = true;
  data.forEach((d, i) => {
    if (d.ema50 !== null) {
      const x = getX(i);
      const y = getY(d.ema50);
      if (firstEma50) { ctx.moveTo(x, y); firstEma50 = false; }
      else { ctx.lineTo(x, y); }
    }
  });
  ctx.stroke();

  // EMA 20
  ctx.strokeStyle = "#00c8ff";
  ctx.lineWidth = 1.8;
  ctx.beginPath();
  let firstEma20 = true;
  data.forEach((d, i) => {
    if (d.ema20 !== null) {
      const x = getX(i);
      const y = getY(d.ema20);
      if (firstEma20) { ctx.moveTo(x, y); firstEma20 = false; }
      else { ctx.lineTo(x, y); }
    }
  });
  ctx.stroke();

  // Candlesticks
  const candleW = Math.max(2, (chartW / data.length) * 0.65);
  data.forEach((d, i) => {
    const x = getX(i);
    const yO = getY(d.open);
    const yC = getY(d.close);
    const yH = getY(d.high);
    const yL = getY(d.low);

    const isBull = d.close >= d.open;
    ctx.strokeStyle = isBull ? "#00f090" : "#ff3b69";
    ctx.fillStyle = isBull ? "#00f090" : "#ff3b69";

    // Wick
    ctx.lineWidth = 1.2;
    ctx.beginPath();
    ctx.moveTo(x, yH);
    ctx.lineTo(x, yL);
    ctx.stroke();

    // Body
    const topY = Math.min(yO, yC);
    const bodyH = Math.max(2, Math.abs(yC - yO));
    ctx.fillRect(x - candleW / 2, topY, candleW, bodyH);

    // Signal Markers
    if (d.signal === 1) {
      ctx.fillStyle = "#00f090";
      ctx.beginPath();
      ctx.arc(x, yL + 12, 4, 0, Math.PI * 2);
      ctx.fill();
    } else if (d.signal === -1) {
      ctx.fillStyle = "#ff3b69";
      ctx.beginPath();
      ctx.arc(x, yH - 12, 4, 0, Math.PI * 2);
      ctx.fill();
    }
  });
}

function renderEquityChart(equityData) {
  const canvas = DOM.equityCanvas;
  if (!canvas || equityData.length === 0) return;

  const dpr = window.devicePixelRatio || 1;
  const rect = canvas.getBoundingClientRect();
  canvas.width = rect.width * dpr;
  canvas.height = rect.height * dpr;
  const eqCtx = canvas.getContext("2d");
  eqCtx.scale(dpr, dpr);

  const w = rect.width;
  const h = rect.height;
  eqCtx.clearRect(0, 0, w, h);

  const pad = { top: 20, right: 60, bottom: 20, left: 10 };
  const cW = w - pad.left - pad.right;
  const cH = h - pad.top - pad.bottom;

  const equities = equityData.map(e => e.Equity);
  let minE = Math.min(...equities);
  let maxE = Math.max(...equities);
  const range = (maxE - minE) || 1;
  minE -= range * 0.05;
  maxE += range * 0.05;

  const getY = (v) => pad.top + cH - ((v - minE) / (maxE - minE)) * cH;
  const getX = (i) => pad.left + (i / (equityData.length - 1)) * cW;

  const grad = eqCtx.createLinearGradient(0, pad.top, 0, h);
  grad.addColorStop(0, "rgba(0, 240, 144, 0.35)");
  grad.addColorStop(1, "rgba(0, 240, 144, 0.0)");

  eqCtx.beginPath();
  eqCtx.moveTo(getX(0), h - pad.bottom);
  equityData.forEach((d, i) => eqCtx.lineTo(getX(i), getY(d.Equity)));
  eqCtx.lineTo(getX(equityData.length - 1), h - pad.bottom);
  eqCtx.closePath();
  eqCtx.fillStyle = grad;
  eqCtx.fill();

  eqCtx.strokeStyle = "#00f090";
  eqCtx.lineWidth = 2.5;
  eqCtx.beginPath();
  equityData.forEach((d, i) => {
    if (i === 0) eqCtx.moveTo(getX(i), getY(d.Equity));
    else eqCtx.lineTo(getX(i), getY(d.Equity));
  });
  eqCtx.stroke();
}

// ----------------- UNIFIED 4-SYSTEMS PERFORMANCE CANVAS ENGINE -----------------
let uCtx, uWidth, uHeight;
let uHoverIndex = null;

function initUnifiedCanvas() {
  const canvas = DOM.unifiedSystemsCanvas;
  if (!canvas) return;
  const dpr = window.devicePixelRatio || 1;
  const rect = canvas.getBoundingClientRect();

  canvas.width = rect.width * dpr;
  canvas.height = rect.height * dpr;
  uCtx = canvas.getContext("2d");
  uCtx.scale(dpr, dpr);
  uWidth = rect.width;
  uHeight = rect.height;

  canvas.addEventListener("mousemove", (e) => {
    if (!STATE.systemsChartData || STATE.systemsChartData.length === 0) return;
    const r = canvas.getBoundingClientRect();
    const mouseX = e.clientX - r.left;
    const pad = { top: 25, right: 70, bottom: 25, left: 15 };
    const cW = uWidth - pad.left - pad.right;
    
    let index = Math.round(((mouseX - pad.left) / cW) * (STATE.systemsChartData.length - 1));
    index = Math.max(0, Math.min(STATE.systemsChartData.length - 1, index));
    uHoverIndex = index;
    renderUnifiedSystemsChart();

    const d = STATE.systemsChartData[index];
    const isVal = STATE.systemsChartMode === "VAL";
    if (DOM.sysChartTooltip && d) {
      DOM.sysChartTooltip.style.display = "block";
      DOM.sysChartTooltip.style.left = `${Math.min(uWidth - 190, Math.max(10, mouseX - 80))}px`;
      DOM.sysChartTooltip.style.top = "15px";
      DOM.sysChartTooltip.innerHTML = `
        <div style="font-weight:700; color:#f8fafc; border-bottom:1px solid rgba(255,255,255,0.1); padding-bottom:4px; margin-bottom:4px;">
          📅 ${d.date}
        </div>
        <div style="color:#00f090; font-weight:700;">🌐 Total: ${isVal ? '฿' + d.unified_val.toLocaleString('en-US', {minimumFractionDigits: 2}) : (d.unified_pct >= 0 ? '+' : '') + d.unified_pct.toFixed(2) + '%'}</div>
        <div style="color:#00c8ff;">🇺🇸 US: ${d.us_pct >= 0 ? '+' : ''}${d.us_pct.toFixed(2)}%</div>
        <div style="color:#ffb703;">🥇 Gold: ${d.gold_pct >= 0 ? '+' : ''}${d.gold_pct.toFixed(2)}%</div>
        <div style="color:#9d4edd;">🪙 Crypto: ${d.crypto_pct >= 0 ? '+' : ''}${d.crypto_pct.toFixed(2)}%</div>
        <div style="color:#ff3b69;">💱 Forex: ${d.forex_pct >= 0 ? '+' : ''}${d.forex_pct.toFixed(2)}%</div>
      `;
    }
  });

  canvas.addEventListener("mouseleave", () => {
    uHoverIndex = null;
    if (DOM.sysChartTooltip) DOM.sysChartTooltip.style.display = "none";
    renderUnifiedSystemsChart();
  });

  window.addEventListener("resize", () => {
    const r = canvas.getBoundingClientRect();
    canvas.width = r.width * dpr;
    canvas.height = r.height * dpr;
    uCtx = canvas.getContext("2d");
    uCtx.scale(dpr, dpr);
    uWidth = r.width;
    uHeight = r.height;
    renderUnifiedSystemsChart();
  });
}

async function fetchSystemsChart(period = "3mo") {
  try {
    const res = await fetch(`/api/systems-chart?period=${period}`);
    const data = await res.json();
    if (!data.success || !data.datapoints) return;

    STATE.systemsChartData = data.datapoints;

    if (data.summary) {
      const s = data.summary;
      if (DOM.ulUnifiedVal) {
        DOM.ulUnifiedVal.textContent = `${s.unified_gain_pct >= 0 ? '+' : ''}${s.unified_gain_pct.toFixed(2)}% (฿${s.latest_portfolio_val_thb.toLocaleString('en-US', {minimumFractionDigits: 2})})`;
        DOM.ulUnifiedVal.className = `ul-val mono ${s.unified_gain_pct >= 0 ? 'positive' : 'negative'}`;
      }
      if (DOM.ulUsVal) {
        DOM.ulUsVal.textContent = `${s.us_gain_pct >= 0 ? '+' : ''}${s.us_gain_pct.toFixed(2)}%`;
        DOM.ulUsVal.className = `ul-val mono ${s.us_gain_pct >= 0 ? 'positive' : 'negative'}`;
      }
      if (DOM.ulGoldVal) {
        DOM.ulGoldVal.textContent = `${s.gold_gain_pct >= 0 ? '+' : ''}${s.gold_gain_pct.toFixed(2)}%`;
        DOM.ulGoldVal.className = `ul-val mono ${s.gold_gain_pct >= 0 ? 'positive' : 'negative'}`;
      }
      if (DOM.ulCryptoVal) {
        DOM.ulCryptoVal.textContent = `${s.crypto_gain_pct >= 0 ? '+' : ''}${s.crypto_gain_pct.toFixed(2)}%`;
        DOM.ulCryptoVal.className = `ul-val mono ${s.crypto_gain_pct >= 0 ? 'positive' : 'negative'}`;
      }
      if (DOM.ulForexVal) {
        DOM.ulForexVal.textContent = `${s.forex_gain_pct >= 0 ? '+' : ''}${s.forex_gain_pct.toFixed(2)}%`;
        DOM.ulForexVal.className = `ul-val mono ${s.forex_gain_pct >= 0 ? 'positive' : 'negative'}`;
      }
    }

    renderUnifiedSystemsChart();
  } catch (err) {
    console.error("Systems chart fetch error", err);
  }
}

function renderUnifiedSystemsChart() {
  const canvas = DOM.unifiedSystemsCanvas;
  if (!canvas || !uCtx || !STATE.systemsChartData || STATE.systemsChartData.length === 0) return;

  const data = STATE.systemsChartData;
  const isVal = STATE.systemsChartMode === "VAL";

  uCtx.clearRect(0, 0, uWidth, uHeight);

  const pad = { top: 25, right: 70, bottom: 25, left: 15 };
  const cW = uWidth - pad.left - pad.right;
  const cH = uHeight - pad.top - pad.bottom;

  let allVals = [];
  data.forEach(d => {
    if (isVal) {
      if (STATE.visibleSystems.unified) allVals.push(d.unified_val);
      if (STATE.visibleSystems.us) allVals.push(100000 * (1 + d.us_pct / 100));
      if (STATE.visibleSystems.gold) allVals.push(90000 * (1 + d.gold_pct / 100));
      if (STATE.visibleSystems.crypto) allVals.push(80000 * (1 + d.crypto_pct / 100));
      if (STATE.visibleSystems.forex) allVals.push(30000 * (1 + d.forex_pct / 100));
    } else {
      if (STATE.visibleSystems.unified) allVals.push(d.unified_pct);
      if (STATE.visibleSystems.us) allVals.push(d.us_pct);
      if (STATE.visibleSystems.gold) allVals.push(d.gold_pct);
      if (STATE.visibleSystems.crypto) allVals.push(d.crypto_pct);
      if (STATE.visibleSystems.forex) allVals.push(d.forex_pct);
    }
  });

  if (allVals.length === 0) allVals = [0, 10];
  let minV = Math.min(...allVals);
  let maxV = Math.max(...allVals);
  const range = (maxV - minV) || 1;
  minV -= range * 0.08;
  maxV += range * 0.08;

  const getY = (v) => pad.top + cH - ((v - minV) / (maxV - minV)) * cH;
  const getX = (i) => pad.left + (i / (data.length - 1)) * cW;

  // Grid Lines
  uCtx.strokeStyle = "rgba(255, 255, 255, 0.05)";
  uCtx.lineWidth = 1;
  for (let i = 0; i <= 4; i++) {
    const y = pad.top + (cH / 4) * i;
    uCtx.beginPath();
    uCtx.moveTo(pad.left, y);
    uCtx.lineTo(uWidth - pad.right, y);
    uCtx.stroke();

    const valLabel = maxV - (i / 4) * (maxV - minV);
    uCtx.fillStyle = "#64748b";
    uCtx.font = "10px 'JetBrains Mono'";
    const txt = isVal ? `฿${Math.round(valLabel).toLocaleString()}` : `${valLabel >= 0 ? '+' : ''}${valLabel.toFixed(1)}%`;
    uCtx.fillText(txt, uWidth - pad.right + 8, y + 3);
  }

  // Zero Line
  if (!isVal && minV < 0 && maxV > 0) {
    const zeroY = getY(0);
    uCtx.strokeStyle = "rgba(255, 255, 255, 0.2)";
    uCtx.setLineDash([4, 4]);
    uCtx.beginPath();
    uCtx.moveTo(pad.left, zeroY);
    uCtx.lineTo(uWidth - pad.right, zeroY);
    uCtx.stroke();
    uCtx.setLineDash([]);
  }

  const drawLine = (valAccessor, strokeStyle, lineWidth, shadowColor, fillArea = false) => {
    uCtx.strokeStyle = strokeStyle;
    uCtx.lineWidth = lineWidth;
    if (shadowColor) {
      uCtx.shadowColor = shadowColor;
      uCtx.shadowBlur = 10;
    } else {
      uCtx.shadowBlur = 0;
    }

    if (fillArea) {
      const grad = uCtx.createLinearGradient(0, pad.top, 0, uHeight);
      grad.addColorStop(0, "rgba(0, 240, 144, 0.25)");
      grad.addColorStop(1, "rgba(0, 240, 144, 0.0)");
      uCtx.beginPath();
      uCtx.moveTo(getX(0), uHeight - pad.bottom);
      data.forEach((d, i) => uCtx.lineTo(getX(i), getY(valAccessor(d))));
      uCtx.lineTo(getX(data.length - 1), uHeight - pad.bottom);
      uCtx.closePath();
      uCtx.fillStyle = grad;
      uCtx.fill();
    }

    uCtx.beginPath();
    data.forEach((d, i) => {
      const y = getY(valAccessor(d));
      if (i === 0) uCtx.moveTo(getX(i), y);
      else uCtx.lineTo(getX(i), y);
    });
    uCtx.stroke();
    uCtx.shadowBlur = 0;
  };

  // Draw 4 Assets & Unified Line
  if (STATE.visibleSystems.forex) {
    drawLine(d => isVal ? 30000 * (1 + d.forex_pct / 100) : d.forex_pct, "#ff3b69", 1.8, null);
  }
  if (STATE.visibleSystems.crypto) {
    drawLine(d => isVal ? 80000 * (1 + d.crypto_pct / 100) : d.crypto_pct, "#9d4edd", 1.8, null);
  }
  if (STATE.visibleSystems.gold) {
    drawLine(d => isVal ? 90000 * (1 + d.gold_pct / 100) : d.gold_pct, "#ffb703", 1.8, null);
  }
  if (STATE.visibleSystems.us) {
    drawLine(d => isVal ? 100000 * (1 + d.us_pct / 100) : d.us_pct, "#00c8ff", 1.8, null);
  }
  if (STATE.visibleSystems.unified) {
    drawLine(d => isVal ? d.unified_val : d.unified_pct, "#00f090", 2.8, "rgba(0, 240, 144, 0.4)", true);
  }

  // Crosshair
  if (uHoverIndex !== null && data[uHoverIndex]) {
    const x = getX(uHoverIndex);
    uCtx.strokeStyle = "rgba(255, 255, 255, 0.4)";
    uCtx.lineWidth = 1;
    uCtx.setLineDash([3, 3]);
    uCtx.beginPath();
    uCtx.moveTo(x, pad.top);
    uCtx.lineTo(x, uHeight - pad.bottom);
    uCtx.stroke();
    uCtx.setLineDash([]);

    const drawDot = (v, color) => {
      const y = getY(v);
      uCtx.fillStyle = color;
      uCtx.beginPath();
      uCtx.arc(x, y, 4, 0, Math.PI * 2);
      uCtx.fill();
    };

    const cur = data[uHoverIndex];
    if (STATE.visibleSystems.forex) drawDot(isVal ? 30000 * (1 + cur.forex_pct / 100) : cur.forex_pct, "#ff3b69");
    if (STATE.visibleSystems.crypto) drawDot(isVal ? 80000 * (1 + cur.crypto_pct / 100) : cur.crypto_pct, "#9d4edd");
    if (STATE.visibleSystems.gold) drawDot(isVal ? 90000 * (1 + cur.gold_pct / 100) : cur.gold_pct, "#ffb703");
    if (STATE.visibleSystems.us) drawDot(isVal ? 100000 * (1 + cur.us_pct / 100) : cur.us_pct, "#00c8ff");
    if (STATE.visibleSystems.unified) drawDot(isVal ? cur.unified_val : cur.unified_pct, "#00f090");
  }
}

