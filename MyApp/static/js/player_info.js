// player_info.js
// Requires Chart.js to be loaded in the template


document.addEventListener('DOMContentLoaded', function() {
    setupEloChart();
    setupMatchSearch();
    setupProjectedPointsButton();
});

function setupEloChart() {
    console.log('Elo Data:', window.eloData);
    const eloDataElem = document.getElementById('eloChart');
    const fallbackElem = document.getElementById('eloChartFallback');
    if (typeof Chart === 'undefined') {
        console.error('Chart.js is not available. Ensure the CDN script is loading.');
        if (eloDataElem) eloDataElem.style.display = 'none';
        if (fallbackElem) {
            fallbackElem.textContent = 'Chart library failed to load. Please refresh or check your network.';
            fallbackElem.style.display = '';
        }
        return;
    }
    if (eloDataElem && window.eloData && Array.isArray(window.eloData.dates) && window.eloData.dates.length > 0) {
        if (fallbackElem) fallbackElem.style.display = 'none';
        eloDataElem.style.display = '';
        const ctx = eloDataElem.getContext('2d');
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: window.eloData.dates,
                datasets: [{
                    label: 'Elo Rating',
                    data: window.eloData.elos,
                    borderColor: 'rgb(75, 192, 192)',
                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 4,
                    pointHoverRadius: 6
                }]
            },
            options: {
                responsive: true,
                interaction: {
                    intersect: false,
                    mode: 'nearest',
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    title: {
                        display: true,
                        text: window.playerName + ' - Elo Rating Progression'
                    },
                    tooltip: {
                        enabled: true,
                        callbacks: {
                            label: function(context) {
                                const date = context.label;
                                const elo = context.parsed.y;
                                return `Date: ${date} | Elo: ${elo}`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        display: true,
                        title: {
                            display: true,
                            text: 'Match Date'
                        }
                    },
                    y: {
                        display: true,
                        title: {
                            display: true,
                            text: 'Elo Rating'
                        }
                    }
                }
            }
        });
    } else if (eloDataElem && fallbackElem) {
        eloDataElem.style.display = 'none';
        fallbackElem.style.display = '';
    }
}

function setupMatchSearch() {
    const matchSearch = document.getElementById('matchSearch');
    if (matchSearch) {
        matchSearch.addEventListener('keyup', function() {
            const searchTerm = this.value.toLowerCase();
            const tableRows = document.querySelectorAll('#matchesTable tbody tr');
            tableRows.forEach(row => {
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(searchTerm) ? '' : 'none';
            });
        });
    }
}

function setupProjectedPointsButton() {
    const loadProjectedBtn = document.getElementById('load-projected-btn');
    if (loadProjectedBtn) {
        loadProjectedBtn.addEventListener('click', function() {
            loadProjectedPoints();
        });
    }
}

let teamIdToName = null;

function loadProjectedPoints() {
    const loadingDiv = document.getElementById('projected-loading');
    const contentDiv = document.getElementById('projected-content');
    const btn = document.getElementById('load-projected-btn');
    // Get player name from the page
    const playerNameElement = document.querySelector('h1.h2');
    if (!playerNameElement) {
        console.error('Could not find player name element');
        return;
    }
    // Extract player name (remove team badge if present)
    const playerName = playerNameElement.textContent.trim().split('\n')[0].trim();
    // Show loading state
    loadingDiv.style.display = 'block';
    contentDiv.innerHTML = '';
    btn.disabled = true;

    // Fetch team map if not already loaded
    const fetchTeamMap = teamIdToName ? Promise.resolve(teamIdToName) : fetch('/api/team_map/').then(r => r.json());
    fetchTeamMap.then(map => {
        teamIdToName = map;
        fetch(`/api/projected_points/${encodeURIComponent(playerName)}/`)
            .then(response => response.json())
            .then(data => {
                loadingDiv.style.display = 'none';
                btn.disabled = false;
                if (data.success) {
                    displayProjectedPoints(data, teamIdToName);
                } else {
                    contentDiv.innerHTML = `
                        <div class="alert alert-warning">
                            <strong>No projected points available.</strong><br>
                            ${data.error || 'Click "Calculate Projected Points" in Data Manager to generate projections.'}
                        </div>
                    `;
                }
            })
            .catch(error => {
                console.error('Error loading projected points:', error);
                loadingDiv.style.display = 'none';
                btn.disabled = false;
                contentDiv.innerHTML = `
                    <div class="alert alert-danger">
                        <strong>Error loading projected points.</strong><br>
                        Please try again later.
                    </div>
                `;
            });
    });
}

function displayProjectedPoints(data, teamIdToName) {
    const contentDiv = document.getElementById('projected-content');
    
    if (data.games_projected === 0) {
        contentDiv.innerHTML = `
            <div class="alert alert-info">
                <strong>No projections available.</strong><br>
                Use the Data Manager to calculate projected points for all players.
            </div>
        `;
        return;
    }
    
    let html = `
        <div class="row mb-3">
            <div class="col-md-4">
                <div class="card text-center bg-primary text-white">
                    <div class="card-body">
                        <h5 class="card-title">Total Projected</h5>
                        <h3 class="card-text">${data.total_projected_points}</h3>
                        <small>Next ${data.games_projected} games</small>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card text-center bg-success text-white">
                    <div class="card-body">
                        <h5 class="card-title">Average per Game</h5>
                        <h3 class="card-text">${(data.total_projected_points / data.games_projected).toFixed(1)}</h3>
                        <small>Expected points</small>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card text-center bg-info text-white">
                    <div class="card-body">
                        <h5 class="card-title">Games Projected</h5>
                        <h3 class="card-text">${data.games_projected}</h3>
                        <small>Upcoming fixtures</small>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="table-responsive">
            <table class="table table-striped">
                <thead>
                    <tr>
                        <th>Gameweek</th>
                        <th>Opponent</th>
                        <th>Venue</th>
                        <th>Difficulty</th>
                        <th>Expected Points</th>
                        <th>Adjusted Points</th>
                    </tr>
                </thead>
                <tbody>
    `;
    
    data.projections.forEach(projection => {
        const venue = projection.is_home ? 'Home' : 'Away';
        const venueIcon = projection.is_home ? 'fa-home' : 'fa-plane';
        const difficultyColor = getDifficultyColor(projection.difficulty);
        // Round points to 1 decimal place
        const expectedPoints = Number(projection.expected_points).toFixed(1);
        const adjustedPoints = Number(projection.adjusted_points).toFixed(1);
        let opponentName = projection.opponent;
        if (teamIdToName && teamIdToName[opponentName]) {
            opponentName = teamIdToName[opponentName];
        }
        html += `
            <tr>
                <td><strong>GW${projection.gameweek}</strong></td>
                <td>${opponentName}</td>
                <td><i class="fas ${venueIcon}"></i> ${venue}</td>
                <td><span class="badge ${difficultyColor}">${projection.difficulty}</span></td>
                <td>${expectedPoints}</td>
                <td><strong>${adjustedPoints}</strong></td>
            </tr>
        `;
    });
    
    html += `
                </tbody>
            </table>
        </div>
        <small class="text-muted">
            <i class="fas fa-info-circle"></i> 
            Projected points use the same ELO formula as the rating calculator, adjusted for fixture difficulty.
        </small>
    `;
    
    contentDiv.innerHTML = html;
}

function getDifficultyColor(difficulty) {
    switch(difficulty) {
        case 1: return 'bg-success'; // Very easy
        case 2: return 'bg-info';    // Easy
        case 3: return 'bg-warning'; // Average
        case 4: return 'bg-warning text-dark'; // Hard
        case 5: return 'bg-danger';  // Very hard
        default: return 'bg-secondary';
    }
}
