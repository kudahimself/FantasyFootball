// squad_points.js - Squad builder focused on projected points

let currentSquadNumber = 1;

document.addEventListener('DOMContentLoaded', function() {
    // Toggle event listener - redirect to ELO page
    const toggle = document.getElementById('selection-mode-toggle');
    if (toggle) {
        toggle.addEventListener('change', function() {
            if (!this.checked) {
                // Redirect to ELO squads page
                window.location.href = '/squad_elo/';
            }
        });
    }
    
    // Generate squads button (manual regeneration)
    const generateBtn = document.getElementById('btn-generate-squads');
    if (generateBtn) {
        generateBtn.addEventListener('click', generateAndDisplaySquads);
    }
    
    // Formation change listener
    const formationSelect = document.getElementById('formation-select');
    if (formationSelect) {
        formationSelect.addEventListener('change', () => {
            console.log('[Squad Points] Formation changed →', formationSelect.value);
            generateAndDisplaySquads();
        });
    }

    // Games-to-consider selector change listener
    const gamesSelect = document.getElementById('games-to-consider-select');
    if (gamesSelect) {
        gamesSelect.addEventListener('change', () => {
            console.log('[Squad Points] Games to consider changed →', gamesSelect.value);
            generateAndDisplaySquads();
        });
    }
});

// Auto-generate squads on page load
window.onload = function() {
    generateAndDisplaySquads();
};

function generateAndDisplaySquads() {
    const formationSelect = document.getElementById('formation-select');
    const gamesSelect = document.getElementById('games-to-consider-select');
    const formation = formationSelect && formationSelect.value ? formationSelect.value : '3-4-3';
    const gamesToConsider = gamesSelect && gamesSelect.value ? parseInt(gamesSelect.value) : 3;

    console.log("[Squad Points] Generating projected points squads for formation:", formation, "| Games to consider:", gamesToConsider);

    // Show loading state
    const btn = document.getElementById('btn-generate-squads');
    if (btn) {
        btn.disabled = true;
        btn.textContent = 'Generating...';
    }

    // Always use projected points endpoint
    fetch('/api/generate_squads_points/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            formation: formation,
            selection_mode: 'projected_points',
            games_to_consider: gamesToConsider
        })
    })
    .then(response => {
        console.log("[Squad Points] Response status:", response.status);
        return response.json();
    })
    .then(data => {
        console.log("[Squad Points] Response data:", data);
        if (btn) {
            btn.disabled = false;
            btn.textContent = 'Generate Squads';
        }
        if (data.success && data.squads && data.squads.length > 0) {
            window.fantasysquads = data.squads;
            showSquad(1);
        } else {
            console.error(`Error generating squads: ${data.error}`);
            const squadContent = document.getElementById('squad-content');
            if (squadContent) {
                squadContent.innerHTML = `<div class="alert alert-danger">Error: ${data.error || 'No squads generated.'}</div>`;
            }
        }
    })
    .catch(error => {
        console.error("[Squad Points] Fetch error:", error);
        if (btn) {
            btn.disabled = false;
            btn.textContent = 'Generate Squads';
        }
        const squadContent = document.getElementById('squad-content');
        if (squadContent) {
            squadContent.innerHTML = `<div class="alert alert-danger">Error: ${error.message}</div>`;
        }
    });
}

function showSquad(squadNumber) {
    currentSquadNumber = squadNumber;
    console.log(`[Squad Points] Showing squad ${squadNumber}`);
    const squadNumberSpan = document.getElementById('current-squad-number');
    if (squadNumberSpan) {
        squadNumberSpan.textContent = squadNumber;
    }
    updateSquadButtonStates(squadNumber);
    const squad = (window.fantasysquads || [])[squadNumber - 1];
    const squadContent = document.getElementById('squad-content');
    if (!squadContent) return;
    if (squad) {
        displaySquadData(squad, squadNumber);
    } else {
        squadContent.innerHTML = `<div class="alert alert-warning">No squad ${squadNumber} found. Generate squads first.</div>`;
    }
}

function updateSquadButtonStates(activeSquad) {
    for (let i = 1; i <= 4; i++) {
        const btn = document.getElementById(`btn-squad-${i}`);
        if (btn) {
            btn.classList.toggle('btn-success', i === activeSquad);
            btn.classList.toggle('btn-outline-success', i !== activeSquad);
        }
    }
}

function displaySquadData(squad, squadNumber) {
    const squadContent = document.getElementById('squad-content');
    if (!squadContent) return;
    
    const formation = document.getElementById('formation-select').value || '3-4-3';
    
    // Create player data object in the format generateFormationGrid expects
    const playerData = {
        goalkeepers: squad.goalkeepers || [],
        defenders: squad.defenders || [],
        midfielders: squad.midfielders || [],
        forwards: squad.forwards || []
    };
    
    // Use formation positions (same as original)
    const positions = getFormationPositions(formation);
    const positionCounts = [
        positions.find(p => p.key === 'goalkeepers')?.count || 1,
        positions.find(p => p.key === 'defenders')?.count || 3,
        positions.find(p => p.key === 'midfielders')?.count || 4,
        positions.find(p => p.key === 'forwards')?.count || 3
    ];
    
    generateFormationGrid(positionCounts, playerData, squadContent);
    
    // Add squad summary
    addSquadSummary(squad, squadNumber, squadContent);
}


function generateFormationGrid(positions, data, targetElement) {
    // Clear previous content
    targetElement.innerHTML = '';

    // Create the main squad-list div (with pitch background)
    const squadList = document.createElement('div');
    squadList.className = 'squad-list';

    const positionOrder = [
        { key: 'goalkeepers', label: 'GKP', count: positions[0] },
        { key: 'defenders', label: 'DEF', count: positions[1] },
        { key: 'midfielders', label: 'MID', count: positions[2] },
        { key: 'forwards', label: 'FWD', count: positions[3] }
    ];

    positionOrder.forEach(pos => {
        const players = data[pos.key] || [];
        if (players.length > 0) {
            const rowDiv = document.createElement('div');
            rowDiv.className = 'squad-row';
            players.forEach(playerObj => {
                // Show second name if available, otherwise first
                let displayName = '';
                if (playerObj.name) {
                    const nameParts = playerObj.name.trim().split(' ');
                    displayName = nameParts.length > 1 ? nameParts[1] : nameParts[0];
                }
                const playerDiv = document.createElement('div');
                playerDiv.innerHTML = `
                    <div class="player-png-container">
                        <img src="/static/img/player.png" width="90" height="90" alt="Player Icon" />
                    </div>
                    <div class="player-svg-name">${displayName}</div>
                `;
                rowDiv.appendChild(playerDiv);
            });
            squadList.appendChild(rowDiv);
        }
    });

    targetElement.appendChild(squadList);
}

function addSquadSummary(squad, squadNumber, targetElement) {
    // Calculate squad totals (only actual players)
    const allPlayers = [
        ...(squad.goalkeepers || []),
        ...(squad.defenders || []),
        ...(squad.midfielders || []),
        ...(squad.forwards || [])
    ];
    const totalCost = allPlayers.reduce((sum, player) => sum + parseFloat(player.cost || 0), 0);
    const totalProjectedPoints = allPlayers.reduce((sum, player) => sum + (parseFloat(player.projected_points) || 0), 0);
    
    const summaryDiv = document.createElement('div');
    summaryDiv.className = 'squad-summary mt-4';
    summaryDiv.innerHTML = `
        <div class="card">
            <div class="card-body">
                <h5 class="card-title">Squad ${squadNumber} Summary (Projected Points)</h5>
                <div class="row">
                    <div class="col-md-4">
                        <p><strong>Total Cost:</strong> £${totalCost.toFixed(1)}m / £100.0m</p>
                        <p><strong>Remaining:</strong> £${(100 - totalCost).toFixed(1)}m</p>
                    </div>
                    <div class="col-md-4">
                        <p><strong>Total Projected Points:</strong> ${totalProjectedPoints.toFixed(1)}</p>
                        <p><strong>Avg per Player:</strong> ${(totalProjectedPoints / allPlayers.length).toFixed(1)}</p>
                    </div>
                    <div class="col-md-4">
                        <p><strong>Players:</strong> ${allPlayers.length}/11</p>
                        <p><strong>Strategy:</strong> Points-optimized</p>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    targetElement.appendChild(summaryDiv);
}

function getFormationPositions(formation) {
    const formations = {
        '3-4-3': [
            { key: 'goalkeepers', title: 'Goalkeepers', class: 'goalkeepers', count: 1 },
            { key: 'defenders', title: 'Defenders', class: 'defenders', count: 3 },
            { key: 'midfielders', title: 'Midfielders', class: 'midfielders', count: 4 },
            { key: 'forwards', title: 'Forwards', class: 'forwards', count: 3 }
        ],
        '3-5-2': [
            { key: 'goalkeepers', title: 'Goalkeepers', class: 'goalkeepers', count: 1 },
            { key: 'defenders', title: 'Defenders', class: 'defenders', count: 3 },
            { key: 'midfielders', title: 'Midfielders', class: 'midfielders', count: 5 },
            { key: 'forwards', title: 'Forwards', class: 'forwards', count: 2 }
        ],
        '4-4-2': [
            { key: 'goalkeepers', title: 'Goalkeepers', class: 'goalkeepers', count: 1 },
            { key: 'defenders', title: 'Defenders', class: 'defenders', count: 4 },
            { key: 'midfielders', title: 'Midfielders', class: 'midfielders', count: 4 },
            { key: 'forwards', title: 'Forwards', class: 'forwards', count: 2 }
        ],
        '4-3-3': [
            { key: 'goalkeepers', title: 'Goalkeepers', class: 'goalkeepers', count: 1 },
            { key: 'defenders', title: 'Defenders', class: 'defenders', count: 4 },
            { key: 'midfielders', title: 'Midfielders', class: 'midfielders', count: 3 },
            { key: 'forwards', title: 'Forwards', class: 'forwards', count: 3 }
        ]
    };
    
    return formations[formation] || formations['3-4-3'];
}

