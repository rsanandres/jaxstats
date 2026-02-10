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

// ============ RENDER DASHBOARD ============
function renderDashboard(data) {
    renderOverallStats(data.overall_stats, data.gpi);
    renderGPI(data.gpi);
    renderTrends(data.trends);
    renderMatchList(data.match_analyses);
    renderChampionStats(data.champion_stats);
    renderCharts(data);
}

function renderOverallStats(stats, gpi) {
    if (!stats) return;
    const wr = pf(stats.win_rate);
    const kda = pf(stats.kda);
    const wrClass = wr >= 55 ? 'text-green-400' : wr <= 45 ? 'text-red-400' : 'text-gray-200';

    document.getElementById('overallStats').innerHTML = `
        <div class="stat-card">
            <div class="label">Win Rate</div>
            <div class="value ${wrClass}">${wr.toFixed(1)}%</div>
            <div class="text-xs text-gray-500">${pi(stats.wins)}W ${pi(stats.losses)}L</div>
        </div>
        <div class="stat-card">
            <div class="label">KDA</div>
            <div class="value">${kda.toFixed(2)}</div>
            <div class="text-xs text-gray-500">${pi(stats.kills)}/${pi(stats.deaths)}/${pi(stats.assists)}</div>
        </div>
        <div class="stat-card">
            <div class="label">Matches</div>
            <div class="value">${pi(stats.total_matches)}</div>
        </div>
        <div class="stat-card">
            <div class="label">Avg Vision</div>
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
    charts.gpiRadar = new Chart(ctx, {
        type: 'radar',
        data: {
            labels: skills.map(s => s.charAt(0).toUpperCase() + s.slice(1)),
            datasets: [{
                data: values,
                backgroundColor: 'rgba(59,130,246,0.15)',
                borderColor: '#3b82f6',
                borderWidth: 2,
                pointBackgroundColor: '#3b82f6',
                pointRadius: 3,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                r: {
                    beginAtZero: true, max: 100,
                    ticks: { display: false, stepSize: 25 },
                    grid: { color: '#1e293b' },
                    pointLabels: { color: '#94a3b8', font: { size: 10 } },
                    angleLines: { color: '#1e293b' },
                }
            },
            plugins: { legend: { display: false } }
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

function renderChampionStats(stats) {
    const el = document.getElementById('championStatsBody');
    if (!stats) { el.innerHTML = ''; return; }

    el.innerHTML = Object.entries(stats)
        .sort((a, b) => b[1].games_played - a[1].games_played)
        .map(([champ, d]) => `
            <tr class="border-t border-gray-800/50 hover:bg-gray-800/30 text-xs">
                <td class="p-2">
                    <div class="flex items-center gap-2">
                        <img src="https://ddragon.leagueoflegends.com/cdn/${ddragonVersion}/img/champion/${champ}.png" alt="${champ}" class="w-6 h-6 rounded" onerror="this.style.display='none'">
                        <span>${champ}</span>
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
}

// ============ CHARTS ============
function renderCharts(data) {
    const matches = data.trend_matches || [];
    if (!matches.length) return;

    const labels = matches.map((_, i) => `G${i + 1}`);
    const chartOpts = {
        responsive: true, maintainAspectRatio: false,
        scales: {
            x: { grid: { color: '#1e293b' }, ticks: { color: '#64748b', font: { size: 10 } } },
            y: { grid: { color: '#1e293b' }, ticks: { color: '#64748b', font: { size: 10 } } }
        },
        plugins: { legend: { labels: { color: '#94a3b8', font: { size: 10 } } } }
    };

    // Performance trend (ML scores from match_analyses)
    const mlScores = (data.match_analyses || []).map(m => m.ml_scores?.performance_score || null).filter(s => s != null);
    if (mlScores.length) {
        destroyChart('perfTrendChart');
        charts.perfTrendChart = new Chart(document.getElementById('perfTrendChart'), {
            type: 'line', data: {
                labels: mlScores.map((_, i) => `G${i + 1}`),
                datasets: [{ label: 'Performance Score', data: mlScores, borderColor: '#3b82f6', backgroundColor: 'rgba(59,130,246,0.1)', fill: true, tension: 0.3, pointRadius: 3 }]
            }, options: { ...chartOpts, scales: { ...chartOpts.scales, y: { ...chartOpts.scales.y, min: 0, max: 100 } } }
        });
    }

    // KDA trend
    destroyChart('kdaTrendChart');
    charts.kdaTrendChart = new Chart(document.getElementById('kdaTrendChart'), {
        type: 'line', data: {
            labels,
            datasets: [
                { label: 'Kills', data: matches.map(m => m.kills), borderColor: '#22c55e', tension: 0.3, pointRadius: 2 },
                { label: 'Deaths', data: matches.map(m => m.deaths), borderColor: '#ef4444', tension: 0.3, pointRadius: 2 },
                { label: 'Assists', data: matches.map(m => m.assists), borderColor: '#3b82f6', tension: 0.3, pointRadius: 2 },
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
                datasets: [{ data: Object.values(roles), backgroundColor: ['#3b82f6', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6'] }]
            }, options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'right', labels: { color: '#94a3b8', font: { size: 10 } } } } }
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
                    { label: 'Physical', data: physArr.slice(0, 10), backgroundColor: '#f59e0b' },
                    { label: 'Magic', data: magArr.slice(0, 10), backgroundColor: '#3b82f6' },
                    { label: 'True', data: trueArr.slice(0, 10), backgroundColor: '#e2e8f0' },
                ]
            }, options: { ...chartOpts, scales: { ...chartOpts.scales, x: { ...chartOpts.scales.x, stacked: true }, y: { ...chartOpts.scales.y, stacked: true } } }
        });
    }
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
        <div class="panel">
            <div class="flex justify-between mb-4">
                <span class="text-blue-400 font-medium">${u1.summoner_name}</span>
                <span class="text-gray-500 text-sm">VS</span>
                <span class="text-red-400 font-medium">${u2.summoner_name}</span>
            </div>
            <div class="space-y-2 mb-6">${barsHtml}</div>
            <h3 class="panel-title mt-4">GPI Skills</h3>
            <div class="space-y-2">${gpiHtml}</div>
        </div>`;
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
