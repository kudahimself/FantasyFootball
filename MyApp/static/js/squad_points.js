// squad_points.js - Squad builder focused on projected points

let currentSquadNumber = 1;

document.addEventListener('DOMContentLoaded', function() {
    // Toggle event listener - redirect to ELO page
    const toggle = document.getElementById('selection-mode-toggle');
    if (toggle) {
        toggle.addEventListener('change', function() {
            if (!this.checked) {
                // Redirect to ELO squads page
                window.location.href = '/squads/';
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
});

// Auto-generate squads on page load
window.onload = function() {
    generateAndDisplaySquads();
};

function generateAndDisplaySquads() {
    const formationSelect = document.getElementById('formation-select');
    const formation = formationSelect && formationSelect.value ? formationSelect.value : '3-4-3';
    
    console.log("[Squad Points] Generating projected points squads for formation:", formation);

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
            selection_mode: 'projected_points'
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
        
        if (data.success) {
            console.log(`Generated ${data.squads_created || 4} squads using projected points`);
            // Automatically show first squad
            showSquad(1);
        } else {
            console.error(`Error generating squads: ${data.error}`);
            const squadContent = document.getElementById('squad-content');
            if (squadContent) {
                squadContent.innerHTML = `<div class="alert alert-danger">Error: ${data.error}</div>`;
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
    
    // Update squad number display
    const squadNumberSpan = document.getElementById('current-squad-number');
    if (squadNumberSpan) {
        squadNumberSpan.textContent = squadNumber;
    }
    
    // Update button states
    updateSquadButtonStates(squadNumber);
    
    // Fetch squad from projected points API
    fetch(`/api/squad_points/${squadNumber}/`)
        .then(response => {
            console.log(`[Squad Points] Squad response status: ${response.status}`);
            return response.json();
        })
        .then(data => {
            console.log(`[Squad Points] Squad data:`, data);
            const squadContent = document.getElementById('squad-content');
            if (!squadContent) return;
            
            if (data.success && data.squad) {
                displaySquadData(data.squad, squadNumber);
            } else {
                squadContent.innerHTML = 
                    `<div class="alert alert-warning">No squad ${squadNumber} found. Generate squads first.</div>`;
            }
        })
        .catch(error => {
            console.error(`[Squad Points] Squad fetch error:`, error);
            const squadContent = document.getElementById('squad-content');
            if (squadContent) {
                squadContent.innerHTML = 
                    `<div class="alert alert-danger">Error loading squad: ${error.message}</div>`;
            }
        });
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

    const goalkeepers = positions[0];
    const defenders = positions[1];
    const midfielders = positions[2];
    const forwards = positions[3];

    const rows = [
        { label: 'GK', count: goalkeepers, players: data?.goalkeepers },
        { label: 'DEF', count: defenders, players: data?.defenders },
        { label: 'MID', count: midfielders, players: data?.midfielders },
        { label: 'FWD', count: forwards, players: data?.forwards }
    ];

    // Create the main formation div
    const formation = document.createElement('div');
    formation.id = 'formation';

    for (let row of rows) {
        if (row.count > 0) {
            const rowContainer = document.createElement('div');
            rowContainer.classList.add('formation-row');

            for (let i = 0; i < row.count; i++) {
                // Create player container
                const playerContainer = document.createElement('div');
                playerContainer.classList.add('player-container');
                
                // Create player circle
                const playerCircle = document.createElement('div');
                playerCircle.classList.add('player-circle');
                playerCircle.textContent = row.label;
                
                // Create player name label
                const playerName = document.createElement('div');
                playerName.classList.add('player-name');
                
                if (row.players && row.players[i]) {
                    playerName.textContent = row.players[i].name;
                    
                    // Add click handler for player info (same as original)
                    playerContainer.addEventListener('click', () => {
                        window.location.href = `/player/${encodeURIComponent(row.players[i].name)}/`;
                    });
                    playerContainer.style.cursor = 'pointer';
                } else {
                    playerName.textContent = row.label + ' ' + (i + 1);
                }
                
                // Append circle and name to container
                playerContainer.appendChild(playerCircle);
                playerContainer.appendChild(playerName);
                
                // Append container to row
                rowContainer.appendChild(playerContainer);
            }
            formation.appendChild(rowContainer);
        }
    }
    // Append the whole formation to the target element
    targetElement.appendChild(formation);
}

function addSquadSummary(squad, squadNumber, targetElement) {
    // Calculate squad totals
    const allPlayers = Object.values(squad).flat();
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