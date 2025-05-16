document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('summonerForm');
    const loading = document.getElementById('loading');
    const results = document.getElementById('results');
    const error = document.getElementById('error');
    const overallStats = document.getElementById('overallStats');
    const matchList = document.getElementById('matchList');
    const matchDetails = document.getElementById('matchDetails');
    const performanceScore = document.getElementById('performanceScore');
    const matchStats = document.getElementById('matchStats');
    const improvementSuggestions = document.getElementById('improvementSuggestions');
    const debugPanel = document.getElementById('debugPanel');
    const debugToggle = document.getElementById('debugToggle');
    const debugLogs = document.getElementById('debugLogs');
    const clearLogs = document.getElementById('clearLogs');

    // Set default summoner
    const defaultSummoner = "aphae#raph";
    const defaultRegion = "na1";
    
    // Set default values in the form
    document.getElementById('summonerName').value = defaultSummoner;
    document.getElementById('region').value = defaultRegion;

    // Debug panel functionality
    debugToggle.addEventListener('click', () => {
        console.log('Debug panel toggle clicked');
        debugPanel.classList.toggle('translate-x-full');
    });

    clearLogs.addEventListener('click', () => {
        console.log('Clear logs clicked');
        debugLogs.innerHTML = '';
    });

    // Function to add a log entry to the debug panel
    function addDebugLog(log) {
        console.log('Adding debug log:', log);
        const logEntry = document.createElement('div');
        logEntry.className = `p-4 rounded-lg ${getLogLevelClass(log.level)}`;
        
        const timestamp = new Date(log.timestamp).toLocaleTimeString();
        
        let content = `
            <div class="flex justify-between items-start mb-2">
                <span class="font-medium">${log.level}</span>
                <span class="text-sm text-gray-400">${timestamp}</span>
            </div>
            <p class="text-sm mb-2">${log.message}</p>
        `;

        if (log.code_context) {
            content += `
                <div class="bg-gray-700 p-2 rounded text-sm font-mono mb-2">
                    <div class="text-gray-400">${log.code_context.filename}:${log.code_context.line_number}</div>
                    <div class="text-gray-300">${log.code_context.function}</div>
                    <div class="text-blue-400">${log.code_context.code}</div>
                </div>
            `;
        }

        if (log.traceback) {
            content += `
                <div class="bg-gray-700 p-2 rounded text-sm font-mono overflow-x-auto">
                    <pre class="text-red-400">${log.traceback}</pre>
                </div>
            `;
        }

        logEntry.innerHTML = content;
        debugLogs.insertBefore(logEntry, debugLogs.firstChild);
    }

    function getLogLevelClass(level) {
        switch (level.toLowerCase()) {
            case 'error':
                return 'bg-red-900/50 border border-red-700';
            case 'warning':
                return 'bg-yellow-900/50 border border-yellow-700';
            case 'info':
                return 'bg-blue-900/50 border border-blue-700';
            default:
                return 'bg-gray-700';
        }
    }

    // Function to fetch and display debug logs
    async function fetchDebugLogs() {
        try {
            console.log('Fetching debug logs...');
            const response = await fetch('/api/debug-logs');
            if (!response.ok) {
                console.error('Failed to fetch debug logs:', response.status, response.statusText);
                throw new Error('Failed to fetch debug logs');
            }
            
            const data = await response.json();
            console.log('Received debug logs:', data);
            
            // Clear existing logs before adding new ones
            debugLogs.innerHTML = '';
            
            // Add each log entry
            data.logs.forEach(log => {
                console.log('Adding log entry:', log);
                addDebugLog(log);
            });
        } catch (err) {
            console.error('Error fetching debug logs:', err);
        }
    }

    // Fetch debug logs immediately and then periodically
    fetchDebugLogs();
    setInterval(fetchDebugLogs, 2000);

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const summonerName = document.getElementById('summonerName').value;
        const region = document.getElementById('region').value;

        console.log('Submitting form with:', { summonerName, region });

        // Show loading state
        loading.classList.remove('hidden');
        results.classList.add('hidden');
        error.classList.add('hidden');
        matchDetails.classList.add('hidden');

        try {
            console.log('Making API request...');
            const response = await fetch('/api/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    summoner_name: summonerName,
                    region: region
                })
            });

            if (!response.ok) {
                console.error('API request failed:', response.status, response.statusText);
                throw new Error('Failed to fetch summoner data');
            }

            const data = await response.json();
            console.log('Received API response:', data);
            displayResults(data);
        } catch (err) {
            console.error('Error in form submission:', err);
            showError(err.message);
        } finally {
            loading.classList.add('hidden');
        }
    });

    function displayResults(data) {
        console.log('Displaying results:', data);
        results.classList.remove('hidden');
        
        // Display overall stats
        displayOverallStats(data.overall_stats);
        
        // Display match list
        displayMatchList(data.match_analyses);
    }

    function displayOverallStats(stats) {
        console.log('Displaying overall stats:', stats);
        if (!stats) {
            console.error('No stats provided to displayOverallStats');
            return;
        }

        // Ensure all numeric values are properly initialized
        const safeStats = {
            win_rate: parseFloat(stats.win_rate) || 0,
            kda: parseFloat(stats.kda) || 0,
            total_matches: parseInt(stats.total_matches) || 0,
            vision_score: parseInt(stats.vision_score) || 0
        };

        console.log('Safe stats:', safeStats);

        overallStats.innerHTML = `
            <div class="stat-card bg-gray-700 p-4 rounded-lg">
                <h3 class="text-sm font-medium text-gray-400">Win Rate</h3>
                <p class="text-2xl font-bold text-white">${safeStats.win_rate.toFixed(1)}%</p>
            </div>
            <div class="stat-card bg-gray-700 p-4 rounded-lg">
                <h3 class="text-sm font-medium text-gray-400">KDA</h3>
                <p class="text-2xl font-bold text-white">${safeStats.kda.toFixed(2)}</p>
            </div>
            <div class="stat-card bg-gray-700 p-4 rounded-lg">
                <h3 class="text-sm font-medium text-gray-400">Total Matches</h3>
                <p class="text-2xl font-bold text-white">${safeStats.total_matches}</p>
            </div>
            <div class="stat-card bg-gray-700 p-4 rounded-lg">
                <h3 class="text-sm font-medium text-gray-400">Vision Score</h3>
                <p class="text-2xl font-bold text-white">${safeStats.vision_score}</p>
            </div>
        `;
    }

    function displayMatchList(matches) {
        console.log('Displaying match list:', matches);
        if (!matches || !Array.isArray(matches)) {
            console.error('Invalid matches data:', matches);
            return;
        }

        // Store match data globally for details
        window.matchData = matches;

        matchList.innerHTML = matches.map((match, idx) => {
            // Ensure all numeric values are properly initialized
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
                vision_score: parseInt(match.vision_score) || 0,
                time_ccing_others: parseInt(match.time_ccing_others) || 0,
                analysis: match.analysis || '',
                improvement_suggestions: match.improvement_suggestions || [],
            };

            // Dropdown content (hidden by default)
            const dropdownId = `match-details-${idx}`;
            const suggestions = safeMatch.improvement_suggestions.length
                ? `<ul class='list-disc pl-5'>${safeMatch.improvement_suggestions.map(s => `<li>${s}</li>`).join('')}</ul>`
                : '<span class="text-gray-400">No suggestions available.</span>';

            return `
                <div class="match-card bg-gray-700 p-4 rounded-lg cursor-pointer transition-all mb-2" onclick="toggleMatchDropdown('${dropdownId}')">
                    <div class="flex items-center justify-between">
                        <div class="flex items-center space-x-4">
                            <img src="https://ddragon.leagueoflegends.com/cdn/13.24.1/img/champion/${safeMatch.champion}.png"
                                 alt="${safeMatch.champion}"
                                 class="w-12 h-12 rounded-full champion-icon">
                            <div>
                                <h3 class="font-medium">${safeMatch.champion}</h3>
                                <p class="text-sm text-gray-400">${safeMatch.position}</p>
                            </div>
                        </div>
                        <div class="text-right">
                            <div class="win-indicator ${safeMatch.win ? 'win' : 'loss'}">
                                ${safeMatch.win ? '<span class="text-green-400">Victory</span>' : '<span class="text-red-400">Defeat</span>'}
                            </div>
                            <p class="text-sm text-gray-400">
                                ${safeMatch.kills}/${safeMatch.deaths}/${safeMatch.assists}
                            </p>
                        </div>
                    </div>
                    <div id="${dropdownId}" class="hidden mt-4 bg-gray-800 rounded p-4">
                        <div class="mb-2">
                            <span class="font-semibold text-blue-400">Analysis:</span>
                            <span>${safeMatch.analysis || 'No analysis available.'}</span>
                        </div>
                        <div class="mb-2">
                            <span class="font-semibold text-blue-400">Stats:</span>
                            <ul class="grid grid-cols-2 gap-2 text-sm mt-2">
                                <li>KDA: <span class="font-mono">${safeMatch.kda.toFixed(2)}</span></li>
                                <li>Damage Dealt: <span class="font-mono">${safeMatch.damage_dealt.toLocaleString()}</span></li>
                                <li>Damage Taken: <span class="font-mono">${safeMatch.damage_taken.toLocaleString()}</span></li>
                                <li>Gold Earned: <span class="font-mono">${safeMatch.gold_earned.toLocaleString()}</span></li>
                                <li>Vision Score: <span class="font-mono">${safeMatch.vision_score}</span></li>
                                <li>Time CCing Others: <span class="font-mono">${safeMatch.time_ccing_others}s</span></li>
                            </ul>
                        </div>
                        <div>
                            <span class="font-semibold text-blue-400">Suggestions:</span>
                            ${suggestions}
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    }

    // Add dropdown toggle function globally
    window.toggleMatchDropdown = function(dropdownId) {
        const el = document.getElementById(dropdownId);
        if (el) {
            el.classList.toggle('hidden');
        }
    };

    function showMatchDetails(matchId) {
        console.log('Showing match details for:', matchId);
        const match = window.matchData.find(m => m.match_id === matchId);
        if (!match) {
            console.error('Match not found:', matchId);
            return;
        }

        console.log('Match data:', match);
        matchDetails.classList.remove('hidden');
        
        // Ensure all numeric values are properly initialized
        const safeMatch = {
            kda: parseFloat(match.kda) || 0,
            damage_dealt: parseInt(match.damage_dealt) || 0,
            damage_taken: parseInt(match.damage_taken) || 0,
            gold_earned: parseInt(match.gold_earned) || 0,
            vision_score: parseInt(match.vision_score) || 0,
            time_ccing_others: parseInt(match.time_ccing_others) || 0
        };

        console.log('Safe match data for details:', safeMatch);

        // Display match stats
        matchStats.innerHTML = `
            <div class="space-y-4">
                <h3 class="text-lg font-medium text-blue-500">Basic Stats</h3>
                <div class="grid grid-cols-2 gap-4">
                    <div class="bg-gray-700 p-3 rounded">
                        <p class="text-sm text-gray-400">KDA</p>
                        <p class="text-lg font-medium">${safeMatch.kda.toFixed(2)}</p>
                    </div>
                    <div class="bg-gray-700 p-3 rounded">
                        <p class="text-sm text-gray-400">Damage Dealt</p>
                        <p class="text-lg font-medium">${safeMatch.damage_dealt.toLocaleString()}</p>
                    </div>
                    <div class="bg-gray-700 p-3 rounded">
                        <p class="text-sm text-gray-400">Damage Taken</p>
                        <p class="text-lg font-medium">${safeMatch.damage_taken.toLocaleString()}</p>
                    </div>
                    <div class="bg-gray-700 p-3 rounded">
                        <p class="text-sm text-gray-400">Gold Earned</p>
                        <p class="text-lg font-medium">${safeMatch.gold_earned.toLocaleString()}</p>
                    </div>
                </div>
            </div>
            <div class="space-y-4">
                <h3 class="text-lg font-medium text-blue-500">Vision Stats</h3>
                <div class="grid grid-cols-2 gap-4">
                    <div class="bg-gray-700 p-3 rounded">
                        <p class="text-sm text-gray-400">Vision Score</p>
                        <p class="text-lg font-medium">${safeMatch.vision_score}</p>
                    </div>
                    <div class="bg-gray-700 p-3 rounded">
                        <p class="text-sm text-gray-400">Time CCing Others</p>
                        <p class="text-lg font-medium">${safeMatch.time_ccing_others}s</p>
                    </div>
                </div>
            </div>
        `;

        // Store match data for later use
        window.matchData = window.matchData || [];
        window.matchData.push(match);
    }

    function showError(message) {
        console.error('Showing error:', message);
        error.textContent = message;
        error.classList.remove('hidden');
    }

    // Make match data available globally
    window.matchData = [];
    window.showMatchDetails = showMatchDetails;

    // Auto-submit the form with default values
    console.log('Auto-submitting form with default values');
    form.dispatchEvent(new Event('submit'));
}); 