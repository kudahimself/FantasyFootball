// your_app/static/your_app/squads.js

let fantasysquads = [];
let lastFormationInfo = null; // { formation: '3-4-3', counts: { keeper, defender, midfielder, attacker } }

// Add event listener for page-based navigation toggle
document.addEventListener('DOMContentLoaded', function() {
    // Toggle event listener - redirect to Projected Points page
    const toggle = document.getElementById('selection-mode-toggle');
    if (toggle) {
        toggle.addEventListener('change', function() {
            if (this.checked) {
                // Redirect to projected points squads page
                window.location.href = '/squad_points/';
            }
        });
    }
});

// This function now handles both fetching and displaying the initial squad.
function generateAndDisplaySquads() {
    // Read selected formation (fallback to 3-4-3 if not present)
    const formationSelect = document.getElementById('formation-select');
    console.log("[Squads] Formation select element:", formationSelect);
    console.log("[Squads] Formation select value:", formationSelect ? formationSelect.value : 'null');
    
    const formation = formationSelect && formationSelect.value ? formationSelect.value : '3-4-3';
    // cache-busting param to avoid any intermediate caching
    const url = `/api/squads/?formation=${encodeURIComponent(formation)}&_ts=${Date.now()}`;
    console.log("[Squads] Request →", { selectedFormation: formation, url });

    // Disable button while loading
    const btn = document.getElementById('btn-generate-squads');
    if (btn) {
        btn.disabled = true;
        btn.textContent = 'Generating...';
    }

    fetch(url)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            fantasysquads = data.squads;
            lastFormationInfo = { formation: data.formation, counts: data.counts };
            console.log("[Squads] Response ←", { returnedFormation: data.formation, counts: data.counts, squads: fantasysquads });
            
            if (fantasysquads.length > 0) {
                showSquad(fantasysquads[0].squad_number);
            } else {
                document.getElementById("squad-content").innerHTML = `<p>No squads were generated.</p>`;
                // Reset squad button highlight if no squads
                for (let i = 1; i <= 4; i++) {
                    const btn = document.getElementById(`btn-squad-${i}`);
                    if (btn) {
                        btn.classList.remove('btn-success');
                        btn.classList.add('btn-outline-success');
                    }
                }
            }
        })
        .catch(error => {
            console.error('Error fetching squads:', error);
            document.getElementById("squad-content").innerHTML = `<p>Error fetching squads. Please try again.</p>`;
        })
        .finally(() => {
            if (btn) {
                btn.disabled = false;
                btn.textContent = 'Generate Squads';
            }
        });
}

function showSquad(squad_number) {
    const squadContent = document.getElementById("squad-content");
    const squadNumberElement = document.getElementById("current-squad-number");
    
    const squad = fantasysquads.find(s => s.squad_number === parseInt(squad_number));
    
    if (squad) {
        // Show the current squad number and the formation as returned by backend
        squadNumberElement.textContent = squad.squad_number;
        try {
            const header = squadNumberElement.parentElement; // <h2>Squad <span>1</span></h2>
            const backendFormation = lastFormationInfo?.formation;
            if (header && backendFormation) {
                if (!document.getElementById('active-formation-label')) {
                    const span = document.createElement('span');
                    span.id = 'active-formation-label';
                    span.style.marginLeft = '12px';
                    span.style.fontSize = '0.9em';
                    span.style.color = '#666';
                    span.textContent = `(${backendFormation})`;
                    header.appendChild(span);
                } else {
                    const span = document.getElementById('active-formation-label');
                    if (span) span.textContent = `(${backendFormation})`;
                }
            }
        } catch (e) {
            console.debug('[Squads] Unable to set header formation label', e);
        }

        // Validate that positions match the backend counts (if provided)
        try {
            const positions = squad.positions;
            if (lastFormationInfo?.counts && Array.isArray(positions) && positions.length === 4) {
                const expected = [
                    lastFormationInfo.counts.keeper,
                    lastFormationInfo.counts.defender,
                    lastFormationInfo.counts.midfielder,
                    lastFormationInfo.counts.attacker,
                ];
                if (positions[0] !== expected[0] || positions[1] !== expected[1] ||
                    positions[2] !== expected[2] || positions[3] !== expected[3]) {
                    console.warn('[Squads] Mismatch: positions array vs backend counts', {
                        positions,
                        expectedCounts: expected,
                        backend: lastFormationInfo
                    });
                }
            }
        } catch {}
        
        // Create player data object in the format generateFormationGrid expects
        const playerData = {
            goalkeepers: squad.goalkeepers || [],
            defenders: squad.defenders || [],
            midfielders: squad.midfielders || [],
            forwards: squad.forwards || []
        };
        
        generateFormationGrid(squad.positions, playerData, squadContent);
        
        // Highlight active squad button if present
        for (let i = 1; i <= 4; i++) {
            const btn = document.getElementById(`btn-squad-${i}`);
            if (btn) {
                btn.classList.toggle('btn-success', i === squad.squad_number);
                btn.classList.toggle('btn-outline-success', i !== squad.squad_number);
            }
        }
    } else {
        squadContent.innerHTML = `<p>No squad found for number ${squad_number}.</p>`;
    }
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


window.onload = function() {
    // Initial load
    generateAndDisplaySquads();
    
    // Add event listener for the generate button
    const generateBtn = document.getElementById('btn-generate-squads');
    if (generateBtn) {
        generateBtn.addEventListener('click', generateAndDisplaySquads);
    }
    
    // Re-generate whenever the formation changes
    const formationSelect = document.getElementById('formation-select');
    if (formationSelect) {
        formationSelect.addEventListener('change', () => {
            console.log('[Squads] Formation changed →', formationSelect.value);
            generateAndDisplaySquads();
        });
    }
};