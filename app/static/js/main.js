/* JaxStats — Gaming Dashboard Frontend */

let ddragonVersion = '14.10.1';
let charts = {};
let currentSummoner = 'aphae#raph';
let currentRegion = 'na1';

// ============ INIT ============
document.addEventListener('DOMContentLoaded', async () => {
    // Fetch DDragon version
    try {
        const resp = await fetch('https://ddragon.leagueoflegends.com/api/versions.json');
        const versions = await resp.json();
        ddragonVersion = versions[0];
    } catch (e) { /* keep default */ }

    // Set defaults
    document.getElementById('summonerName').value = currentSummoner;
    document.getElementById('region').value = currentRegion;

    // Tab switching
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.add('hidden'));
            btn.classList.add('active');
            document.getElementById(btn.dataset.tab).classList.remove('hidden');
        });
    });

    // Forms
    document.getElementById('summonerForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        currentSummoner = document.getElementById('summonerName').value;
        currentRegion = document.getElementById('region').value;
        await fetchStats(true);
    });

    document.getElementById('refreshBtn').addEventListener('click', () => fetchStats(false));
    document.getElementById('compareForm').addEventListener('submit', handleCompare);
});

// ============ FETCH STATS ============
async function fetchStats(useCache = true) {
    showLoading(true);
    hideError();
    document.getElementById('emptyState').classList.add('hidden');

    try {
        const resp = await fetch('/api/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                summoner_name: currentSummoner,
                region: currentRegion,
                match_count: 20,
                use_cache: useCache
            })
        });
        if (!resp.ok) {
            const err = await resp.json().catch(() => ({}));
            throw new Error(err.detail || 'Failed to fetch stats');
        }
        const data = await resp.json();

        // Hide empty state, show profile + stats
        document.getElementById('emptyState').classList.add('hidden');
        renderProfileBanner(data);
        renderDashboard(data);

        // Show stats tab
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.add('hidden'));
        document.getElementById('tabStats').classList.add('active');
        document.getElementById('statsTab').classList.remove('hidden');

        // Fetch live game in background
        fetchLiveGame();

        if (!useCache) showToast('Data refreshed', 'success');
    } catch (err) {
        showError(err.message);
    } finally {
        showLoading(false);
    }
}

// ============ GPI TIER ============
function gpiTierLabel(score) {
    if (score >= 80) return { label: 'Elite', color: '#fbbf24' };
    if (score >= 65) return { label: 'Great', color: '#22c55e' };
    if (score >= 50) return { label: 'Good', color: '#3b82f6' };
    if (score >= 35) return { label: 'Average', color: '#94a3b8' };
    return { label: 'Below Average', color: '#f87171' };
}

// ============ PROFILE BANNER ============
function renderProfileBanner(data) {
    const banner = document.getElementById('profileBanner');
    banner.classList.remove('hidden');
    banner.querySelector('.panel').classList.add('fade-in');

    document.getElementById('profileName').textContent = currentSummoner;
    document.getElementById('profileRegion').textContent = currentRegion.replace('1', '').toUpperCase();

    const gpi = data.gpi;
    const stats = data.overall_stats || {};
    const wr = pf(stats.win_rate);
    const kda = pf(stats.kda);

    if (gpi && gpi.overall) {
        const tier = gpiTierLabel(gpi.overall);
        document.getElementById('profileGPI').textContent = gpi.overall.toFixed(0);
        document.getElementById('profileGPITier').textContent = `GPI \u2022 ${tier.label}`;
        document.getElementById('profileGPITier').style.color = tier.color;
        document.getElementById('gpiTier').textContent = tier.label;
        document.getElementById('gpiTier').style.color = tier.color;
    }

    const wrEl = document.getElementById('profileWR');
    wrEl.textContent = wr.toFixed(1) + '%';
    wrEl.className = 'text-lg font-semibold ' + (wr >= 55 ? 'text-green-400' : wr <= 45 ? 'text-red-400' : 'text-gray-100');
    wrEl.style.fontFamily = "'Orbitron', sans-serif";

    document.getElementById('profileKDA').textContent = kda.toFixed(2);
}

// ============ RENDER DASHBOARD ============
function renderDashboard(data) {
    renderOverallStats(data.overall_stats, data.gpi);
    renderGPI(data.gpi);
    renderTrends(data.trends);
    renderMatchList(data.match_analyses);
    renderChampionStats(data.champion_stats);
    renderAdvancedStats(data.advanced_stats);
    renderCharts(data);

    // Refresh Lucide icons after dynamic content render
    if (typeof lucide !== 'undefined') lucide.createIcons();

    // Apply staggered fade-in to panels
    document.querySelectorAll('#statsTab .panel').forEach((panel, i) => {
        panel.classList.remove('fade-in');
        void panel.offsetWidth; // force reflow
        panel.style.animationDelay = `${i * 0.06}s`;
        panel.classList.add('fade-in');
    });
}

function renderOverallStats(stats, gpi) {
    if (!stats) return;
    const wr = pf(stats.win_rate);
    const kda = pf(stats.kda);
    const wrClass = wr >= 55 ? 'text-green-400' : wr <= 45 ? 'text-red-400' : 'text-gray-200';

    document.getElementById('overallStats').innerHTML = `
        <div class="stat-card">
            <div class="label"><i data-lucide="trophy" class="inline w-3 h-3 mr-1 opacity-40"></i>Win Rate</div>
            <div class="value ${wrClass}">${wr.toFixed(1)}%</div>
            <div class="text-xs text-gray-500">${pi(stats.wins)}W ${pi(stats.losses)}L</div>
        </div>
        <div class="stat-card">
            <div class="label"><i data-lucide="target" class="inline w-3 h-3 mr-1 opacity-40"></i>KDA</div>
            <div class="value">${kda.toFixed(2)}</div>
            <div class="text-xs text-gray-500">${pi(stats.kills)}/${pi(stats.deaths)}/${pi(stats.assists)}</div>
        </div>
        <div class="stat-card">
            <div class="label"><i data-lucide="hash" class="inline w-3 h-3 mr-1 opacity-40"></i>Matches</div>
            <div class="value">${pi(stats.total_matches)}</div>
        </div>
        <div class="stat-card">
            <div class="label"><i data-lucide="eye" class="inline w-3 h-3 mr-1 opacity-40"></i>Avg Vision</div>
            <div class="value">${stats.total_matches ? Math.round(pi(stats.vision_score)/pi(stats.total_matches)) : 0}</div>
        </div>
    `;
}

function renderGPI(gpi) {
    if (!gpi || !gpi.overall) {
        document.getElementById('gpiOverall').textContent = '--';
        return;
    }
    document.getElementById('gpiOverall').textContent = gpi.overall.toFixed(0);

    const skills = ['farming', 'vision', 'aggression', 'fighting', 'survivability', 'objectives', 'consistency', 'versatility'];
    const values = skills.map(s => gpi[s] || 0);

    destroyChart('gpiRadar');
    const ctx = document.getElementById('gpiRadar').getContext('2d');
    const radarGrad = ctx.createRadialGradient(ctx.canvas.width/2, ctx.canvas.height/2, 0, ctx.canvas.width/2, ctx.canvas.height/2, ctx.canvas.height/2);
    radarGrad.addColorStop(0, 'rgba(59,130,246,0.35)');
    radarGrad.addColorStop(1, 'rgba(59,130,246,0.05)');
    charts.gpiRadar = new Chart(ctx, {
        type: 'radar',
        data: {
            labels: skills.map(s => s.charAt(0).toUpperCase() + s.slice(1)),
            datasets: [{
                data: values,
                backgroundColor: radarGrad,
                borderColor: '#3b82f6',
                borderWidth: 2,
                pointBackgroundColor: '#3b82f6',
                pointRadius: 3,
                pointHoverRadius: 5,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                r: {
                    beginAtZero: true, max: 100,
                    ticks: { display: false, stepSize: 25 },
                    grid: { color: '#334155' },
                    pointLabels: { color: '#cbd5e1', font: { size: 10, family: "'Inter', sans-serif" } },
                    angleLines: { color: '#334155' },
                }
            },
            plugins: { legend: { display: false }, tooltip: themedTooltip }
        }
    });
}

function renderTrends(trends) {
    const el = document.getElementById('trendIndicators');
    if (!trends || !Object.keys(trends).length) { el.innerHTML = ''; return; }

    const labels = { kda: 'KDA', cs_per_min: 'CS/min', damage_dealt: 'Damage', gold_earned: 'Gold', vision_score: 'Vision' };
    const arrows = { improving: '\u2191', declining: '\u2193', stable: '\u2192' };

    let html = '';
    for (const [key, t] of Object.entries(trends)) {
        if (key === 'streak') {
            if (t.count >= 2) {
                const cls = t.type === 'win' ? 'improving' : 'declining';
                html += `<span class="trend-pill ${cls}">${t.count} ${t.type} streak</span>`;
            }
            continue;
        }
        if (!labels[key]) continue;
        html += `<span class="trend-pill ${t.direction}">${arrows[t.direction]} ${labels[key]} ${t.change_pct > 0 ? '+' : ''}${t.change_pct.toFixed(0)}%</span>`;
    }
    el.innerHTML = html;
}

function renderMatchList(matches) {
    const el = document.getElementById('matchList');
    if (!matches || !matches.length) { el.innerHTML = '<p class="text-gray-500 text-sm">No matches found</p>'; return; }

    el.innerHTML = matches.map((m, i) => {
        const ml = m.ml_scores || {};
        const score = ml.performance_score;
        const tier = ml.predicted_tier;
        const scoreCls = score >= 80 ? 'excellent' : score >= 60 ? 'good' : score >= 40 ? 'average' : 'poor';

        return `
        <div class="match-card" onclick="toggleDrop(${i})">
            <div class="flex items-center justify-between">
                <div class="flex items-center gap-3">
                    <img src="https://ddragon.leagueoflegends.com/cdn/${ddragonVersion}/img/champion/${m.champion || 'Aatrox'}.png"
                         alt="${m.champion}" class="champion-icon" onerror="this.src='https://ddragon.leagueoflegends.com/cdn/${ddragonVersion}/img/champion/Aatrox.png'">
                    <div>
                        <span class="font-medium text-sm">${m.champion || 'Unknown'}</span>
                        <span class="text-xs text-gray-500 ml-2">${m.position || ''}</span>
                    </div>
                </div>
                <div class="flex items-center gap-3">
                    ${score != null ? `<span class="score-badge ${scoreCls}">${score.toFixed(0)}</span>` : ''}
                    ${tier ? `<span class="tier-badge">${tier}</span>` : ''}
                    <div class="text-right">
                        <div class="win-indicator ${m.win ? 'win' : 'loss'}">${m.win ? 'W' : 'L'}</div>
                        <p class="text-xs text-gray-400 mt-0.5 font-mono">${pi(m.kills)}/${pi(m.deaths)}/${pi(m.assists)}</p>
                    </div>
                </div>
            </div>
            <div id="drop-${i}" class="match-dropdown hidden">
                <div class="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
                    <div><span class="text-gray-500">KDA</span><br><span class="font-mono">${pf(m.kda).toFixed(2)}</span></div>
                    <div><span class="text-gray-500">Damage</span><br><span class="font-mono">${pi(m.damage_dealt).toLocaleString()}</span></div>
                    <div><span class="text-gray-500">Gold</span><br><span class="font-mono">${pi(m.gold_earned).toLocaleString()}</span></div>
                    <div><span class="text-gray-500">Vision</span><br><span class="font-mono">${pi(m.vision_score)}</span></div>
                    <div><span class="text-gray-500">CS</span><br><span class="font-mono">${pi(m.minions_killed) + pi(m.neutral_minions_killed)}</span></div>
                    <div><span class="text-gray-500">Duration</span><br><span class="font-mono">${formatDuration(m.game_duration)}</span></div>
                    ${ml.win_probability != null ? `<div><span class="text-gray-500">Win Prob</span><br><span class="font-mono">${ml.win_probability.toFixed(0)}%</span></div>` : ''}
                </div>
                ${m.analysis ? `<div class="mt-3 text-xs text-gray-400 bg-gray-900/50 rounded p-2">${m.analysis}</div>` : ''}
            </div>
        </div>`;
    }).join('');
}

let champStatsData = [];
let champSortKey = 'games_played';
let champSortAsc = false;

function renderChampionStats(stats) {
    const el = document.getElementById('championStatsBody');
    if (!stats) { el.innerHTML = ''; champStatsData = []; return; }

    champStatsData = Object.entries(stats).map(([champ, d]) => ({ champ, ...d }));
    champSortKey = 'games_played';
    champSortAsc = false;
    renderChampionRows();
}

function renderChampionRows() {
    const el = document.getElementById('championStatsBody');
    const sorted = [...champStatsData].sort((a, b) => {
        const va = champSortKey === 'champ' ? a.champ.toLowerCase() : a[champSortKey];
        const vb = champSortKey === 'champ' ? b.champ.toLowerCase() : b[champSortKey];
        if (va < vb) return champSortAsc ? -1 : 1;
        if (va > vb) return champSortAsc ? 1 : -1;
        return 0;
    });

    el.innerHTML = sorted.map(d => `
        <tr class="border-t border-gray-800/50 hover:bg-gray-800/30 text-xs">
            <td class="p-2">
                <div class="flex items-center gap-2">
                    <img src="https://ddragon.leagueoflegends.com/cdn/${ddragonVersion}/img/champion/${d.champ}.png" alt="${d.champ}" class="w-6 h-6 rounded" onerror="this.style.display='none'">
                    <span>${d.champ}</span>
                </div>
            </td>
            <td class="p-2">${d.games_played}</td>
            <td class="p-2 ${d.win_rate >= 55 ? 'text-green-400' : d.win_rate <= 45 ? 'text-red-400' : ''}">${d.win_rate.toFixed(0)}%</td>
            <td class="p-2 font-mono">${d.kda.toFixed(2)}</td>
            <td class="p-2 font-mono">${d.avg_kills.toFixed(1)}/${d.avg_deaths.toFixed(1)}/${d.avg_assists.toFixed(1)}</td>
            <td class="p-2">${Math.round(d.avg_damage).toLocaleString()}</td>
            <td class="p-2">${Math.round(d.avg_gold).toLocaleString()}</td>
        </tr>
    `).join('');

    // Update sort indicators
    document.querySelectorAll('#championTable th[data-sort]').forEach(th => {
        const arrow = th.querySelector('.sort-arrow');
        if (th.dataset.sort === champSortKey) {
            arrow.textContent = champSortAsc ? ' \u25B2' : ' \u25BC';
        } else {
            arrow.textContent = '';
        }
    });
}

window.sortChampTable = function(key) {
    if (champSortKey === key) {
        champSortAsc = !champSortAsc;
    } else {
        champSortKey = key;
        champSortAsc = false;
    }
    renderChampionRows();
};

// ============ CHARTS ============
function makeGradient(ctx, colorTop, colorBot) {
    const g = ctx.createLinearGradient(0, 0, 0, ctx.canvas.height);
    g.addColorStop(0, colorTop);
    g.addColorStop(1, colorBot);
    return g;
}

const themedTooltip = {
    backgroundColor: 'rgba(15, 23, 42, 0.9)',
    titleColor: '#e2e8f0',
    bodyColor: '#94a3b8',
    borderColor: 'rgba(59, 130, 246, 0.3)',
    borderWidth: 1,
    cornerRadius: 8,
    padding: 10,
    titleFont: { family: "'Inter', sans-serif", weight: '600' },
    bodyFont: { family: "'Inter', sans-serif" },
};

function renderCharts(data) {
    const matches = data.trend_matches || [];
    if (!matches.length) return;

    const labels = matches.map((_, i) => `G${i + 1}`);
    const chartOpts = {
        responsive: true, maintainAspectRatio: false,
        scales: {
            x: { grid: { color: '#334155' }, ticks: { color: '#94a3b8', font: { size: 10 } } },
            y: { grid: { color: '#334155' }, ticks: { color: '#94a3b8', font: { size: 10 } } }
        },
        plugins: {
            legend: { labels: { color: '#cbd5e1', font: { size: 10 } } },
            tooltip: themedTooltip,
        }
    };

    // Performance trend (ML scores from match_analyses)
    const mlScores = (data.match_analyses || []).map(m => m.ml_scores?.performance_score || null).filter(s => s != null);
    if (mlScores.length) {
        destroyChart('perfTrendChart');
        const perfCtx = document.getElementById('perfTrendChart').getContext('2d');
        const perfGrad = makeGradient(perfCtx, 'rgba(59,130,246,0.3)', 'rgba(59,130,246,0)');
        charts.perfTrendChart = new Chart(perfCtx, {
            type: 'line', data: {
                labels: mlScores.map((_, i) => `G${i + 1}`),
                datasets: [{ label: 'Performance Score', data: mlScores, borderColor: '#3b82f6', backgroundColor: perfGrad, fill: true, tension: 0.3, pointRadius: 3, pointBackgroundColor: '#3b82f6' }]
            }, options: { ...chartOpts, scales: { ...chartOpts.scales, y: { ...chartOpts.scales.y, min: 0, max: 100 } } }
        });
    }

    // KDA trend with gradient fills
    destroyChart('kdaTrendChart');
    const kdaCtx = document.getElementById('kdaTrendChart').getContext('2d');
    const killGrad = makeGradient(kdaCtx, 'rgba(34,197,94,0.25)', 'rgba(34,197,94,0)');
    const deathGrad = makeGradient(kdaCtx, 'rgba(239,68,68,0.25)', 'rgba(239,68,68,0)');
    const assistGrad = makeGradient(kdaCtx, 'rgba(59,130,246,0.25)', 'rgba(59,130,246,0)');
    charts.kdaTrendChart = new Chart(kdaCtx, {
        type: 'line', data: {
            labels,
            datasets: [
                { label: 'Kills', data: matches.map(m => m.kills), borderColor: '#22c55e', backgroundColor: killGrad, fill: true, tension: 0.3, pointRadius: 2, pointBackgroundColor: '#22c55e' },
                { label: 'Deaths', data: matches.map(m => m.deaths), borderColor: '#ef4444', backgroundColor: deathGrad, fill: true, tension: 0.3, pointRadius: 2, pointBackgroundColor: '#ef4444' },
                { label: 'Assists', data: matches.map(m => m.assists), borderColor: '#3b82f6', backgroundColor: assistGrad, fill: true, tension: 0.3, pointRadius: 2, pointBackgroundColor: '#3b82f6' },
            ]
        }, options: chartOpts
    });

    // Role distribution
    const roles = {};
    (data.overall_stats?.positions_played || {}) && Object.entries(data.overall_stats.positions_played).forEach(([pos, d]) => {
        if (pos) roles[pos] = d.games;
    });
    if (Object.keys(roles).length) {
        destroyChart('roleChart');
        charts.roleChart = new Chart(document.getElementById('roleChart'), {
            type: 'doughnut', data: {
                labels: Object.keys(roles),
                datasets: [{ data: Object.values(roles), backgroundColor: ['#3b82f6', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6'], borderColor: 'rgba(15,23,42,0.8)', borderWidth: 2 }]
            }, options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'right', labels: { color: '#94a3b8', font: { size: 10 } } }, tooltip: themedTooltip } }
        });
    }

    // Damage breakdown (average physical/magic/true from match analyses)
    const analyses = data.match_analyses || [];
    if (analyses.length) {
        const physArr = [], magArr = [], trueArr = [];
        analyses.forEach(m => {
            const c = m.challenges || {};
            physArr.push(pi(m.damage_dealt) * 0.6); // approximation if no breakdown
            magArr.push(pi(m.damage_dealt) * 0.3);
            trueArr.push(pi(m.damage_dealt) * 0.1);
        });
        destroyChart('dmgChart');
        charts.dmgChart = new Chart(document.getElementById('dmgChart'), {
            type: 'bar', data: {
                labels: analyses.slice(0, 10).map((_, i) => `G${i + 1}`),
                datasets: [
                    { label: 'Physical', data: physArr.slice(0, 10), backgroundColor: 'rgba(245,158,11,0.8)', borderRadius: 2 },
                    { label: 'Magic', data: magArr.slice(0, 10), backgroundColor: 'rgba(59,130,246,0.8)', borderRadius: 2 },
                    { label: 'True', data: trueArr.slice(0, 10), backgroundColor: 'rgba(226,232,240,0.8)', borderRadius: 2 },
                ]
            }, options: { ...chartOpts, scales: { ...chartOpts.scales, x: { ...chartOpts.scales.x, stacked: true }, y: { ...chartOpts.scales.y, stacked: true } } }
        });
    }
}

// ============ ADVANCED STATS ============
function renderAdvancedStats(stats) {
    const container = document.getElementById('advancedStatsContainer');
    if (!stats || !Object.keys(stats).length) {
        container.classList.add('hidden');
        return;
    }
    container.classList.remove('hidden');
    renderLaneDominance(stats.lane_dominance);
    renderClutchFactor(stats.clutch_factor);
    renderSkillshot(stats.skillshot_accuracy);
    renderCommunication(stats.communication);
    renderVisionQuality(stats.vision_quality);
    renderEfficiency(stats.efficiency);
    renderRoleSpecific(stats.counter_jungle, stats.tank_frontline, stats.support_value);
    renderCrossMatch(stats.cross_match);

    // Refresh icons + staggered fade-in for advanced panels
    if (typeof lucide !== 'undefined') lucide.createIcons();
    container.querySelectorAll('.panel').forEach((panel, i) => {
        panel.classList.remove('fade-in');
        void panel.offsetWidth;
        panel.style.animationDelay = `${i * 0.06}s`;
        panel.classList.add('fade-in');
    });
}

function compositeBar(value, max = 100) {
    const pct = Math.min(value / max * 100, 100);
    const color = pct >= 60 ? 'linear-gradient(90deg,#3b82f6,#22c55e)' : pct >= 35 ? 'linear-gradient(90deg,#f59e0b,#fbbf24)' : 'linear-gradient(90deg,#ef4444,#f87171)';
    return `<div class="composite-bar mt-2"><div class="composite-fill" style="width:${pct}%;background:${color}"></div></div>`;
}

function sparkline(values, max = 100) {
    if (!values.length) return '';
    return `<div class="sparkline-bar">${values.map(v => {
        const h = Math.max(v / max * 40, 2);
        const bg = v >= 60 ? '#22c55e' : v >= 35 ? '#f59e0b' : '#64748b';
        return `<div style="height:${h}px;background:${bg}" title="${v}"></div>`;
    }).join('')}</div>`;
}

function renderLaneDominance(data) {
    if (!data) return;
    document.getElementById('laneDominancePanel').innerHTML = `
        <h2 class="panel-title"><i data-lucide="sword" class="inline w-3.5 h-3.5 mr-1.5 opacity-50"></i>Lane Dominance</h2>
        <p class="text-2xl font-bold text-blue-400">${data.average}<span class="text-sm text-gray-500 ml-1">/100</span></p>
        ${compositeBar(data.average)}
        ${sparkline(data.per_match)}
    `;
}

function renderClutchFactor(data) {
    if (!data) return;
    document.getElementById('clutchFactorPanel').innerHTML = `
        <h2 class="panel-title"><i data-lucide="zap" class="inline w-3.5 h-3.5 mr-1.5 opacity-50"></i>Clutch Factor</h2>
        <p class="text-2xl font-bold text-purple-400">${data.average}<span class="text-sm text-gray-500 ml-1">/100</span></p>
        ${compositeBar(data.average)}
        ${sparkline(data.per_match)}
    `;
}

function renderSkillshot(data) {
    if (!data) return;

    // Per-champion breakdown
    const perChamp = data.per_champion || {};
    const champRows = Object.entries(perChamp)
        .sort((a, b) => b[1].games - a[1].games)
        .map(([champ, d]) => {
            const pct = Math.min(d.average, 100);
            const color = pct >= 25 ? '#22c55e' : pct >= 15 ? '#f59e0b' : '#ef4444';
            return `
            <div class="flex items-center gap-2 py-1.5 border-b border-gray-800/50 last:border-0">
                <img src="https://ddragon.leagueoflegends.com/cdn/${ddragonVersion}/img/champion/${champ}.png" alt="${champ}" class="w-5 h-5 rounded" onerror="this.style.display='none'">
                <span class="text-xs flex-1">${champ}</span>
                <span class="text-xs text-gray-400">${d.games}g</span>
                <div class="w-16 h-1.5 bg-gray-800 rounded overflow-hidden">
                    <div class="h-full rounded" style="width:${pct}%;background:${color}"></div>
                </div>
                <span class="text-xs font-semibold w-10 text-right" style="color:${color}">${d.average}%</span>
            </div>`;
        }).join('');

    document.getElementById('skillshotPanel').innerHTML = `
        <h2 class="panel-title"><i data-lucide="crosshair" class="inline w-3.5 h-3.5 mr-1.5 opacity-50"></i>Skillshot Accuracy</h2>
        <p class="text-2xl font-bold text-cyan-400">${data.average}<span class="text-sm text-gray-500 ml-1">%</span></p>
        ${compositeBar(data.average)}
        <div class="flex justify-between mt-3 text-xs text-gray-500">
            <span>${data.total_hits.toLocaleString()} hits</span>
            <span>${data.total_uses.toLocaleString()} casts</span>
        </div>
        ${champRows ? `<div class="mt-4 pt-3 border-t border-gray-800"><div class="text-xs text-gray-400 mb-2 uppercase tracking-wider font-medium">By Champion</div>${champRows}</div>` : ''}
    `;
}

function renderCommunication(data) {
    if (!data) return;
    const pingLabels = {
        allInPings: 'All In', assistMePings: 'Assist Me', commandPings: 'Command',
        dangerPings: 'Danger', enemyMissingPings: 'Enemy Missing', enemyVisionPings: 'Enemy Vision',
        getBackPings: 'Get Back', holdPings: 'Hold', needVisionPings: 'Need Vision',
        onMyWayPings: 'On My Way', pushPings: 'Push',
    };
    const archetypeClass = {
        'Shotcaller': 'shotcaller', 'Danger Pinger': 'danger', 'Quiet': 'quiet', 'Communicator': 'communicator'
    }[data.archetype] || 'quiet';

    const maxPings = Math.max(...Object.values(data.pings), 1);
    const pingBars = Object.entries(data.pings)
        .filter(([, v]) => v > 0)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 6)
        .map(([type, count]) => {
            const pct = (count / maxPings * 100).toFixed(0);
            return `<div class="mini-stat">
                <span class="label">${pingLabels[type] || type}</span>
                <div class="flex-1 mx-2"><div class="composite-bar"><div class="composite-fill" style="width:${pct}%"></div></div></div>
                <span class="value">${count}</span>
            </div>`;
        }).join('');

    document.getElementById('communicationPanel').innerHTML = `
        <h2 class="panel-title"><i data-lucide="message-circle" class="inline w-3.5 h-3.5 mr-1.5 opacity-50"></i>Communication</h2>
        <div class="flex items-center gap-3 mb-3">
            <span class="archetype-badge ${archetypeClass}">${data.archetype}</span>
            <span class="text-xs text-gray-500">${data.pings_per_min} pings/min</span>
            <span class="text-xs text-gray-600">${data.total_pings} total</span>
        </div>
        ${pingBars}
    `;
}

function renderVisionQuality(data) {
    if (!data) return;
    document.getElementById('visionQualityPanel').innerHTML = `
        <h2 class="panel-title"><i data-lucide="eye" class="inline w-3.5 h-3.5 mr-1.5 opacity-50"></i>Vision Quality</h2>
        <div class="grid grid-cols-2 gap-3">
            <div class="stat-card">
                <div class="label">Control Ward Coverage</div>
                <div class="value text-sm">${data.avg_control_ward_coverage}%</div>
            </div>
            <div class="stat-card">
                <div class="label">Vision Advantage</div>
                <div class="value text-sm">${data.avg_vision_advantage > 0 ? '+' : ''}${data.avg_vision_advantage}</div>
            </div>
            <div class="stat-card">
                <div class="label">Unseen Recalls</div>
                <div class="value text-sm">${data.total_unseen_recalls}</div>
            </div>
            <div class="stat-card">
                <div class="label">Early Ward Kills</div>
                <div class="value text-sm">${data.total_ward_takedowns_early}</div>
            </div>
        </div>
    `;
}

function renderEfficiency(data) {
    if (!data) return;
    const stats = [
        { label: 'Dmg/Gold Spent', value: data.avg_damage_per_gold_spent },
        { label: 'Gold Efficiency', value: data.avg_gold_efficiency + '%' },
        { label: 'Kill Share', value: data.avg_kill_participation_ratio + '%' },
        { label: 'CC/Death', value: data.avg_cc_per_death + 's' },
        { label: 'Dmg/Gold Earned', value: data.avg_damage_per_gold_earned },
    ];
    document.getElementById('efficiencyPanel').innerHTML = `
        <h2 class="panel-title"><i data-lucide="gauge" class="inline w-3.5 h-3.5 mr-1.5 opacity-50"></i>Efficiency Ratios</h2>
        <div class="grid grid-cols-2 md:grid-cols-5 gap-3">
            ${stats.map(s => `<div class="stat-card"><div class="label">${s.label}</div><div class="value text-sm">${s.value}</div></div>`).join('')}
        </div>
    `;
}

function renderRoleSpecific(jungle, tank, support) {
    const row = document.getElementById('roleSpecificRow');
    const jp = document.getElementById('counterJunglePanel');
    const tp = document.getElementById('tankFrontlinePanel');
    const sp = document.getElementById('supportValuePanel');
    let anyVisible = false;

    if (jungle) {
        anyVisible = true;
        jp.classList.remove('hidden');
        jp.innerHTML = `
            <h2 class="panel-title"><i data-lucide="trees" class="inline w-3.5 h-3.5 mr-1.5 opacity-50"></i>Counter-Jungle</h2>
            <p class="text-xs text-gray-500 mb-2">${jungle.games} jungle game${jungle.games !== 1 ? 's' : ''}</p>
            <div class="mini-stat"><span class="label">Avg Buffs Stolen</span><span class="value">${jungle.avg_buffs_stolen}</span></div>
            <div class="mini-stat"><span class="label">Avg Enemy Camp Kills</span><span class="value">${jungle.avg_enemy_jungle_kills}</span></div>
            ${jungle.per_match.length ? jungle.per_match.map((m, i) => `
                <div class="text-xs text-gray-600 mt-1">G${i+1}: ${m.buffs_stolen} stolen, ${m.enemy_jungle_kills} camps, ${m.scuttle_kills} crabs</div>
            `).slice(0, 3).join('') : ''}
        `;
    } else { jp.classList.add('hidden'); }

    if (tank) {
        anyVisible = true;
        tp.classList.remove('hidden');
        tp.innerHTML = `
            <h2 class="panel-title"><i data-lucide="shield" class="inline w-3.5 h-3.5 mr-1.5 opacity-50"></i>Tank / Frontline</h2>
            <p class="text-xs text-gray-500 mb-2">${tank.games} tanky game${tank.games !== 1 ? 's' : ''}</p>
            <div class="mini-stat"><span class="label">Avg Damage Mitigated</span><span class="value">${Math.round(tank.avg_damage_mitigated).toLocaleString()}</span></div>
            ${tank.per_match.length ? `
                <div class="mini-stat"><span class="label">Survived Full Team Dmg</span><span class="value">${tank.per_match.reduce((a,m) => a + m.killed_champ_full_team_survived, 0)}</span></div>
                <div class="mini-stat"><span class="label">Survived 3+ CC</span><span class="value">${tank.per_match.reduce((a,m) => a + m.survived_three_immobilizes, 0)}</span></div>
                <div class="mini-stat"><span class="label">Took Large Dmg & Lived</span><span class="value">${tank.per_match.reduce((a,m) => a + m.took_large_damage_survived, 0)}</span></div>
            ` : ''}
        `;
    } else { tp.classList.add('hidden'); }

    if (support) {
        anyVisible = true;
        sp.classList.remove('hidden');
        sp.innerHTML = `
            <h2 class="panel-title"><i data-lucide="heart-pulse" class="inline w-3.5 h-3.5 mr-1.5 opacity-50"></i>Support Value</h2>
            <p class="text-xs text-gray-500 mb-2">${support.games} support game${support.games !== 1 ? 's' : ''}</p>
            <div class="mini-stat"><span class="label">Avg Shielding</span><span class="value">${Math.round(support.avg_shields).toLocaleString()}</span></div>
            <div class="mini-stat"><span class="label">Avg Healing</span><span class="value">${Math.round(support.avg_heals).toLocaleString()}</span></div>
            ${support.per_match.length ? `
                <div class="mini-stat"><span class="label">Ally Saves</span><span class="value">${support.per_match.reduce((a,m) => a + m.save_ally, 0)}</span></div>
                <div class="mini-stat"><span class="label">Quest On Time</span><span class="value">${support.per_match.filter(m => m.quest_completed_on_time).length}/${support.games}</span></div>
            ` : ''}
        `;
    } else { sp.classList.add('hidden'); }

    row.classList.toggle('hidden', !anyVisible);
}

function renderCrossMatch(data) {
    if (!data) return;
    const tilt = data.tilt_detection || {};
    const tod = data.time_of_day || {};
    const surr = data.surrender_stats || {};

    // Tilt Detection
    const wrAfterWin = tilt.wr_after_win != null ? tilt.wr_after_win : '--';
    const wrAfterLoss = tilt.wr_after_loss != null ? tilt.wr_after_loss : '--';
    let tiltLabel = '';
    if (tilt.wr_after_win != null && tilt.wr_after_loss != null) {
        const diff = tilt.wr_after_win - tilt.wr_after_loss;
        if (diff > 15) tiltLabel = '<span class="highlight-pill" style="background:#064e3b;color:#6ee7b7">Momentum Player</span>';
        else if (diff < -15) tiltLabel = '<span class="highlight-pill" style="background:#7f1d1d;color:#fca5a5">Tilt Prone</span>';
        else tiltLabel = '<span class="highlight-pill">Mentally Stable</span>';
    }
    document.getElementById('tiltDetectionPanel').innerHTML = `
        <h2 class="panel-title"><i data-lucide="brain" class="inline w-3.5 h-3.5 mr-1.5 opacity-50"></i>Tilt Detection</h2>
        <div class="mb-2">${tiltLabel}</div>
        <div class="mini-stat"><span class="label">WR After Win</span><span class="value ${typeof wrAfterWin === 'number' && wrAfterWin >= 50 ? 'text-green-400' : ''}">${wrAfterWin}${typeof wrAfterWin === 'number' ? '%' : ''}</span></div>
        <div class="mini-stat"><span class="label">WR After Loss</span><span class="value ${typeof wrAfterLoss === 'number' && wrAfterLoss >= 50 ? 'text-green-400' : 'text-red-400'}">${wrAfterLoss}${typeof wrAfterLoss === 'number' ? '%' : ''}</span></div>
        <div class="text-xs text-gray-600 mt-2">${tilt.games_after_win || 0} games after wins, ${tilt.games_after_loss || 0} after losses</div>
    `;

    // Time of Day
    const todEntries = Object.entries(tod);
    const maxGames = Math.max(...todEntries.map(([,d]) => d.games), 1);
    const todBars = todEntries.map(([bucket, d]) => {
        const h = Math.max(d.games / maxGames * 50, 4);
        const bg = d.win_rate >= 55 ? '#22c55e' : d.win_rate <= 45 ? '#ef4444' : '#3b82f6';
        return `<div class="text-center flex-1">
            <div class="mx-auto rounded-t-sm" style="height:${h}px;width:80%;background:${bg}" title="${d.win_rate}% WR"></div>
            <div class="text-xs text-gray-600 mt-1">${bucket}</div>
            <div class="text-xs text-gray-500">${d.games}g ${d.win_rate}%</div>
        </div>`;
    }).join('');
    document.getElementById('timeOfDayPanel').innerHTML = `
        <h2 class="panel-title"><i data-lucide="clock" class="inline w-3.5 h-3.5 mr-1.5 opacity-50"></i>Time of Day (UTC)</h2>
        <div class="flex items-end gap-1 mt-2" style="min-height:70px">${todBars}</div>
    `;

    // Surrender Stats
    document.getElementById('surrenderPanel').innerHTML = `
        <h2 class="panel-title"><i data-lucide="flag" class="inline w-3.5 h-3.5 mr-1.5 opacity-50"></i>Surrender Stats</h2>
        <div class="mini-stat"><span class="label">Surrenders</span><span class="value">${surr.total_surrenders} / ${surr.total_games}</span></div>
        <div class="mini-stat"><span class="label">Early FFs</span><span class="value">${surr.early_surrenders}</span></div>
        <div class="mini-stat"><span class="label">Surrender Rate</span><span class="value">${surr.surrender_rate}%</span></div>
        ${compositeBar(surr.surrender_rate)}
    `;
}

// ============ COMPARISON ============
async function handleCompare(e) {
    e.preventDefault();
    showLoading(true);
    hideError();

    try {
        const resp = await fetch('/api/compare', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                summoner1_name: document.getElementById('summoner1Name').value,
                summoner1_region: document.getElementById('summoner1Region').value,
                summoner2_name: document.getElementById('summoner2Name').value,
                summoner2_region: document.getElementById('summoner2Region').value,
                match_count: 10
            })
        });
        if (!resp.ok) throw new Error('Comparison failed');
        const data = await resp.json();
        renderComparison(data.user1, data.user2);
    } catch (err) {
        showError(err.message);
    } finally {
        showLoading(false);
    }
}

function renderComparison(u1, u2) {
    const el = document.getElementById('comparisonResults');
    el.classList.remove('hidden');

    const stats = [
        { label: 'Win Rate', key: 'win_rate', suffix: '%', decimals: 1 },
        { label: 'KDA', key: 'kda', decimals: 2 },
        { label: 'Avg Damage', key: 'total_damage_dealt', avg: true },
        { label: 'Avg Gold', key: 'total_gold_earned', avg: true },
        { label: 'Avg Vision', key: 'vision_score', avg: true },
    ];

    const s1 = u1.overall_stats || {};
    const s2 = u2.overall_stats || {};
    const m1 = Math.max(pi(s1.total_matches), 1);
    const m2 = Math.max(pi(s2.total_matches), 1);

    let barsHtml = stats.map(s => {
        let v1 = pf(s1[s.key]);
        let v2 = pf(s2[s.key]);
        if (s.avg) { v1 = v1 / m1; v2 = v2 / m2; }
        const max = Math.max(v1, v2, 1);
        const p1 = (v1 / max * 100).toFixed(0);
        const p2 = (v2 / max * 100).toFixed(0);
        const d = s.decimals || 0;
        const suf = s.suffix || '';

        return `
        <div class="compare-bar">
            <span class="text-xs text-blue-400 w-16 text-right font-mono">${v1.toFixed(d)}${suf}</span>
            <div class="bar-track"><div class="bar-fill blue" style="width:${p1}%;float:right"></div></div>
            <span class="text-xs text-gray-500 w-20 text-center">${s.label}</span>
            <div class="bar-track"><div class="bar-fill red" style="width:${p2}%"></div></div>
            <span class="text-xs text-red-400 w-16 font-mono">${v2.toFixed(d)}${suf}</span>
        </div>`;
    }).join('');

    // GPI comparison
    const g1 = u1.gpi || {};
    const g2 = u2.gpi || {};
    const gpiSkills = ['farming', 'vision', 'aggression', 'fighting', 'survivability', 'objectives'];
    let gpiHtml = gpiSkills.map(skill => {
        const v1 = pf(g1[skill]);
        const v2 = pf(g2[skill]);
        return `
        <div class="compare-bar">
            <span class="text-xs text-blue-400 w-12 text-right font-mono">${v1.toFixed(0)}</span>
            <div class="bar-track"><div class="bar-fill blue" style="width:${v1}%;float:right"></div></div>
            <span class="text-xs text-gray-500 w-24 text-center">${skill.charAt(0).toUpperCase() + skill.slice(1)}</span>
            <div class="bar-track"><div class="bar-fill red" style="width:${v2}%"></div></div>
            <span class="text-xs text-red-400 w-12 font-mono">${v2.toFixed(0)}</span>
        </div>`;
    }).join('');

    el.innerHTML = `
        <div class="panel fade-in">
            <div class="flex justify-between mb-4">
                <span class="text-blue-400 font-medium">${u1.summoner_name}</span>
                <span class="text-gray-500 text-sm">VS</span>
                <span class="text-red-400 font-medium">${u2.summoner_name}</span>
            </div>
            <div class="space-y-2 mb-6">${barsHtml}</div>
            <h3 class="panel-title mt-4"><i data-lucide="radar" class="inline w-3.5 h-3.5 mr-1.5 opacity-50"></i>GPI Skills</h3>
            <div class="space-y-2">${gpiHtml}</div>
        </div>`;
    if (typeof lucide !== 'undefined') lucide.createIcons();
}

// ============ LIVE GAME ============
async function fetchLiveGame() {
    const el = document.getElementById('liveGameContent');
    try {
        const resp = await fetch(`/api/live-game/${encodeURIComponent(currentSummoner)}?region=${currentRegion}`);
        if (resp.status === 404) {
            el.innerHTML = '<p class="text-gray-500 text-sm">Not currently in a game</p>';
            return;
        }
        if (!resp.ok) throw new Error('Failed to fetch live game');
        const data = await resp.json();
        renderLiveGame(data);
    } catch (err) {
        el.innerHTML = `<p class="text-gray-500 text-sm">${err.message}</p>`;
    }
}

function renderLiveGame(data) {
    const el = document.getElementById('liveGameContent');
    const team1 = data.participants.filter(p => p.teamId === 100);
    const team2 = data.participants.filter(p => p.teamId === 200);

    const renderTeam = (team, color) => team.map(p => {
        const gpi = p.gpi || {};
        return `
        <div class="player-row">
            <div class="flex-1">
                <div class="text-sm font-medium">${p.summonerName || 'Unknown'}</div>
                <div class="text-xs text-gray-500">Champion ID: ${p.championId}</div>
            </div>
            ${gpi.overall ? `<span class="score-badge ${gpi.overall >= 60 ? 'good' : 'average'}">${gpi.overall.toFixed(0)}</span>` : ''}
            ${p.recent_win_rate != null ? `<span class="text-xs text-gray-400">${p.recent_win_rate.toFixed(0)}% WR</span>` : ''}
        </div>`;
    }).join('');

    el.innerHTML = `
        <div class="text-center text-xs text-gray-500 mb-4">${data.game_mode} — ${formatDuration(data.game_length)}</div>
        <div class="team-grid">
            <div>
                <h3 class="text-sm font-medium text-blue-400 mb-2">Blue Team</h3>
                <div class="space-y-2">${renderTeam(team1, 'blue')}</div>
            </div>
            <div>
                <h3 class="text-sm font-medium text-red-400 mb-2">Red Team</h3>
                <div class="space-y-2">${renderTeam(team2, 'red')}</div>
            </div>
        </div>`;
    if (typeof lucide !== 'undefined') lucide.createIcons();
}

// ============ UTILITIES ============
function pf(v) { return parseFloat(v) || 0; }
function pi(v) { return parseInt(v) || 0; }
function formatDuration(s) { const m = Math.floor((s||0)/60); const sec = (s||0)%60; return `${m}:${sec.toString().padStart(2,'0')}`; }

function destroyChart(id) { if (charts[id]) { charts[id].destroy(); charts[id] = null; } }

function showLoading(show) {
    document.getElementById('loading').classList.toggle('hidden', !show);
}

function showError(msg) {
    const el = document.getElementById('error');
    el.textContent = msg;
    el.classList.remove('hidden');
}

function hideError() {
    document.getElementById('error').classList.add('hidden');
}

function showToast(msg, type = 'success') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = msg;
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}

window.toggleDrop = function(i) {
    const el = document.getElementById(`drop-${i}`);
    if (el) el.classList.toggle('hidden');
};

// ============ WATCHLIST ============
let watchlistLoaded = false;

async function loadWatchlist() {
    try {
        const resp = await fetch('/api/watchlist');
        if (!resp.ok) throw new Error('Failed to load watchlist');
        const data = await resp.json();
        renderWatchlistCards(data.summoners);
        applyScheduleToForm(data.schedule);
    } catch (err) {
        console.error('Watchlist load error:', err);
    }
}

function applyScheduleToForm(schedule) {
    if (!schedule) return;
    document.getElementById('wlSchedEnabled').checked = schedule.enabled;
    document.getElementById('wlSchedTime').value = schedule.time || '06:00';
    const tzSel = document.getElementById('wlSchedTz');
    for (const opt of tzSel.options) {
        if (opt.value === schedule.timezone) { opt.selected = true; break; }
    }
}

function renderWatchlistCards(summoners) {
    const container = document.getElementById('watchlistCards');
    const empty = document.getElementById('watchlistEmpty');

    if (!summoners || !summoners.length) {
        container.innerHTML = '';
        container.appendChild(empty);
        empty.classList.remove('hidden');
        if (typeof lucide !== 'undefined') lucide.createIcons();
        return;
    }

    const freshMs = 24 * 60 * 60 * 1000; // 24h
    const staleMs = 48 * 60 * 60 * 1000; // 48h

    container.innerHTML = summoners.map(s => {
        const lat = s.latest || {};
        const lastRefreshed = lat.last_refreshed;
        let statusClass = 'wl-status-none';
        let statusTitle = 'Never refreshed';
        if (lastRefreshed) {
            const age = Date.now() - new Date(lastRefreshed).getTime();
            if (age < freshMs) { statusClass = 'wl-status-fresh'; statusTitle = 'Refreshed recently'; }
            else if (age < staleMs) { statusClass = 'wl-status-stale'; statusTitle = 'Stale (>24h)'; }
            else { statusClass = 'wl-status-old'; statusTitle = 'Old (>48h)'; }
        }

        const gpi = lat.gpi_overall != null ? lat.gpi_overall.toFixed(0) : '--';
        const wr = lat.win_rate != null ? parseFloat(lat.win_rate).toFixed(1) + '%' : '--';
        const kda = lat.kda != null ? parseFloat(lat.kda).toFixed(2) : '--';
        const timeStr = lastRefreshed ? new Date(lastRefreshed).toLocaleString() : 'Never';

        return `
        <div class="wl-card fade-in" data-name="${s.name}" data-region="${s.region}" data-slug="${s.slug}">
            <div class="flex items-center justify-between mb-3">
                <div class="flex items-center gap-2">
                    <span class="wl-status-dot ${statusClass}" title="${statusTitle}"></span>
                    <div>
                        <div class="text-sm font-medium text-gray-100">${s.name}</div>
                        <div class="text-xs text-gray-500">${s.region.replace('1','').toUpperCase()} &middot; ${s.snapshot_mode}</div>
                    </div>
                </div>
                <div class="flex gap-1">
                    <button class="btn-secondary wl-btn-sm" onclick="refreshWatchlistSummoner('${s.name}','${s.region}')" title="Refresh">
                        <i data-lucide="refresh-cw" class="w-3 h-3"></i>
                    </button>
                    <button class="btn-secondary wl-btn-sm wl-btn-danger" onclick="removeWatchlistSummoner('${s.name}','${s.region}')" title="Remove">
                        <i data-lucide="x" class="w-3 h-3"></i>
                    </button>
                </div>
            </div>
            <div class="grid grid-cols-3 gap-2 text-center">
                <div class="stat-card">
                    <div class="label">GPI</div>
                    <div class="value text-sm text-blue-400">${gpi}</div>
                </div>
                <div class="stat-card">
                    <div class="label">WR</div>
                    <div class="value text-sm">${wr}</div>
                </div>
                <div class="stat-card">
                    <div class="label">KDA</div>
                    <div class="value text-sm">${kda}</div>
                </div>
            </div>
            <div class="flex items-center justify-between mt-3">
                <span class="text-xs text-gray-600">${timeStr}</span>
                <button class="text-xs text-blue-400 hover:text-blue-300" onclick="showWatchlistHistory('${s.slug}','${s.name}')">History</button>
            </div>
        </div>`;
    }).join('');

    if (typeof lucide !== 'undefined') lucide.createIcons();
}

window.refreshWatchlistSummoner = async function(name, region) {
    showToast('Refreshing ' + name + '...', 'success');
    try {
        const resp = await fetch('/api/watchlist/refresh', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, region })
        });
        if (!resp.ok) throw new Error('Refresh failed');
        showToast(name + ' refreshed', 'success');
        await loadWatchlist();
    } catch (err) {
        showToast('Refresh failed: ' + err.message, 'error');
    }
};

window.removeWatchlistSummoner = async function(name, region) {
    try {
        const resp = await fetch('/api/watchlist/remove', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, region })
        });
        if (!resp.ok) throw new Error('Remove failed');
        showToast(name + ' removed', 'success');
        await loadWatchlist();
    } catch (err) {
        showToast('Remove failed: ' + err.message, 'error');
    }
};

window.showWatchlistHistory = async function(slug, name) {
    const panel = document.getElementById('watchlistHistory');
    const content = document.getElementById('wlHistoryContent');
    document.getElementById('wlHistoryName').textContent = name;
    panel.classList.remove('hidden');
    content.innerHTML = '<p class="text-gray-500 text-sm">Loading...</p>';

    try {
        const resp = await fetch(`/api/watchlist/history/${encodeURIComponent(slug)}`);
        if (!resp.ok) throw new Error('Failed to load history');
        const data = await resp.json();
        const history = data.history || [];

        if (!history.length) {
            content.innerHTML = '<p class="text-gray-500 text-sm">No snapshots yet.</p>';
            return;
        }

        content.innerHTML = `
            <table class="w-full text-sm">
                <thead>
                    <tr class="text-left text-xs text-gray-400 uppercase tracking-wider">
                        <th class="p-2">Date</th>
                        <th class="p-2">GPI</th>
                        <th class="p-2">Win Rate</th>
                        <th class="p-2">KDA</th>
                    </tr>
                </thead>
                <tbody>
                    ${history.map(h => `
                        <tr class="border-t border-gray-800/50 hover:bg-gray-800/30">
                            <td class="p-2 text-xs">${h.date}</td>
                            <td class="p-2 text-blue-400 font-mono">${h.gpi_overall != null ? h.gpi_overall.toFixed(0) : '--'}</td>
                            <td class="p-2 font-mono">${h.win_rate != null ? parseFloat(h.win_rate).toFixed(1) + '%' : '--'}</td>
                            <td class="p-2 font-mono">${h.kda != null ? parseFloat(h.kda).toFixed(2) : '--'}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>`;
    } catch (err) {
        content.innerHTML = `<p class="text-red-400 text-sm">${err.message}</p>`;
    }
};

// Wire up watchlist forms after DOM ready
document.addEventListener('DOMContentLoaded', () => {
    // Load watchlist when tab is clicked
    document.getElementById('tabWatchlist')?.addEventListener('click', () => {
        if (!watchlistLoaded) {
            watchlistLoaded = true;
            loadWatchlist();
        }
    });

    // Add summoner form
    document.getElementById('watchlistAddForm')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const name = document.getElementById('wlSummonerName').value.trim();
        const region = document.getElementById('wlRegion').value;
        const matchCount = parseInt(document.getElementById('wlMatchCount').value);
        const snapshotMode = document.getElementById('wlSnapshotMode').value;

        if (!name) return;

        try {
            const resp = await fetch('/api/watchlist/add', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, region, match_count: matchCount, snapshot_mode: snapshotMode })
            });
            if (!resp.ok) {
                const err = await resp.json().catch(() => ({}));
                throw new Error(err.detail || 'Failed to add');
            }
            document.getElementById('wlSummonerName').value = '';
            showToast(name + ' added — refreshing in background', 'success');
            await loadWatchlist();
        } catch (err) {
            showToast(err.message, 'error');
        }
    });

    // Schedule form
    document.getElementById('watchlistScheduleForm')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const enabled = document.getElementById('wlSchedEnabled').checked;
        const time = document.getElementById('wlSchedTime').value;
        const tz = document.getElementById('wlSchedTz').value;

        try {
            const resp = await fetch('/api/watchlist/schedule', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ enabled, time, timezone: tz })
            });
            if (!resp.ok) throw new Error('Failed to save schedule');
            showToast('Schedule saved', 'success');
        } catch (err) {
            showToast(err.message, 'error');
        }
    });

    // Refresh All button
    document.getElementById('wlRefreshAllBtn')?.addEventListener('click', async () => {
        showToast('Refreshing all summoners...', 'success');
        try {
            const resp = await fetch('/api/watchlist/refresh', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({})
            });
            if (!resp.ok) throw new Error('Refresh failed');
            showToast('All summoners refreshed', 'success');
            await loadWatchlist();
        } catch (err) {
            showToast('Refresh failed: ' + err.message, 'error');
        }
    });

    // History close
    document.getElementById('wlHistoryClose')?.addEventListener('click', () => {
        document.getElementById('watchlistHistory').classList.add('hidden');
    });
});
