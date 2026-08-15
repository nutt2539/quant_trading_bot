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
  scalper: {
    activeAssetClass: "CRYPTO",
    activeSymbol: "BTC-USD",
    activeTf: "5m",
    activeSide: "LONG",
    leverage: 5,
    margin: 2000,
    tpPct: 1.5,
    slPct: 0.8,
    chartData: [],
    status: null,
    signals: []
  },
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

  // Scalper Pro
  scalpAutoToggle: document.getElementById("scalp-auto-toggle"),
  btnPanicScalpAll: document.getElementById("btn-panic-scalp-all"),
  scalpCryptoReturn: document.getElementById("scalp-crypto-return"),
  scalpCryptoBalance: document.getElementById("scalp-crypto-balance"),
  scalpCryptoMargin: document.getElementById("scalp-crypto-margin"),
  scalpCryptoFloat: document.getElementById("scalp-crypto-float"),
  scalpCryptoEquity: document.getElementById("scalp-crypto-equity"),
  scalpForexReturn: document.getElementById("scalp-forex-return"),
  scalpForexBalance: document.getElementById("scalp-forex-balance"),
  scalpForexMargin: document.getElementById("scalp-forex-margin"),
  scalpForexFloat: document.getElementById("scalp-forex-float"),
  scalpForexEquity: document.getElementById("scalp-forex-equity"),
  scalpTotalFloat: document.getElementById("scalp-total-float"),
  scalpTotalRealized: document.getElementById("scalp-total-realized"),
  scalpWinRate: document.getElementById("scalp-win-rate"),
  scalpTotalEquity: document.getElementById("scalp-total-equity"),
  scalpActiveTicketsBadge: document.getElementById("scalp-active-tickets-badge"),
  scalpChartCanvas: document.getElementById("scalper-chart-canvas"),
  scalpChartTooltip: document.getElementById("scalper-chart-tooltip"),
  scalpChartTitle: document.getElementById("scalp-chart-title"),
  scalpChartPrice: document.getElementById("scalp-chart-price"),
  scalpSpreadTag: document.getElementById("scalp-spread-tag"),
  scalpSymbolBtns: document.getElementById("scalp-symbol-btns"),
  scalpTfBtns: document.getElementById("scalp-tf-btns"),
  scalpSignalsContainer: document.getElementById("scalp-signals-container"),
  btnRefreshScalpSignals: document.getElementById("btn-refresh-scalp-signals"),
  tabScalpCrypto: document.getElementById("tab-scalp-crypto"),
  tabScalpForex: document.getElementById("tab-scalp-forex"),
  scalpOrderSymbol: document.getElementById("scalp-order-symbol"),
  btnSideLong: document.getElementById("btn-side-long"),
  btnSideShort: document.getElementById("btn-side-short"),
  scalpLeverageDisplay: document.getElementById("scalp-leverage-display"),
  scalpLeveragePills: document.getElementById("scalp-leverage-pills"),
  scalpMarginInput: document.getElementById("scalp-margin-input"),
  scalpMaxAvailText: document.getElementById("scalp-max-avail-text"),
  scalpPctPills: document.getElementById("scalp-pct-pills"),
  scalpEffectiveSize: document.getElementById("scalp-effective-size"),
  scalpEstEntry: document.getElementById("scalp-est-entry"),
  scalpTpInput: document.getElementById("scalp-tp-input"),
  scalpSlInput: document.getElementById("scalp-sl-input"),
  scalpTpPriceHint: document.getElementById("scalp-tp-price-hint"),
  scalpSlPriceHint: document.getElementById("scalp-sl-price-hint"),
  btnExecuteScalpOrder: document.getElementById("btn-execute-scalp-order"),
  scalpPositionsTbody: document.getElementById("scalp-positions-tbody"),
  scalpOpenCountBadge: document.getElementById("scalp-open-count-badge"),
  scalpHistoryTbody: document.getElementById("scalp-history-tbody"),

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
  setupScalperEventListeners();
  initCanvas();
  initUnifiedCanvas();
  initScalperCanvas();
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
      if (targetId === "view-scalper") {
        fetchScalperStatus();
        fetchScalperChart(STATE.scalper.activeSymbol, STATE.scalper.activeTf);
        fetchScalperSignals();
      }
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
  fetchScalperStatus();

  STATE.pollingTimer = setInterval(() => {
    fetchStatus();
    fetchTickers();
    fetchPositions();
    fetchHarvester();
    fetchScalperStatus();
  }, 3500);
}

async function fetchInitialData() {
  await fetchStatus();
  await fetchTickers();
  await fetchStrategies();
  await fetchMarketChart(STATE.activeSymbol, STATE.activePeriod);
  await fetchSystemsChart(STATE.systemsChartPeriod);
  await fetchScalperStatus();
  await fetchScalperSignals();
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
  const systemMeta = {
    "US_INDEX": { icon: "🇺🇸", title: "US Index (฿100k)" },
    "GOLD": { icon: "🥇", title: "Gold Bot (฿90k)" },
    "CRYPTO": { icon: "🪙", title: "Crypto Bot (฿80k)" },
    "FOREX": { icon: "💱", title: "Forex Bot (฿30k)" }
  };

  for (const [key, sys] of Object.entries(systems)) {
    const meta = systemMeta[key] || { icon: "⚡", title: sys.name };
    const pnlSign = sys.net_pnl_thb >= 0 ? '+' : '';
    const pnlClass = sys.net_pnl_thb >= 0 ? 'positive' : 'negative';
    const tagClass = sys.net_pnl_pct >= 0 ? 'buy' : 'sell';

    let card = DOM.systemsCardsGrid.querySelector(`.system-card[data-sys-key="${key}"]`);
    if (!card) {
      card = document.createElement("div");
      card.className = "system-card";
      card.setAttribute("data-sys-key", key);

      card.innerHTML = `
        <div class="sys-card-header">
          <div class="sys-title-group">
            <h3>${meta.icon} ${meta.title}</h3>
            <div style="display:flex; align-items:center; gap:6px; margin-top:2px;">
              <span class="sys-alloc-badge" id="sys-alloc-${key}">Alloc: ฿${sys.allocation_thb.toLocaleString()} (฿${sys.portfolio_val_thb.toLocaleString()})</span>
              <span class="status-pill-small ${sys.is_market_open ? 'open' : 'closed'}" id="sys-mkt-${key}">${sys.market_status_label || (sys.is_market_open ? '🟢 ตลาดเปิด' : '🔴 ปิดวันหยุด')}</span>
            </div>
          </div>
          <span class="signal-tag ${tagClass}" id="sys-tag-${key}">${pnlSign}${sys.net_pnl_pct.toFixed(2)}%</span>
        </div>

        <div class="sys-pnl-banner">
          <div>
            <span class="metric-label">กำไรสุทธิ (P&L)</span>
            <div class="sys-pnl-val mono ${pnlClass}" id="sys-pnl-${key}">${pnlSign}฿${sys.net_pnl_thb.toLocaleString('en-US', { minimumFractionDigits: 2 })}</div>
          </div>
          <div style="text-align: right;">
            <span class="metric-label">Win Rate</span>
            <div class="mono" id="sys-win-${key}" style="font-weight: 700; font-size: 13px;">${sys.win_rate_pct.toFixed(1)}%</div>
          </div>
        </div>

        <div class="sys-stats-row">
          <div class="stat-item"><span>สะสม TP:</span> <strong class="positive" id="sys-tp-${key}">+฿${sys.cumulative_take_profit_thb.toLocaleString()}</strong></div>
          <div class="stat-item"><span>สะสม Cut:</span> <strong class="negative" id="sys-cut-${key}">-฿${sys.cumulative_cut_loss_thb.toLocaleString()}</strong></div>
          <div class="stat-item"><span>ปิดแล้ว:</span> <strong id="sys-closed-${key}">${sys.closed_trades_count} ไม้</strong></div>
          <div class="stat-item"><span>ถือครอง:</span> <strong id="sys-holdings-${key}">${sys.active_holdings_count} ไม้</strong></div>
        </div>

        <div class="sys-strategy-selector">
          <label>Active Strategy (${key}):</label>
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
    } else {
      // Dynamic in-place updates on every poll tick
      const elAlloc = document.getElementById(`sys-alloc-${key}`);
      const elMkt = document.getElementById(`sys-mkt-${key}`);
      const elTag = document.getElementById(`sys-tag-${key}`);
      const elPnl = document.getElementById(`sys-pnl-${key}`);
      const elWin = document.getElementById(`sys-win-${key}`);
      const elTp = document.getElementById(`sys-tp-${key}`);
      const elCut = document.getElementById(`sys-cut-${key}`);
      const elClosed = document.getElementById(`sys-closed-${key}`);
      const elHoldings = document.getElementById(`sys-holdings-${key}`);
      const elDropdown = card.querySelector(".sys-strat-dropdown");

      if (elAlloc) elAlloc.textContent = `Alloc: ฿${sys.allocation_thb.toLocaleString()} (฿${sys.portfolio_val_thb.toLocaleString()})`;
      if (elMkt) {
        elMkt.textContent = sys.market_status_label || (sys.is_market_open ? '🟢 ตลาดเปิด' : '🔴 ปิดวันหยุด');
        elMkt.className = `status-pill-small ${sys.is_market_open ? 'open' : 'closed'}`;
      }
      if (elTag) {
        elTag.textContent = `${pnlSign}${sys.net_pnl_pct.toFixed(2)}%`;
        elTag.className = `signal-tag ${tagClass}`;
      }
      if (elPnl) {
        elPnl.textContent = `${pnlSign}฿${sys.net_pnl_thb.toLocaleString('en-US', { minimumFractionDigits: 2 })}`;
        elPnl.className = `sys-pnl-val mono ${pnlClass}`;
      }
      if (elWin) elWin.textContent = `${sys.win_rate_pct.toFixed(1)}%`;
      if (elTp) elTp.textContent = `+฿${sys.cumulative_take_profit_thb.toLocaleString()}`;
      if (elCut) elCut.textContent = `-฿${sys.cumulative_cut_loss_thb.toLocaleString()}`;
      if (elClosed) elClosed.textContent = `${sys.closed_trades_count} ไม้`;
      if (elHoldings) elHoldings.textContent = `${sys.active_holdings_count} ไม้`;
      if (elDropdown && document.activeElement !== elDropdown) {
        elDropdown.value = sys.active_strategy;
      }
    }
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

// ==========================================================================
// SCALPER PRO (SHORT / LONG) CONTROLLER & ENGINE
// ==========================================================================

let scalpCtx, scalpWidth, scalpHeight;

function setupScalperEventListeners() {
  // 1. Asset Class Switcher (Crypto vs Forex)
  if (DOM.tabScalpCrypto && DOM.tabScalpForex) {
    DOM.tabScalpCrypto.addEventListener("click", () => switchScalpAssetClass("CRYPTO"));
    DOM.tabScalpForex.addEventListener("click", () => switchScalpAssetClass("FOREX"));
  }

  // 2. Order Symbol Change
  if (DOM.scalpOrderSymbol) {
    DOM.scalpOrderSymbol.addEventListener("change", (e) => {
      STATE.scalper.activeSymbol = e.target.value;
      updateScalpSymbolButtons(STATE.scalper.activeSymbol);
      fetchScalperChart(STATE.scalper.activeSymbol, STATE.scalper.activeTf);
      updateScalpOrderFormCalculations();
    });
  }

  // 3. Chart Symbol Quick Buttons
  if (DOM.scalpSymbolBtns) {
    DOM.scalpSymbolBtns.querySelectorAll("button").forEach(btn => {
      btn.addEventListener("click", () => {
        const sym = btn.getAttribute("data-sym");
        STATE.scalper.activeSymbol = sym;
        
        // Auto detect asset class
        const isForex = sym.includes("=") || sym.includes("EUR") || sym.includes("GBP") || sym.includes("JPY");
        const targetAsset = isForex ? "FOREX" : "CRYPTO";
        if (targetAsset !== STATE.scalper.activeAssetClass) {
          switchScalpAssetClass(targetAsset, sym);
        } else {
          if (DOM.scalpOrderSymbol) DOM.scalpOrderSymbol.value = sym;
          updateScalpSymbolButtons(sym);
          fetchScalperChart(sym, STATE.scalper.activeTf);
          updateScalpOrderFormCalculations();
        }
      });
    });
  }

  // 4. Chart Timeframe Quick Buttons (1M, 5M, 15M)
  if (DOM.scalpTfBtns) {
    DOM.scalpTfBtns.querySelectorAll("button").forEach(btn => {
      btn.addEventListener("click", () => {
        DOM.scalpTfBtns.querySelectorAll("button").forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        STATE.scalper.activeTf = btn.getAttribute("data-tf");
        fetchScalperChart(STATE.scalper.activeSymbol, STATE.scalper.activeTf);
      });
    });
  }

  // 5. Order Side Buttons (LONG vs SHORT)
  if (DOM.btnSideLong && DOM.btnSideShort) {
    DOM.btnSideLong.addEventListener("click", () => setScalpOrderSide("LONG"));
    DOM.btnSideShort.addEventListener("click", () => setScalpOrderSide("SHORT"));
  }

  // 6. Leverage Pills (1X, 2X, 5X, 10X, 20X)
  if (DOM.scalpLeveragePills) {
    DOM.scalpLeveragePills.querySelectorAll("button").forEach(btn => {
      btn.addEventListener("click", () => {
        DOM.scalpLeveragePills.querySelectorAll("button").forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        STATE.scalper.leverage = parseFloat(btn.getAttribute("data-lev")) || 5;
        if (DOM.scalpLeverageDisplay) DOM.scalpLeverageDisplay.textContent = `${STATE.scalper.leverage}X`;
        updateScalpOrderFormCalculations();
      });
    });
  }

  // 7. Margin Input & Percentage Pills
  if (DOM.scalpMarginInput) {
    DOM.scalpMarginInput.addEventListener("input", () => {
      STATE.scalper.margin = parseFloat(DOM.scalpMarginInput.value) || 1000;
      updateScalpOrderFormCalculations();
    });
  }

  if (DOM.scalpPctPills) {
    DOM.scalpPctPills.querySelectorAll("button").forEach(btn => {
      btn.addEventListener("click", () => {
        const pct = parseFloat(btn.getAttribute("data-pct")) || 25;
        const bal = getScalpAvailableBalance(STATE.scalper.activeAssetClass);
        const calcMargin = Math.max(100, Math.floor((bal * (pct / 100)) / 100) * 100);
        STATE.scalper.margin = calcMargin;
        if (DOM.scalpMarginInput) DOM.scalpMarginInput.value = calcMargin;
        updateScalpOrderFormCalculations();
      });
    });
  }

  // 8. TP & SL Input Changes
  if (DOM.scalpTpInput) {
    DOM.scalpTpInput.addEventListener("input", () => {
      STATE.scalper.tpPct = parseFloat(DOM.scalpTpInput.value) || 1.5;
      updateScalpOrderFormCalculations();
    });
  }
  if (DOM.scalpSlInput) {
    DOM.scalpSlInput.addEventListener("input", () => {
      STATE.scalper.slPct = parseFloat(DOM.scalpSlInput.value) || 0.8;
      updateScalpOrderFormCalculations();
    });
  }

  // 9. Execute Order Button
  if (DOM.btnExecuteScalpOrder) {
    DOM.btnExecuteScalpOrder.addEventListener("click", executeScalperOrder);
  }

  // 10. Auto-Scalper Master Toggle
  if (DOM.scalpAutoToggle) {
    DOM.scalpAutoToggle.addEventListener("change", async (e) => {
      const enabled = e.target.checked;
      try {
        const res = await fetch("/api/scalper/toggle-auto", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ enabled })
        });
        const data = await res.json();
        showToast(data.message, "info");
        fetchScalperStatus();
      } catch (err) {
        showToast("Auto-scalp toggle failed", "error");
      }
    });
  }

  // 11. Panic Close All Scalps
  if (DOM.btnPanicScalpAll) {
    DOM.btnPanicScalpAll.addEventListener("click", closeAllScalperPositions);
  }

  // 12. Refresh AI Signals
  if (DOM.btnRefreshScalpSignals) {
    DOM.btnRefreshScalpSignals.addEventListener("click", () => {
      DOM.btnRefreshScalpSignals.textContent = "⏳ Scanning...";
      fetchScalperSignals().then(() => {
        DOM.btnRefreshScalpSignals.innerHTML = "<span>🔄 สแกนใหม่</span>";
        showToast("สแกนสัญญาณ Scalping ล่าสุดเรียบร้อย!", "success");
      });
    });
  }
}

function getScalpAvailableBalance(assetClass) {
  if (!STATE.scalper.status || !STATE.scalper.status.capital_summary) return 20000.0;
  const key = assetClass.toLowerCase();
  return STATE.scalper.status.capital_summary[key]?.balance_thb || 20000.0;
}

function switchScalpAssetClass(assetClass, specificSymbol = null) {
  STATE.scalper.activeAssetClass = assetClass;

  if (DOM.tabScalpCrypto) DOM.tabScalpCrypto.classList.toggle("active", assetClass === "CRYPTO");
  if (DOM.tabScalpForex) DOM.tabScalpForex.classList.toggle("active", assetClass === "FOREX");

  // Re-populate symbol selectbox
  if (DOM.scalpOrderSymbol) {
    DOM.scalpOrderSymbol.innerHTML = "";
    if (assetClass === "CRYPTO") {
      DOM.scalpOrderSymbol.innerHTML = `
        <option value="BTC-USD">🪙 BTC-USD (Bitcoin)</option>
        <option value="ETH-USD">💎 ETH-USD (Ethereum)</option>
        <option value="SOL-USD">⚡ SOL-USD (Solana)</option>
      `;
      STATE.scalper.activeSymbol = specificSymbol || "BTC-USD";
    } else {
      DOM.scalpOrderSymbol.innerHTML = `
        <option value="EURUSD=X">💶 EUR/USD (Euro / US Dollar)</option>
        <option value="GBPUSD=X">💷 GBP/USD (British Pound)</option>
        <option value="USDJPY=X">💴 USD/JPY (US Dollar / Yen)</option>
      `;
      STATE.scalper.activeSymbol = specificSymbol || "EURUSD=X";
    }
    DOM.scalpOrderSymbol.value = STATE.scalper.activeSymbol;
  }

  updateScalpSymbolButtons(STATE.scalper.activeSymbol);
  fetchScalperChart(STATE.scalper.activeSymbol, STATE.scalper.activeTf);
  updateScalpOrderFormCalculations();
}

function updateScalpSymbolButtons(symbol) {
  if (!DOM.scalpSymbolBtns) return;
  DOM.scalpSymbolBtns.querySelectorAll("button").forEach(btn => {
    btn.classList.toggle("active", btn.getAttribute("data-sym") === symbol);
  });
}

function setScalpOrderSide(side) {
  STATE.scalper.activeSide = side;
  if (DOM.btnSideLong) DOM.btnSideLong.classList.toggle("active", side === "LONG");
  if (DOM.btnSideShort) DOM.btnSideShort.classList.toggle("active", side === "SHORT");

  if (DOM.btnExecuteScalpOrder) {
    DOM.btnExecuteScalpOrder.className = `btn-execute-scalp ${side.toLowerCase()}`;
  }
  updateScalpOrderFormCalculations();
}

function updateScalpOrderFormCalculations() {
  const margin = parseFloat(DOM.scalpMarginInput ? DOM.scalpMarginInput.value : 2000) || 2000;
  const leverage = STATE.scalper.leverage || 5;
  const side = STATE.scalper.activeSide || "LONG";
  const tpPct = parseFloat(DOM.scalpTpInput ? DOM.scalpTpInput.value : 1.5) || 1.5;
  const slPct = parseFloat(DOM.scalpSlInput ? DOM.scalpSlInput.value : 0.8) || 0.8;

  const effectiveSize = margin * leverage;
  if (DOM.scalpEffectiveSize) {
    DOM.scalpEffectiveSize.textContent = `฿${effectiveSize.toLocaleString('en-US', { minimumFractionDigits: 2 })}`;
  }

  const avail = getScalpAvailableBalance(STATE.scalper.activeAssetClass);
  if (DOM.scalpMaxAvailText) {
    DOM.scalpMaxAvailText.textContent = `คงเหลือ: ฿${avail.toLocaleString('en-US', { minimumFractionDigits: 2 })}`;
  }

  let currPrice = 0.0;
  if (STATE.scalper.chartData && STATE.scalper.chartData.length > 0) {
    currPrice = STATE.scalper.chartData[STATE.scalper.chartData.length - 1].close;
  }
  if (currPrice > 0) {
    if (DOM.scalpEstEntry) DOM.scalpEstEntry.textContent = `$${currPrice.toLocaleString('en-US', { minimumFractionDigits: currPrice < 10 ? 4 : 2 })}`;
    
    const tpDelta = currPrice * (tpPct / 100);
    const slDelta = currPrice * (slPct / 100);
    const tpPrice = side === "LONG" ? (currPrice + tpDelta) : (currPrice - tpDelta);
    const slPrice = side === "LONG" ? (currPrice - slDelta) : (currPrice + slDelta);

    const decimals = currPrice < 10 ? 4 : 2;
    if (DOM.scalpTpPriceHint) DOM.scalpTpPriceHint.textContent = `TP Price: $${tpPrice.toFixed(decimals)}`;
    if (DOM.scalpSlPriceHint) DOM.scalpSlPriceHint.textContent = `SL Price: $${slPrice.toFixed(decimals)}`;
  }

  if (DOM.btnExecuteScalpOrder) {
    DOM.btnExecuteScalpOrder.innerHTML = `<span>⚡ เปิดไม้ ${side} ทันที (฿${margin.toLocaleString()} x ${leverage}X)</span>`;
  }
}

// ----------------- SCALPER DATA FETCHERS & RENDERERS -----------------

async function fetchScalperStatus() {
  try {
    const res = await fetch("/api/scalper/status");
    const data = await res.json();
    if (!data.success) return;

    STATE.scalper.status = data;

    // HUD: Crypto Bucket
    const c = data.capital_summary.crypto;
    if (DOM.scalpCryptoReturn) {
      DOM.scalpCryptoReturn.textContent = `${c.return_pct >= 0 ? '+' : ''}${c.return_pct.toFixed(2)}%`;
      DOM.scalpCryptoReturn.className = `s-bucket-badge ${c.return_pct >= 0 ? 'positive' : 'negative'}`;
    }
    if (DOM.scalpCryptoBalance) DOM.scalpCryptoBalance.textContent = `฿${c.balance_thb.toLocaleString('en-US', { minimumFractionDigits: 2 })}`;
    if (DOM.scalpCryptoMargin) DOM.scalpCryptoMargin.textContent = `฿${c.margin_used_thb.toLocaleString('en-US', { minimumFractionDigits: 2 })}`;
    if (DOM.scalpCryptoFloat) {
      DOM.scalpCryptoFloat.textContent = `${c.floating_pnl_thb >= 0 ? '+' : ''}฿${c.floating_pnl_thb.toLocaleString('en-US', { minimumFractionDigits: 2 })}`;
      DOM.scalpCryptoFloat.className = `mono ${c.floating_pnl_thb >= 0 ? 'positive' : 'negative'}`;
    }
    if (DOM.scalpCryptoEquity) DOM.scalpCryptoEquity.textContent = `฿${c.equity_thb.toLocaleString('en-US', { minimumFractionDigits: 2 })}`;

    // HUD: Forex Bucket
    const f = data.capital_summary.forex;
    if (DOM.scalpForexReturn) {
      DOM.scalpForexReturn.textContent = `${f.return_pct >= 0 ? '+' : ''}${f.return_pct.toFixed(2)}%`;
      DOM.scalpForexReturn.className = `s-bucket-badge ${f.return_pct >= 0 ? 'positive' : 'negative'}`;
    }
    if (DOM.scalpForexBalance) DOM.scalpForexBalance.textContent = `฿${f.balance_thb.toLocaleString('en-US', { minimumFractionDigits: 2 })}`;
    if (DOM.scalpForexMargin) DOM.scalpForexMargin.textContent = `฿${f.margin_used_thb.toLocaleString('en-US', { minimumFractionDigits: 2 })}`;
    if (DOM.scalpForexFloat) {
      DOM.scalpForexFloat.textContent = `${f.floating_pnl_thb >= 0 ? '+' : ''}฿${f.floating_pnl_thb.toLocaleString('en-US', { minimumFractionDigits: 2 })}`;
      DOM.scalpForexFloat.className = `mono ${f.floating_pnl_thb >= 0 ? 'positive' : 'negative'}`;
    }
    if (DOM.scalpForexEquity) DOM.scalpForexEquity.textContent = `฿${f.equity_thb.toLocaleString('en-US', { minimumFractionDigits: 2 })}`;

    // HUD: Total Bucket
    const sum = data.capital_summary;
    if (DOM.scalpTotalFloat) {
      DOM.scalpTotalFloat.textContent = `${sum.total_floating_pnl_thb >= 0 ? '+' : ''}฿${sum.total_floating_pnl_thb.toLocaleString('en-US', { minimumFractionDigits: 2 })}`;
      DOM.scalpTotalFloat.className = `mono ${sum.total_floating_pnl_thb >= 0 ? 'positive' : 'negative'}`;
    }
    if (DOM.scalpTotalRealized) {
      DOM.scalpTotalRealized.textContent = `${sum.total_realized_pnl_thb >= 0 ? '+' : ''}฿${sum.total_realized_pnl_thb.toLocaleString('en-US', { minimumFractionDigits: 2 })}`;
      DOM.scalpTotalRealized.className = `mono ${sum.total_realized_pnl_thb >= 0 ? 'positive' : 'negative'}`;
    }
    if (DOM.scalpWinRate) DOM.scalpWinRate.textContent = `${sum.win_rate_pct.toFixed(1)}% (${sum.total_closed_trades} ไม้)`;
    if (DOM.scalpTotalEquity) DOM.scalpTotalEquity.textContent = `฿${sum.total_equity_thb.toLocaleString('en-US', { minimumFractionDigits: 2 })}`;
    if (DOM.scalpActiveTicketsBadge) DOM.scalpActiveTicketsBadge.textContent = `${data.active_tickets_count} ตั๋วเปิดอยู่`;
    if (DOM.scalpOpenCountBadge) DOM.scalpOpenCountBadge.textContent = `${data.active_tickets_count} Active Tickets`;

    renderScalperPositions(data.open_positions);
    renderScalperHistory(data.closed_positions);
    updateScalpOrderFormCalculations();
  } catch (err) {
    console.error("Scalper status fetch error", err);
  }
}

function renderScalperPositions(positions) {
  if (!DOM.scalpPositionsTbody) return;
  DOM.scalpPositionsTbody.innerHTML = "";

  if (!positions || positions.length === 0) {
    DOM.scalpPositionsTbody.innerHTML = `<tr><td colspan="11" class="text-center" style="color:var(--text-muted); padding:20px;">ไม่มีตั๋วเทรดที่กำลังเปิดอยู่ — ส่งคำสั่ง Short/Long หรือเปิดใช้งาน AI Auto-Scalper</td></tr>`;
    return;
  }

  positions.forEach(p => {
    const tr = document.createElement("tr");
    const isLong = p.side === "LONG";
    const pnlSign = p.floating_pnl_thb >= 0 ? '+' : '';
    const pnlClass = p.floating_pnl_thb >= 0 ? 'positive' : 'negative';
    const dec = p.entry_price < 10 ? 4 : 2;

    tr.innerHTML = `
      <td class="mono font-bold" style="color:#f8fafc;">${p.id}</td>
      <td>${p.icon || '⚡'} <strong>${p.name}</strong> <span style="font-size:10px; color:var(--text-muted);">(${p.symbol})</span></td>
      <td><span class="sig-side-badge ${isLong ? 'long' : 'short'}">${isLong ? '🟢 LONG' : '🔴 SHORT'}</span></td>
      <td class="mono">$${p.entry_price.toFixed(dec)}</td>
      <td class="mono font-bold">$${(p.current_price || p.entry_price).toFixed(dec)}</td>
      <td><span class="mono" style="background:rgba(255,255,255,0.08); padding:2px 6px; border-radius:4px; font-weight:700;">${p.leverage}X</span></td>
      <td class="mono">฿${p.margin_thb.toLocaleString('en-US', { minimumFractionDigits: 2 })}</td>
      <td class="mono font-bold ${pnlClass}">${pnlSign}฿${p.floating_pnl_thb.toLocaleString('en-US', { minimumFractionDigits: 2 })} (${pnlSign}${p.floating_pnl_pct.toFixed(2)}%)</td>
      <td class="mono" style="font-size:11px;">
        <span style="color:#00f090;">TP: ${p.tp_price ? '$' + p.tp_price.toFixed(dec) : '-'}</span><br>
        <span style="color:#ff3b69;">SL: ${p.sl_price ? '$' + p.sl_price.toFixed(dec) : '-'}</span>
      </td>
      <td style="font-size:11px; color:var(--text-muted);">${p.open_time}</td>
      <td>
        <button class="btn-scalp-action close-ticket" onclick="closeScalperTicket('${p.id}')">
          <span>❌ ปิดไม้</span>
        </button>
      </td>
    `;
    DOM.scalpPositionsTbody.appendChild(tr);
  });
}

function renderScalperHistory(history) {
  if (!DOM.scalpHistoryTbody) return;
  DOM.scalpHistoryTbody.innerHTML = "";

  if (!history || history.length === 0) {
    DOM.scalpHistoryTbody.innerHTML = `<tr><td colspan="9" class="text-center" style="color:var(--text-muted); padding:16px;">ยังไม่มีประวัติการปิดไม้</td></tr>`;
    return;
  }

  history.forEach(h => {
    const tr = document.createElement("tr");
    const isLong = h.side === "LONG";
    const pnlSign = h.realized_pnl_thb >= 0 ? '+' : '';
    const pnlClass = h.realized_pnl_thb >= 0 ? 'positive' : 'negative';
    const dec = h.entry_price < 10 ? 4 : 2;

    tr.innerHTML = `
      <td class="mono font-bold">${h.id}</td>
      <td>${h.icon || '⚡'} ${h.name}</td>
      <td><span class="sig-side-badge ${isLong ? 'long' : 'short'}">${isLong ? '🟢 LONG' : '🔴 SHORT'}</span></td>
      <td class="mono">$${h.entry_price.toFixed(dec)} ➔ $${(h.close_price || h.entry_price).toFixed(dec)}</td>
      <td class="mono">฿${h.margin_thb.toLocaleString('en-US', { minimumFractionDigits: 2 })}</td>
      <td class="mono font-bold ${pnlClass}">${pnlSign}฿${h.realized_pnl_thb.toLocaleString('en-US', { minimumFractionDigits: 2 })}</td>
      <td class="mono font-bold ${pnlClass}">${pnlSign}${h.realized_pnl_pct.toFixed(2)}%</td>
      <td><span style="font-size:10px; padding:2px 6px; border-radius:4px; background:rgba(255,255,255,0.06);">${h.close_reason || 'MANUAL'}</span></td>
      <td style="font-size:11px; color:var(--text-muted);">${h.close_time || '-'}</td>
    `;
    DOM.scalpHistoryTbody.appendChild(tr);
  });
}

async function fetchScalperChart(symbol, tf = "5m") {
  try {
    const period = tf === "1m" ? "1d" : tf === "5m" ? "2d" : "5d";
    const res = await fetch(`/api/market-chart?symbol=${symbol}&period=${period}&interval=${tf}`);
    const data = await res.json();
    if (!data.success || !data.candles) return;

    STATE.scalper.chartData = data.candles;
    
    if (DOM.scalpChartTitle) {
      const symInfo = symbol.includes("BTC") ? "🪙 BTC-USD (Bitcoin)" :
                      symbol.includes("ETH") ? "💎 ETH-USD (Ethereum)" :
                      symbol.includes("SOL") ? "⚡ SOL-USD (Solana)" :
                      symbol.includes("EUR") ? "💶 EUR/USD (Forex)" :
                      symbol.includes("GBP") ? "💷 GBP/USD (Forex)" : "💴 USD/JPY (Forex)";
      DOM.scalpChartTitle.textContent = `${symInfo} — ${tf.toUpperCase()} Scalp Station`;
    }

    if (DOM.scalpChartPrice && data.candles.length > 0) {
      const latestC = data.candles[data.candles.length - 1].close;
      const dec = latestC < 10 ? 4 : 2;
      DOM.scalpChartPrice.textContent = `$${latestC.toLocaleString('en-US', { minimumFractionDigits: dec })}`;
    }

    renderScalperChart();
    updateScalpOrderFormCalculations();
  } catch (err) {
    console.error("Scalper chart fetch error", err);
  }
}

function initScalperCanvas() {
  const canvas = DOM.scalpChartCanvas;
  if (!canvas) return;

  const dpr = window.devicePixelRatio || 1;
  const rect = canvas.getBoundingClientRect();
  canvas.width = rect.width * dpr;
  canvas.height = rect.height * dpr;
  scalpCtx = canvas.getContext("2d");
  scalpCtx.scale(dpr, dpr);
  scalpWidth = rect.width;
  scalpHeight = rect.height;

  window.addEventListener("resize", () => {
    const r = canvas.getBoundingClientRect();
    canvas.width = r.width * dpr;
    canvas.height = r.height * dpr;
    scalpCtx = canvas.getContext("2d");
    scalpCtx.scale(dpr, dpr);
    scalpWidth = r.width;
    scalpHeight = r.height;
    renderScalperChart();
  });
}

function renderScalperChart() {
  const canvas = DOM.scalpChartCanvas;
  if (!canvas || !scalpCtx || !STATE.scalper.chartData || STATE.scalper.chartData.length === 0) return;

  const candles = STATE.scalper.chartData;
  scalpCtx.clearRect(0, 0, scalpWidth, scalpHeight);

  const pad = { top: 20, right: 65, bottom: 25, left: 10 };
  const cW = scalpWidth - pad.left - pad.right;
  const cH = scalpHeight - pad.top - pad.bottom;

  let minP = Math.min(...candles.map(c => c.low));
  let maxP = Math.max(...candles.map(c => c.high));
  const range = (maxP - minP) || 1;
  minP -= range * 0.05;
  maxP += range * 0.05;

  const getY = (p) => pad.top + cH - ((p - minP) / (maxP - minP)) * cH;
  const candleW = Math.max(2, (cW / candles.length) * 0.7);

  // 1. Horizontal Grid lines
  scalpCtx.strokeStyle = "rgba(255, 255, 255, 0.05)";
  scalpCtx.lineWidth = 1;
  for (let i = 0; i <= 4; i++) {
    const y = pad.top + (cH / 4) * i;
    scalpCtx.beginPath();
    scalpCtx.moveTo(pad.left, y);
    scalpCtx.lineTo(scalpWidth - pad.right, y);
    scalpCtx.stroke();

    const priceLabel = maxP - (i / 4) * (maxP - minP);
    scalpCtx.fillStyle = "#64748b";
    scalpCtx.font = "10px 'JetBrains Mono'";
    const dec = priceLabel < 10 ? 4 : 2;
    scalpCtx.fillText(`$${priceLabel.toFixed(dec)}`, scalpWidth - pad.right + 6, y + 3);
  }

  // 2. Candlesticks
  candles.forEach((c, i) => {
    const x = pad.left + (i / (candles.length - 1 || 1)) * cW;
    const yO = getY(c.open);
    const yC = getY(c.close);
    const yH = getY(c.high);
    const yL = getY(c.low);

    const isBull = c.close >= c.open;
    scalpCtx.strokeStyle = isBull ? "#00f090" : "#ff3b69";
    scalpCtx.fillStyle = isBull ? "#00f090" : "#ff3b69";

    // Wick
    scalpCtx.lineWidth = 1.2;
    scalpCtx.beginPath();
    scalpCtx.moveTo(x, yH);
    scalpCtx.lineTo(x, yL);
    scalpCtx.stroke();

    // Body
    const topY = Math.min(yO, yC);
    const bodyH = Math.max(2, Math.abs(yC - yO));
    scalpCtx.fillRect(x - candleW / 2, topY, candleW, bodyH);
  });

  // 3. Open Positions Targets Overlay
  if (STATE.scalper.status && STATE.scalper.status.open_positions) {
    const activeForSym = STATE.scalper.status.open_positions.filter(p => p.symbol === STATE.scalper.activeSymbol);
    activeForSym.forEach(p => {
      // Entry Line
      const yEntry = getY(p.entry_price);
      scalpCtx.strokeStyle = p.side === "LONG" ? "#00f090" : "#ff3b69";
      scalpCtx.lineWidth = 1;
      scalpCtx.setLineDash([4, 4]);
      scalpCtx.beginPath();
      scalpCtx.moveTo(pad.left, yEntry);
      scalpCtx.lineTo(scalpWidth - pad.right, yEntry);
      scalpCtx.stroke();
      scalpCtx.setLineDash([]);

      // TP Line
      if (p.tp_price) {
        const yTP = getY(p.tp_price);
        scalpCtx.strokeStyle = "#00f090";
        scalpCtx.lineWidth = 1.2;
        scalpCtx.setLineDash([2, 2]);
        scalpCtx.beginPath();
        scalpCtx.moveTo(pad.left, yTP);
        scalpCtx.lineTo(scalpWidth - pad.right, yTP);
        scalpCtx.stroke();
        scalpCtx.setLineDash([]);
      }

      // SL Line
      if (p.sl_price) {
        const ySL = getY(p.sl_price);
        scalpCtx.strokeStyle = "#ff3b69";
        scalpCtx.lineWidth = 1.2;
        scalpCtx.setLineDash([2, 2]);
        scalpCtx.beginPath();
        scalpCtx.moveTo(pad.left, ySL);
        scalpCtx.lineTo(scalpWidth - pad.right, ySL);
        scalpCtx.stroke();
        scalpCtx.setLineDash([]);
      }
    });
  }
}

async function fetchScalperSignals() {
  try {
    const res = await fetch("/api/scalper/signals");
    const data = await res.json();
    if (!data.success || !data.signals) return;

    STATE.scalper.signals = data.signals;
    renderScalperSignals(data.signals);
  } catch (err) {
    console.error("Scalper signals fetch error", err);
  }
}

function renderScalperSignals(signals) {
  if (!DOM.scalpSignalsContainer) return;
  DOM.scalpSignalsContainer.innerHTML = "";

  if (!signals || signals.length === 0) {
    DOM.scalpSignalsContainer.innerHTML = `<div style="grid-column: 1/-1; text-align:center; color:var(--text-muted); padding:16px;">กำลังสแกนจังหวะโมเมนตัม 1M/5M/15M ทั่วตลาด...</div>`;
    return;
  }

  signals.forEach(s => {
    const card = document.createElement("div");
    const isLong = s.side === "LONG";
    card.className = `scalp-signal-item ${isLong ? 'long' : 'short'}`;
    const dec = s.current_price < 10 ? 4 : 2;

    card.innerHTML = `
      <div class="sig-item-top">
        <span class="sig-item-title">${s.icon} ${s.name} (${s.symbol})</span>
        <span class="sig-side-badge ${isLong ? 'long' : 'short'}">${isLong ? '🟢 LONG' : '🔴 SHORT'} (${s.confidence}%)</span>
      </div>
      <div class="sig-item-reason">💡 ${s.reason}</div>
      <div class="sig-item-targets">
        <span>ราคาเข้า: <strong>$${s.current_price.toFixed(dec)}</strong></span>
        <span style="color:#00f090;">TP: +${s.tp_pct}% ($${s.tp_price})</span>
        <span style="color:#ff3b69;">SL: -${s.sl_pct}% ($${s.sl_price})</span>
      </div>
      <button class="btn-apply-scalp-signal" onclick="applyScalpSignalToOrder('${s.symbol}', '${s.side}', ${s.suggested_leverage}, ${s.tp_pct}, ${s.sl_pct})">
        <span>⚡ 1-Click นำสัญญาณนี้ไปเปิดไม้</span>
      </button>
    `;
    DOM.scalpSignalsContainer.appendChild(card);
  });
}

// Global helper for 1-Click Signal Apply
window.applyScalpSignalToOrder = function(symbol, side, leverage, tpPct, slPct) {
  const isForex = symbol.includes("=") || symbol.includes("EUR") || symbol.includes("GBP") || symbol.includes("JPY");
  const targetAsset = isForex ? "FOREX" : "CRYPTO";

  switchScalpAssetClass(targetAsset, symbol);
  setScalpOrderSide(side);

  if (DOM.scalpLeveragePills) {
    DOM.scalpLeveragePills.querySelectorAll("button").forEach(btn => {
      btn.classList.toggle("active", parseFloat(btn.getAttribute("data-lev")) === leverage);
    });
  }
  STATE.scalper.leverage = leverage;
  if (DOM.scalpLeverageDisplay) DOM.scalpLeverageDisplay.textContent = `${leverage}X`;

  if (DOM.scalpTpInput) DOM.scalpTpInput.value = tpPct;
  if (DOM.scalpSlInput) DOM.scalpSlInput.value = slPct;
  STATE.scalper.tpPct = tpPct;
  STATE.scalper.slPct = slPct;

  updateScalpOrderFormCalculations();
  showToast(`🎯 โหลดสัญญาณ ${side} ${symbol} เข้าหน้าส่งคำสั่งเรียบร้อย!`, "info");
};

// Global helper for Close Ticket
window.closeScalperTicket = async function(ticketId) {
  if (!confirm(`ยืนยันการปิดตั๋วไม้ ${ticketId} ทันที?`)) return;
  try {
    const res = await fetch("/api/scalper/close-position", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ticket_id: ticketId })
    });
    const data = await res.json();
    showToast(data.message, data.success ? "success" : "error");
    fetchScalperStatus();
  } catch (err) {
    showToast("Close ticket failed: " + err, "error");
  }
};

async function executeScalperOrder() {
  const symbol = DOM.scalpOrderSymbol ? DOM.scalpOrderSymbol.value : STATE.scalper.activeSymbol;
  const side = STATE.scalper.activeSide || "LONG";
  const margin = parseFloat(DOM.scalpMarginInput ? DOM.scalpMarginInput.value : 2000) || 2000;
  const leverage = STATE.scalper.leverage || 5;
  const tpPct = parseFloat(DOM.scalpTpInput ? DOM.scalpTpInput.value : 1.5) || 1.5;
  const slPct = parseFloat(DOM.scalpSlInput ? DOM.scalpSlInput.value : 0.8) || 0.8;

  try {
    if (DOM.btnExecuteScalpOrder) DOM.btnExecuteScalpOrder.disabled = true;
    const res = await fetch("/api/scalper/order", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        symbol: symbol,
        side: side,
        margin_thb: margin,
        leverage: leverage,
        tp_pct: tpPct,
        sl_pct: slPct,
        notes: "Manual Execution from Scalper Pro"
      })
    });
    const data = await res.json();
    if (DOM.btnExecuteScalpOrder) DOM.btnExecuteScalpOrder.disabled = false;

    if (data.success) {
      showToast(`🎉 ${data.message}`, "success");
      fetchScalperStatus();
      fetchScalperChart(symbol, STATE.scalper.activeTf);
    } else {
      showToast(`⚠️ ${data.message || "ส่งคำสั่งไม่สำเร็จ"}`, "error");
    }
  } catch (err) {
    if (DOM.btnExecuteScalpOrder) DOM.btnExecuteScalpOrder.disabled = false;
    showToast("Order execution error: " + err, "error");
  }
}

async function closeAllScalperPositions() {
  if (!confirm("🚨 ยืนยันการปิดทุกไม้ Scalp ฉุกเฉินทั้งหมด (Emergency Close All Scalps)?")) return;
  try {
    const res = await fetch("/api/scalper/close-all", { method: "POST" });
    const data = await res.json();
    showToast(data.message, "success");
    fetchScalperStatus();
    fetchScalperChart(STATE.scalper.activeSymbol, STATE.scalper.activeTf);
  } catch (err) {
    showToast("Panic close failed: " + err, "error");
  }
}


