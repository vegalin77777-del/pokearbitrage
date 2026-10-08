// PokeArbitrage Pro 前端核心邏輯
let currentCategory = 'all';
let currentEncCategory = 'all';
let allCardsData = [];
let comparisonChartInstance = null;
let scanPollingInterval = null;

document.addEventListener('DOMContentLoaded', () => {
    loadSettings();
    loadDeals();
    loadCardsEncyclopedia();
    loadComparisonMatrix();
    checkScanStatus();
});

// ======================= 頁籤切換 =======================
function switchTab(tabId) {
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('bg-indigo-600', 'text-white', 'shadow-md', 'shadow-indigo-600/20');
        btn.classList.add('text-slate-400');
    });

    const activeBtn = document.getElementById(`tab-${tabId}`);
    if (activeBtn) {
        activeBtn.classList.remove('text-slate-400');
        activeBtn.classList.add('bg-indigo-600', 'text-white', 'shadow-md', 'shadow-indigo-600/20');
    }

    document.querySelectorAll('.tab-panel').forEach(panel => panel.classList.add('hidden'));
    const activePanel = document.getElementById(`panel-${tabId}`);
    if (activePanel) {
        activePanel.classList.remove('hidden');
    }

    if (tabId === 'comparison') {
        renderComparisonChart();
    }
}

// ======================= 撿漏雷達 (DEALS) =======================
function filterCategory(cat) {
    currentCategory = cat;
    document.querySelectorAll('.cat-pill').forEach(btn => {
        if (btn.getAttribute('data-cat') === cat) {
            btn.className = 'cat-pill px-3 py-1.5 rounded-lg text-xs font-bold bg-indigo-600 text-white';
        } else {
            btn.className = 'cat-pill px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-800 text-slate-400 hover:text-white';
        }
    });
    loadDeals();
}

async function loadDeals() {
    const tier = document.getElementById('filterTier').value;
    const sort = document.getElementById('filterSort').value;
    const excludeSuspicious = document.getElementById('chkExcludeSuspicious').checked;

    const url = `/api/deals?category=${currentCategory}&tier=${tier}&sort=${sort}&exclude_suspicious=${excludeSuspicious}`;
    
    try {
        const res = await fetch(url);
        const data = await res.json();
        
        if (data.status === 'success') {
            // 更新指標卡
            document.getElementById('metricSuperDeals').innerText = data.metrics.super_deals;
            document.getElementById('metricGoodDeals').innerText = data.metrics.good_deals;
            document.getElementById('metricAvgDiscount').innerText = `${data.metrics.avg_discount}%`;
            document.getElementById('metricLastScan').innerText = data.metrics.last_scan_time;
            document.getElementById('superDealsCountBadge').innerText = data.metrics.super_deals;

            renderDealsGrid(data.deals);
        }
    } catch (err) {
        console.error('Error loading deals:', err);
    }
}

function renderDealsGrid(deals) {
    const grid = document.getElementById('dealsGrid');
    const emptyState = document.getElementById('noDealsState');

    if (!deals || deals.length === 0) {
        grid.innerHTML = '';
        emptyState.classList.remove('hidden');
        return;
    }

    emptyState.classList.add('hidden');
    grid.innerHTML = deals.map(d => {
        const isSuper = d.deal_tier === 'SUPER_DEAL';
        const isSuspicious = d.is_suspicious;

        return `
            <div class="glass-card rounded-2xl p-5 border border-slate-800 relative flex flex-col justify-between ${isSuper ? 'glow-emerald border-emerald-500/40' : ''}">
                <div>
                    <!-- 頂部標籤與折扣 Badge -->
                    <div class="flex items-start justify-between gap-2 mb-3">
                        <div class="flex items-center gap-1.5 flex-wrap">
                            <span class="px-2 py-0.5 rounded-md text-[11px] font-black border ${d.tier_badge}">
                                ${d.tier_label}
                            </span>
                            <span class="px-2 py-0.5 rounded-md text-[11px] font-bold bg-slate-800 text-slate-300 border border-slate-700">
                                ${d.grade}
                            </span>
                        </div>
                        <div class="text-right">
                            <span class="text-xs font-black px-2 py-1 rounded-lg ${d.discount_pct >= 0 ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30' : 'bg-slate-800 text-slate-400'}">
                                ${d.discount_pct >= 0 ? `-${d.discount_pct}%` : `+${Math.abs(d.discount_pct)}%`}
                            </span>
                        </div>
                    </div>

                    <!-- 卡牌圖與商品標題 -->
                    <div class="flex gap-3 mb-4">
                        <div class="w-20 h-28 rounded-xl bg-slate-900 border border-slate-700/80 overflow-hidden flex-shrink-0 relative group">
                            <img src="${d.image_url}" alt="${d.card_name_zh}" class="w-full h-full object-cover group-hover:scale-110 transition-transform duration-300" onerror="this.src='https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/6.png'">
                        </div>
                        <div class="flex-1 min-w-0">
                            <span class="text-[11px] font-bold text-indigo-400 block truncate">${d.card_name_zh}</span>
                            <h4 class="text-xs font-medium text-slate-200 line-clamp-2 leading-relaxed mt-0.5" title="${d.title}">${d.title}</h4>
                            <div class="mt-2 text-[11px] text-slate-400 flex items-center gap-2">
                                <span class="truncate"><i class="fa-solid fa-user-check text-slate-500 mr-1"></i>${d.seller_name}</span>
                            </div>
                        </div>
                    </div>

                    <!-- 價格計算對比區 -->
                    <div class="bg-slate-900/80 rounded-xl p-3 border border-slate-800/80 mb-4 space-y-1.5">
                        <div class="flex justify-between items-baseline">
                            <span class="text-xs text-slate-400">即時特價：</span>
                            <div class="text-right">
                                <span class="text-lg font-black text-emerald-400">NT$ ${d.price_twd.toLocaleString()}</span>
                                <span class="text-[11px] text-slate-400 block font-mono">(¥ ${d.price_jpy.toLocaleString()})</span>
                            </div>
                        </div>
                        <div class="flex justify-between items-center text-[11px] pt-1 border-t border-slate-800/60">
                            <span class="text-slate-500">公道市價基準：</span>
                            <span class="text-slate-400 font-mono">NT$ ${d.fair_price_twd.toLocaleString()}</span>
                        </div>
                        <div class="flex justify-between items-center text-[11px]">
                            <span class="text-emerald-400 font-bold">現省金額：</span>
                            <span class="text-emerald-300 font-black font-mono">NT$ ${d.savings_twd > 0 ? d.savings_twd.toLocaleString() : 0}</span>
                        </div>
                    </div>

                    ${isSuspicious ? `
                        <div class="p-2 mb-3 rounded-lg bg-rose-950/60 border border-rose-800/80 text-[11px] text-rose-300 flex items-center gap-1.5">
                            <i class="fa-solid fa-triangle-exclamation text-rose-400"></i>
                            <span>${d.scam_reason}</span>
                        </div>
                    ` : ''}
                </div>

                <!-- 🛒 一鍵直達下單通道按鈕組 -->
                <div class="space-y-1.5 pt-2 border-t border-slate-800/80">
                    <p class="text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-1 flex items-center justify-between">
                        <span>⚡ 一鍵即時下單 / 搶購通道</span>
                        <span class="text-indigo-400">100% 帳號安全</span>
                    </p>
                    <div class="grid grid-cols-2 gap-1.5">
                        <a href="${d.links.tw_mercari}" target="_blank" rel="noopener noreferrer" class="flex items-center justify-center gap-1.5 py-2 px-2 rounded-xl bg-gradient-to-r from-indigo-600 to-indigo-700 hover:from-indigo-500 hover:to-indigo-600 text-white font-bold text-xs shadow-md shadow-indigo-600/30 transition-all active:scale-95">
                            <span>🇹🇼 台灣 Mercari</span>
                            <i class="fa-solid fa-arrow-up-right-from-square text-[10px]"></i>
                        </a>
                        <a href="${d.links.jp_mercari}" target="_blank" rel="noopener noreferrer" class="flex items-center justify-center gap-1.5 py-2 px-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-bold text-xs border border-slate-700 transition-all active:scale-95">
                            <span>🇯🇵 日本 Mercari</span>
                            <i class="fa-solid fa-arrow-up-right-from-square text-[10px]"></i>
                        </a>
                    </div>
                    <a href="${d.links.buyee}" target="_blank" rel="noopener noreferrer" class="block w-full text-center py-1.5 rounded-lg bg-slate-900/90 hover:bg-slate-800 text-[11px] text-slate-400 hover:text-slate-200 border border-slate-800 transition-all">
                        📦 海外 Buyee 代購直通車下單
                    </a>
                </div>
            </div>
        `;
    }).join('');
}


// ======================= 珍貴卡牌圖鑑百科 (ENCYCLOPEDIA) =======================
function filterCardsView(cat) {
    currentEncCategory = cat;
    document.querySelectorAll('.enc-pill').forEach(btn => {
        if (btn.getAttribute('data-enc') === cat) {
            btn.className = 'enc-pill px-3 py-1 text-xs font-bold rounded-lg bg-indigo-600 text-white';
        } else {
            btn.className = 'enc-pill px-3 py-1 text-xs rounded-lg bg-slate-800 text-slate-400 hover:text-white';
        }
    });
    renderCardsEncyclopedia();
}

async function loadCardsEncyclopedia() {
    try {
        const res = await fetch('/api/cards');
        const data = await res.json();
        if (data.status === 'success') {
            allCardsData = data.cards;
            renderCardsEncyclopedia();
        }
    } catch (err) {
        console.error('Error loading encyclopedia:', err);
    }
}

function renderCardsEncyclopedia() {
    const grid = document.getElementById('cardsEncyclopediaGrid');
    const filtered = currentEncCategory === 'all' 
        ? allCardsData 
        : allCardsData.filter(c => c.category === currentEncCategory);

    grid.innerHTML = filtered.map(c => `
        <div class="glass-card rounded-2xl p-5 border border-slate-800 flex flex-col md:flex-row gap-5">
            <!-- 卡片大圖 -->
            <div class="w-full md:w-36 flex-shrink-0 flex flex-col items-center">
                <div class="w-36 h-52 rounded-xl bg-slate-900 border border-slate-700 overflow-hidden shadow-xl mb-3">
                    <img src="${c.image_url}" alt="${c.name_zh}" class="w-full h-full object-cover hover:scale-105 transition-transform" onerror="this.src='https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/6.png'">
                </div>
                <button onclick="scanSingleCard('${c.id}')" class="w-full py-1.5 px-2 rounded-lg bg-indigo-600/30 hover:bg-indigo-600 text-indigo-300 hover:text-white font-bold text-xs border border-indigo-500/40 transition-all flex items-center justify-center gap-1">
                    <i class="fa-solid fa-magnifying-glass"></i>
                    <span>掃描此卡即時賣家</span>
                </button>
            </div>

            <!-- 卡牌詳細資產資訊 -->
            <div class="flex-1 space-y-3">
                <div class="flex items-start justify-between">
                    <div>
                        <span class="text-[11px] font-black uppercase tracking-wider text-amber-400">${c.category_name} (${c.release_year})</span>
                        <h3 class="text-base font-black text-white">${c.name_zh}</h3>
                        <p class="text-xs text-slate-400 font-mono">${c.name_en} / ${c.name_ja}</p>
                    </div>
                </div>

                <!-- 拍賣與存量數據 -->
                <div class="grid grid-cols-2 gap-2 text-xs">
                    <div class="bg-slate-900/80 p-2.5 rounded-xl border border-slate-800">
                        <span class="text-slate-500 block text-[10px]">PSA 10 拍賣天價紀錄</span>
                        <span class="font-black text-amber-300 text-sm">$${c.psa10_record_usd ? c.psa10_record_usd.toLocaleString() : '--'} USD</span>
                    </div>
                    <div class="bg-slate-900/80 p-2.5 rounded-xl border border-slate-800">
                        <span class="text-slate-500 block text-[10px]">PSA 10 全球存量</span>
                        <span class="font-bold text-slate-200 text-xs">${c.psa10_pop}</span>
                    </div>
                </div>

                <!-- 💡 珍貴原因深度解析 -->
                <div class="bg-indigo-950/30 border border-indigo-800/40 p-3 rounded-xl space-y-1">
                    <div class="flex items-center gap-1.5 text-xs font-bold text-indigo-300">
                        <i class="fa-solid fa-circle-question"></i>
                        <span>為什麼珍貴？(保值原因深度解析)</span>
                    </div>
                    <p class="text-xs text-slate-300 leading-relaxed">${c.rarity_reason}</p>
                </div>

                <!-- 行情基準與關鍵字 -->
                <div class="text-[11px] text-slate-400 flex items-center justify-between pt-1 border-t border-slate-800">
                    <span>市場基準：<strong class="text-slate-200 font-mono">NT$ ${c.market_fair_value_twd.toLocaleString()}</strong></span>
                    <span class="truncate max-w-[200px]" title="${c.search_keywords_mercari}">檢索關鍵字：${c.search_keywords_mercari}</span>
                </div>
            </div>
        </div>
    `).join('');
}


// ======================= 跨平台價格矩陣 (COMPARISON) =======================
async function loadComparisonMatrix() {
    try {
        const res = await fetch('/api/comparison');
        const data = await res.json();
        if (data.status === 'success') {
            renderComparisonTable(data.comparison);
            initComparisonChart(data.comparison);
        }
    } catch (err) {
        console.error('Error loading comparison matrix:', err);
    }
}

function renderComparisonTable(matrix) {
    const tbody = document.getElementById('comparisonTableBody');
    tbody.innerHTML = matrix.map(m => `
        <tr class="hover:bg-slate-800/40 transition-colors">
            <td class="p-3 font-semibold text-white flex items-center gap-2">
                <img src="${m.image_url}" class="w-8 h-10 object-cover rounded bg-slate-800" onerror="this.src='https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/6.png'">
                <div>
                    <div>${m.name_zh}</div>
                    <span class="text-[10px] text-slate-500">${m.release_year} 年發行</span>
                </div>
            </td>
            <td class="p-3 text-slate-400">${m.category_name}</td>
            <td class="p-3 text-right font-mono text-slate-300 font-bold">NT$ ${m.fair_price_twd.toLocaleString()}</td>
            <td class="p-3 text-right font-mono text-emerald-400 font-black">NT$ ${m.mercari_min_twd.toLocaleString()}</td>
            <td class="p-3 text-right font-mono text-cyan-400">NT$ ${m.cardmarket_trend_twd.toLocaleString()}</td>
            <td class="p-3 text-right font-mono text-amber-400">NT$ ${m.ebay_sold_twd.toLocaleString()}</td>
            <td class="p-3 text-center font-bold text-amber-300">$${m.psa10_record_usd ? m.psa10_record_usd.toLocaleString() : '--'}</td>
            <td class="p-3 text-center">
                <div class="flex items-center justify-center gap-2">
                    <a href="${m.cardmarket_url}" target="_blank" class="px-2 py-1 rounded bg-cyan-900/40 hover:bg-cyan-800 text-cyan-300 text-[11px] border border-cyan-700/60 transition-all">
                        Cardmarket
                    </a>
                    ${m.best_deal ? `
                        <a href="${m.best_deal.links.tw_mercari}" target="_blank" class="px-2 py-1 rounded bg-emerald-900/40 hover:bg-emerald-800 text-emerald-300 text-[11px] border border-emerald-700/60 font-bold transition-all">
                            Mercari 最低
                        </a>
                    ` : ''}
                </div>
            </td>
        </tr>
    `).join('');
}

function initComparisonChart(matrix) {
    const ctx = document.getElementById('comparisonChart');
    if (!ctx) return;

    // 取前 6 張熱門代表性卡牌作直觀圖表對比
    const sample = matrix.slice(0, 6);
    const labels = sample.map(s => s.name_zh.length > 10 ? s.name_zh.substring(0, 10) + '...' : s.name_zh);

    const fairPrices = sample.map(s => s.fair_price_twd);
    const mercariPrices = sample.map(s => s.mercari_min_twd);
    const cardmarketPrices = sample.map(s => s.cardmarket_trend_twd);
    const ebayPrices = sample.map(s => s.ebay_sold_twd);

    if (comparisonChartInstance) {
        comparisonChartInstance.destroy();
    }

    comparisonChartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: '公道行情基準 (TWD)',
                    data: fairPrices,
                    backgroundColor: 'rgba(148, 163, 184, 0.6)',
                    borderColor: '#94a3b8',
                    borderWidth: 1
                },
                {
                    label: 'Mercari 當前特惠 (TWD)',
                    data: mercariPrices,
                    backgroundColor: 'rgba(16, 185, 129, 0.8)',
                    borderColor: '#10b981',
                    borderWidth: 1
                },
                {
                    label: 'Cardmarket 趨勢 (TWD)',
                    data: cardmarketPrices,
                    backgroundColor: 'rgba(6, 182, 212, 0.8)',
                    borderColor: '#06b6d4',
                    borderWidth: 1
                },
                {
                    label: 'eBay 歷史成交均價 (TWD)',
                    data: ebayPrices,
                    backgroundColor: 'rgba(245, 158, 11, 0.8)',
                    borderColor: '#f59e0b',
                    borderWidth: 1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: { color: '#94a3b8', font: { size: 10 } }
                },
                x: {
                    grid: { display: false },
                    ticks: { color: '#cbd5e1', font: { size: 11, weight: 'bold' } }
                }
            },
            plugins: {
                legend: {
                    labels: { color: '#e2e8f0', font: { size: 11 } }
                }
            }
        }
    });
}

function renderComparisonChart() {
    if (comparisonChartInstance) {
        comparisonChartInstance.resize();
    }
}


// ======================= 掃描觸發與進度輪詢 =======================
async function triggerFullScan() {
    const btn = document.getElementById('btnTriggerScan');
    const icon = document.getElementById('scanIcon');
    icon.classList.add('fa-spin');

    try {
        const res = await fetch('/api/scan', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({})
        });
        const data = await res.json();
        
        if (data.status === 'started' || data.status === 'busy') {
            startScanProgressPolling();
        }
    } catch (err) {
        console.error('Trigger scan error:', err);
    }
}

async function scanSingleCard(cardId) {
    try {
        const res = await fetch('/api/scan', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ card_id: cardId })
        });
        const data = await res.json();
        if (data.status === 'started') {
            startScanProgressPolling();
            switchTab('deals');
        }
    } catch (err) {
        console.error('Scan single card error:', err);
    }
}

function startScanProgressPolling() {
    const progressContainer = document.getElementById('scanProgressBarContainer');
    const progressBar = document.getElementById('scanProgressBar');
    const statusText = document.getElementById('scanStatusText');
    const icon = document.getElementById('scanIcon');

    progressContainer.classList.remove('hidden');
    icon.classList.add('fa-spin');

    if (scanPollingInterval) clearInterval(scanPollingInterval);

    scanPollingInterval = setInterval(async () => {
        try {
            const res = await fetch('/api/scan/status');
            const data = await res.json();

            if (data.is_scanning) {
                progressBar.style.width = `${data.percentage}%`;
                statusText.innerText = `正在掃描: ${data.current_card} (${data.current}/${data.total})`;
            } else {
                clearInterval(scanPollingInterval);
                progressBar.style.width = '100%';
                setTimeout(() => {
                    progressContainer.classList.add('hidden');
                    progressBar.style.width = '0';
                    icon.classList.remove('fa-spin');
                    statusText.innerText = '掃描完成！定時排程運行中';
                    // 重新載入最新資料
                    loadDeals();
                    loadComparisonMatrix();
                }, 800);
            }
        } catch (err) {
            console.error('Polling error:', err);
        }
    }, 1500);
}

async function checkScanStatus() {
    try {
        const res = await fetch('/api/scan/status');
        const data = await res.json();
        if (data.is_scanning) {
            startScanProgressPolling();
        }
    } catch (err) {
        console.error('Check status error:', err);
    }
}


// ======================= 設定儲存 (SETTINGS) =======================
async function loadSettings() {
    try {
        const res = await fetch('/api/settings');
        const data = await res.json();
        if (data.status === 'success') {
            const s = data.settings;
            document.getElementById('cfgJpyRate').value = s.exchange_rates.JPY_TO_TWD;
            document.getElementById('cfgUsdRate').value = s.exchange_rates.USD_TO_TWD;
            document.getElementById('cfgEurRate').value = s.exchange_rates.EUR_TO_TWD;
            document.getElementById('cfgScanInterval').value = s.scan_interval_minutes;
            document.getElementById('cfgAutoScanEnabled').checked = s.auto_scan_enabled;
            document.getElementById('cfgPreferredPlatform').value = s.preferred_platform || 'tw_mercari';
            document.getElementById('cfgDiscordWebhook').value = s.notifications.discord_webhook_url || '';
            document.getElementById('cfgTgToken').value = s.notifications.telegram_bot_token || '';
            document.getElementById('cfgTgChatId').value = s.notifications.telegram_chat_id || '';
        }
    } catch (err) {
        console.error('Load settings error:', err);
    }
}

async function saveSettings() {
    const settings = {
        exchange_rates: {
            JPY_TO_TWD: parseFloat(document.getElementById('cfgJpyRate').value),
            USD_TO_TWD: parseFloat(document.getElementById('cfgUsdRate').value),
            EUR_TO_TWD: parseFloat(document.getElementById('cfgEurRate').value),
        },
        scan_interval_minutes: parseInt(document.getElementById('cfgScanInterval').value),
        auto_scan_enabled: document.getElementById('cfgAutoScanEnabled').checked,
        preferred_platform: document.getElementById('cfgPreferredPlatform').value,
        notifications: {
            discord_webhook_url: document.getElementById('cfgDiscordWebhook').value.trim(),
            telegram_bot_token: document.getElementById('cfgTgToken').value.trim(),
            telegram_chat_id: document.getElementById('cfgTgChatId').value.trim(),
        }
    };

    try {
        const res = await fetch('/api/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(settings)
        });
        const data = await res.json();
        if (data.status === 'success') {
            const statusEl = document.getElementById('settingsSaveStatus');
            statusEl.classList.remove('hidden');
            setTimeout(() => statusEl.classList.add('hidden'), 3000);
            // 重新刷新價格計算
            loadDeals();
            loadComparisonMatrix();
        }
    } catch (err) {
        console.error('Save settings error:', err);
    }
}
