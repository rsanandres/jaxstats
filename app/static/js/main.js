document.addEventListener('DOMContentLoaded', () => {
    const tabStats = document.getElementById('tabStats');
    const tabCompare = document.getElementById('tabCompare');
    const results = document.getElementById('results');
    const compareTab = document.getElementById('compareTab');

    tabStats.addEventListener('click', () => {
        tabStats.classList.add('active');
        tabCompare.classList.remove('active');
        results.classList.remove('hidden');
        compareTab.classList.add('hidden');
    });

    tabCompare.addEventListener('click', () => {
        tabCompare.classList.add('active');
        tabStats.classList.remove('active');
        compareTab.classList.remove('hidden');
        results.classList.add('hidden');
    });

    // Existing form and fetch logic for single user stats
    const form = document.getElementById('summonerForm');
    const loading = document.getElementById('loading');
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

    // Add refresh button to the form
    const refreshButton = document.createElement('button');
    refreshButton.type = 'button';
    refreshButton.className = 'px-4 py-2 bg-gray-700 text-gray-200 rounded hover:bg-gray-600 transition-colors flex items-center space-x-2';
    refreshButton.innerHTML = `
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
        <span>Refresh Data</span>
    `;
    form.appendChild(refreshButton);

    // Add loading spinner component
    const loadingSpinner = document.createElement('div');
    loadingSpinner.className = 'hidden fixed bottom-4 right-4 bg-gray-800 rounded-lg shadow-lg p-4 flex items-center space-x-3';
    loadingSpinner.innerHTML = `
        <div class="animate-spin rounded-full h-5 w-5 border-b-2 border-gray-200"></div>
        <span class="text-gray-200">Updating data...</span>
    `;
    document.body.appendChild(loadingSpinner);

    let currentSummoner = defaultSummoner;
    let currentRegion = defaultRegion;
    let isRefreshing = false;

    async function fetchData(useCache = true) {
        if (isRefreshing) return;
        isRefreshing = true;

        try {
            // First request with cached data
            const response = await fetch('/api/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    summoner_name: currentSummoner,
                    region: currentRegion,
                    match_count: 20,
                    use_cache: true  // Always use cache first
                }),
            });

            if (!response.ok) {
                throw new Error('Failed to fetch stats');
            }

            const data = await response.json();
            
            // Show initial data from cache immediately
            displayOverallStats(data.overall_stats);
            displayMatchList(data.match_analyses);
            displayChampionStats(data.champion_stats);
            results.classList.remove('hidden');

            // If we're not using cache or have new matches to load, fetch fresh data in background
            if (!useCache || data.match_count.new > 0) {
                loadingSpinner.classList.remove('hidden');

                // Fetch fresh data in the background
                const freshResponse = await fetch(`/api/analyze/${currentSummoner}?region=${currentRegion}&match_count=20&use_cache=false`);
                if (freshResponse.ok) {
                    const freshData = await freshResponse.json();
                    
                    // Update UI with fresh data
                    displayOverallStats(freshData.overall_stats);
                    displayMatchList(freshData.match_analyses);
                    displayChampionStats(freshData.champion_stats);

                    // Show success message
                    const successMessage = document.createElement('div');
                    successMessage.className = 'fixed bottom-4 right-4 bg-green-800 text-gray-200 rounded-lg shadow-lg p-4 flex items-center space-x-3';
                    successMessage.innerHTML = `
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                        </svg>
                        <span>Data updated successfully</span>
                    `;
                    document.body.appendChild(successMessage);
                    setTimeout(() => successMessage.remove(), 3000);
                }
            }

        } catch (err) {
            error.textContent = err.message;
            error.classList.remove('hidden');
        } finally {
            loading.classList.add('hidden');
            loadingSpinner.classList.add('hidden');
            isRefreshing = false;
        }
    }

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        currentSummoner = document.getElementById('summonerName').value;
        currentRegion = document.getElementById('region').value;

        loading.classList.remove('hidden');
        results.classList.add('hidden');
        error.classList.add('hidden');
        matchDetails.classList.add('hidden');

        await fetchData(true);
    });

    refreshButton.addEventListener('click', async () => {
        await fetchData(false);
    });

    // New form and fetch logic for comparing two users
    const compareForm = document.createElement('form');
    compareForm.id = 'compareForm';
    compareForm.className = 'search-form';
    compareForm.innerHTML = `
        <div class="form-group">
            <label for="summoner1Name">Summoner 1 Name</label>
            <input type="text" id="summoner1Name" name="summoner1Name" required>
        </div>
        <div class="form-group">
            <label for="summoner1Region">Summoner 1 Region</label>
            <select id="summoner1Region" name="summoner1Region" required>
                <option value="na1">North America</option>
                <option value="euw1">Europe West</option>
                <option value="eun1">Europe Nordic</option>
                <option value="kr">Korea</option>
            </select>
        </div>
        <div class="form-group">
            <label for="summoner2Name">Summoner 2 Name</label>
            <input type="text" id="summoner2Name" name="summoner2Name" required>
        </div>
        <div class="form-group">
            <label for="summoner2Region">Summoner 2 Region</label>
            <select id="summoner2Region" name="summoner2Region" required>
                <option value="na1">North America</option>
                <option value="euw1">Europe West</option>
                <option value="eun1">Europe Nordic</option>
                <option value="kr">Korea</option>
            </select>
        </div>
        <button type="submit" class="btn w-full">Compare</button>
    `;
    compareTab.insertBefore(compareForm, compareTab.firstChild);

    compareForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const summoner1Name = document.getElementById('summoner1Name').value;
        const summoner1Region = document.getElementById('summoner1Region').value;
        const summoner2Name = document.getElementById('summoner2Name').value;
        const summoner2Region = document.getElementById('summoner2Region').value;

        try {
            loading.classList.remove('hidden');
            error.classList.add('hidden');

            const response = await fetch('/api/compare', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    summoner1_name: summoner1Name,
                    summoner1_region: summoner1Region,
                    summoner2_name: summoner2Name,
                    summoner2_region: summoner2Region,
                    match_count: 20
                }),
            });

            if (!response.ok) {
                throw new Error('Failed to fetch comparison');
            }

            const data = await response.json();
            displayComparison(data.user1, data.user2);
        } catch (err) {
            error.textContent = err.message;
            error.classList.remove('hidden');
        } finally {
            loading.classList.add('hidden');
        }
    });

    function displayComparison(user1, user2) {
        const user1Stats = document.getElementById('user1Stats');
        const user2Stats = document.getElementById('user2Stats');

        user1Stats.innerHTML = `
            <h3>${user1.summoner_name}</h3>
            <p>Level: ${user1.summoner_level}</p>
            <p>Win Rate: ${user1.overall_stats.win_rate.toFixed(1)}%</p>
            <p>KDA: ${user1.overall_stats.kda.toFixed(2)}</p>
            <p>Matches: ${user1.overall_stats.total_matches}</p>
            <p>Vision: ${user1.overall_stats.vision_score}</p>
        `;

        user2Stats.innerHTML = `
            <h3>${user2.summoner_name}</h3>
            <p>Level: ${user2.summoner_level}</p>
            <p>Win Rate: ${user2.overall_stats.win_rate.toFixed(1)}%</p>
            <p>KDA: ${user2.overall_stats.kda.toFixed(2)}</p>
            <p>Matches: ${user2.overall_stats.total_matches}</p>
            <p>Vision: ${user2.overall_stats.vision_score}</p>
        `;
    }

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