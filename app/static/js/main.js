document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('summonerForm');
    const loading = document.getElementById('loading');
    const results = document.getElementById('results');
    const error = document.getElementById('error');
    const overallStats = document.getElementById('overallStats');
    const matchList = document.getElementById('matchList');
    const matchDetails = document.getElementById('matchDetails');
    const matchStats = document.getElementById('matchStats');
    const championStatsBody = document.getElementById('championStatsBody');

    // Set default summoner
    const defaultSummoner = "aphae#raph";
    const defaultRegion = "na1";
    
    // Set default values in the form
    document.getElementById('summonerName').value = defaultSummoner;
    document.getElementById('region').value = defaultRegion;

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const summonerName = document.getElementById('summonerName').value;
        const region = document.getElementById('region').value;

        try {
            loading.classList.remove('hidden');
            results.classList.add('hidden');
            error.classList.add('hidden');
            matchDetails.classList.add('hidden');

            const response = await fetch('/api/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    summoner_name: summonerName,
                    region: region,
                    match_count: 20
                }),
            });

            if (!response.ok) {
                throw new Error('Failed to fetch stats');
            }

            const data = await response.json();
            displayOverallStats(data.overall_stats);
            displayMatchList(data.match_analyses);
            displayChampionStats(data.champion_stats);

            results.classList.remove('hidden');
        } catch (err) {
            error.textContent = err.message;
            error.classList.remove('hidden');
        } finally {
            loading.classList.add('hidden');
        }
    });

    function displayOverallStats(stats) {
        if (!stats) return;

        const safeStats = {
            win_rate: parseFloat(stats.win_rate) || 0,
            kda: parseFloat(stats.kda) || 0,
            total_matches: parseInt(stats.total_matches) || 0,
            vision_score: parseInt(stats.vision_score) || 0
        };

        overallStats.innerHTML = `
            <div class="stat-card">
                <h3>Win Rate</h3>
                <p>${safeStats.win_rate.toFixed(1)}%</p>
            </div>
            <div class="stat-card">
                <h3>KDA</h3>
                <p>${safeStats.kda.toFixed(2)}</p>
            </div>
            <div class="stat-card">
                <h3>Matches</h3>
                <p>${safeStats.total_matches}</p>
            </div>
            <div class="stat-card">
                <h3>Vision</h3>
                <p>${safeStats.vision_score}</p>
            </div>
        `;
    }

    function displayMatchList(matches) {
        if (!matches || !Array.isArray(matches)) return;

        window.matchData = matches;

        matchList.innerHTML = matches.map((match, idx) => {
            const safeMatch = {
                match_id: match.match_id || '',
                champion: match.champion || 'Unknown',
                position: match.position || 'Unknown',
                win: Boolean(match.win),
                kills: parseInt(match.kills) || 0,
                deaths: parseInt(match.deaths) || 0,
                assists: parseInt(match.assists) || 0,
                kda: parseFloat(match.kda) || 0,
                damage_dealt: parseInt(match.damage_dealt) || 0,
                damage_taken: parseInt(match.damage_taken) || 0,
                gold_earned: parseInt(match.gold_earned) || 0,
                vision_score: parseInt(match.vision_score) || 0
            };

            const dropdownId = `match-details-${idx}`;

            return `
                <div class="match-card" onclick="toggleMatchDropdown('${dropdownId}')">
                    <div class="flex items-center justify-between">
                        <div class="flex items-center space-x-4">
                            <img src="https://ddragon.leagueoflegends.com/cdn/13.24.1/img/champion/${safeMatch.champion}.png"
                                 alt="${safeMatch.champion}"
                                 class="champion-icon">
                            <div>
                                <h3 class="font-medium text-gray-200">${safeMatch.champion}</h3>
                                <p class="text-sm text-gray-500">${safeMatch.position}</p>
                            </div>
                        </div>
                        <div class="text-right">
                            <div class="win-indicator ${safeMatch.win ? 'win' : 'loss'}">
                                ${safeMatch.win ? 'Victory' : 'Defeat'}
                            </div>
                            <p class="text-sm text-gray-500">
                                ${safeMatch.kills}/${safeMatch.deaths}/${safeMatch.assists}
                            </p>
                        </div>
                    </div>
                    <div id="${dropdownId}" class="hidden mt-4 bg-gray-900/50 rounded p-4 border border-gray-800">
                        <div class="grid grid-cols-2 gap-4 text-sm">
                            <div>
                                <p class="text-gray-500">KDA</p>
                                <p class="font-mono text-gray-200">${safeMatch.kda.toFixed(2)}</p>
                            </div>
                            <div>
                                <p class="text-gray-500">Damage</p>
                                <p class="font-mono text-gray-200">${safeMatch.damage_dealt.toLocaleString()}</p>
                            </div>
                            <div>
                                <p class="text-gray-500">Gold</p>
                                <p class="font-mono text-gray-200">${safeMatch.gold_earned.toLocaleString()}</p>
                            </div>
                            <div>
                                <p class="text-gray-500">Vision</p>
                                <p class="font-mono text-gray-200">${safeMatch.vision_score}</p>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    }

    function displayChampionStats(stats) {
        if (!stats) return;

        championStatsBody.innerHTML = Object.entries(stats)
            .sort((a, b) => b[1].games_played - a[1].games_played) // Sort by games played
            .map(([champion, data]) => `
                <tr class="border-t border-gray-800 hover:bg-gray-800/50">
                    <td class="p-2">
                        <div class="flex items-center space-x-2">
                            <img src="https://ddragon.leagueoflegends.com/cdn/13.24.1/img/champion/${champion}.png"
                                 alt="${champion}"
                                 class="w-8 h-8 rounded">
                            <span class="text-gray-200">${champion}</span>
                        </div>
                    </td>
                    <td class="p-2 text-gray-200">${data.games_played}</td>
                    <td class="p-2 text-gray-200">${data.win_rate.toFixed(1)}%</td>
                    <td class="p-2 text-gray-200">${data.kda.toFixed(2)}</td>
                    <td class="p-2 text-gray-200">${data.avg_kills.toFixed(1)}</td>
                    <td class="p-2 text-gray-200">${data.avg_deaths.toFixed(1)}</td>
                    <td class="p-2 text-gray-200">${data.avg_assists.toFixed(1)}</td>
                    <td class="p-2 text-gray-200">${Math.round(data.avg_damage).toLocaleString()}</td>
                    <td class="p-2 text-gray-200">${Math.round(data.avg_gold).toLocaleString()}</td>
                    <td class="p-2 text-gray-200">${Math.round(data.avg_vision)}</td>
                </tr>
            `).join('');
    }

    window.toggleMatchDropdown = function(dropdownId) {
        const el = document.getElementById(dropdownId);
        if (el) {
            el.classList.toggle('hidden');
        }
    };
}); 