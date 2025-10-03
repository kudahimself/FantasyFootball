// Discard local changes and revert to last loaded squad
function discardLocalChanges() {
    if (window.localTeams && window.serverPlayers) {
        // Deep copy to avoid reference issues
        window.localTeams = {};
        console.log(' Reverting to last loaded squad from window.squads:', window.squads);
        window.localTeams = JSON.parse(JSON.stringify(window.squads));
        window.editMode = false;
        window.localTeam = window.localTeams[window.selectedgw]

        // Rebuild window.localTeam as an object with grouped arrays
        window.localTeam = {
            goalkeepers: [],
            defenders: [],
            midfielders: [],
            forwards: []
        };
        const positionMapping = {
            'goalkeepers': 'GKP',
            'defenders': 'DEF',
            'midfielders': 'MID',
            'forwards': 'FWD'
        };
        Object.keys(positionMapping).forEach(dbPosition => {
            const players = window.localTeam[dbPosition] || [];
            players.forEach(playerEntry => {
                let playerName = typeof playerEntry === 'string' ? playerEntry : playerEntry.name;
                if (!playerName) return;
                const playerMatch = window.serverPlayers.find(p => p.name === playerName);
                if (playerMatch) {
                    const expectedPosition = positionMapping[dbPosition];
                    const correctedPlayer = playerMatch.position === expectedPosition
                        ? playerMatch
                        : { ...playerMatch, position: expectedPosition };
                    window.localTeam[dbPosition].push(correctedPlayer);
                }
            });
        });

        // Set edit mode to false
        console.log(' Heeere Squad');
        window.editMode = false;
        // Update all squad-related UI
        if (typeof updateSquadDisplay === 'function') updateSquadDisplay(window.localTeams, window.selectedgw);

        if (typeof showStatusMessage === 'function') {
            showStatusMessage('Changes discarded. Squad reverted to last loaded state.', 'success');
        }
    } else {
        if (typeof showStatusMessage === 'function') {
            showStatusMessage('No previous squad data to revert to.', 'error');
        }
    }

    // Ensure window.localTeams is reset to the original squads
    if (window.squads) {
        window.localTeams = JSON.parse(JSON.stringify(window.squads)); // Deep copy to avoid reference issues
        console.log('✅ Reverted to original squad data:', window.localTeams);
    } else {
        console.error('❌ No original squad data found to revert to.');
    }
}
// Update squad display function (uses localTeam)
function updateSquadDisplay(squadsData = null, gameweek = window.gw) {
    const squadList = document.getElementById('squad-list');
    squadList.innerHTML = '<div style="color:#888;text-align:center;width:100%;">Loading squad...</div>';
    window.selectedgw = gameweek;

    // If localTeams is not provided, use the current gameweek's data
    // Use only the localTeams provided; do not fallback to window.squads
    let squadsDataToUse;
    if (!squadsData) {
        squadsDataToUse = window.localTeams || window.squads;
        if (!squadsDataToUse) {
            console.error(`❌ No data found for gameweek ${gameweek}.`);
            squadList.innerHTML = '<div style="color:#888;text-align:center;width:100%;">No squad data available.</div>';
            return;
        }
    } else {
        squadsDataToUse = squadsData;
    }
    squadsData = squadsDataToUse;
    // Try to find the exact gameweek first
    let foundSquad = squadsData[gameweek] || null;
    let foundGw = gameweek;

    // If not found, search backwards for the most recent non-null squad data
    if (!foundSquad) {
        const gwNumbers = Object.keys(squadsData)
            .map(Number)
            .filter(n => !isNaN(n) && n < gameweek)
            .sort((a, b) => b - a); // Descending order

        for (let gw of gwNumbers) {
            if (squadsData[gw]) {
                foundSquad = squadsData[gw];
                foundGw = gw;
                break;
            }
        }
    }

    if (!foundSquad) {
        squadList.innerHTML = '<div style="color:#888;text-align:center;width:100%;">No squad data available for this or previous gameweeks.</div>';
        return;
    }

    console.log(`✅ Loaded data for gameweek ${foundGw}:`, foundSquad);
    window.localTeam = foundSquad; // Update localTeam with the found gameweek's data

    renderSquad(window.localTeam);

    // Update squad badges after rendering squad
    if (typeof updateSquadBadges === 'function') {
        updateSquadBadges();
    }


    // Load substitutions for the displayed squad based on the toggled substitution mode
    if (typeof loadSubstituteRecommendations === 'function' && typeof loadIndividualSubstituteRecommendations === 'function') {
        if (showPackageSubstitutes) {
            loadSubstituteRecommendations(foundSquad, window.selectedgw);
        } else {
            loadIndividualSubstituteRecommendations(foundSquad, window.selectedgw);
        }
    }
    // Add editable-squad-row class after squad rows are rendered
    setTimeout(() => {
        const squadRows = document.querySelectorAll('.squad-row');
        if (window.editMode) {
            squadRows.forEach(row => row.classList.add('editable-squad-row'));
        } else {
            squadRows.forEach(row => row.classList.remove('editable-squad-row'));
        }
    }, 0);
}

// Render players dynamically
function renderPlayers() {
    const playersList = document.getElementById('players-list');
    
    if (dynamicFilteredPlayers.length === 0) {
        playersList.innerHTML = `
            <div class="alert alert-info m-3">
                <i class="fas fa-search"></i> No players found matching your criteria.
            </div>
        `;
        return;
    }
    
    const playersHTML = dynamicFilteredPlayers.map(player => {
        // Format player data safely
        const name = player.name || 'Unknown Player';
        const team = player.team || 'Unknown Team';
        const position = player.position || 'UNK';
        const eloRating = player.elo ? Math.round(player.elo * 10) / 10 : 0;
        const cost = player.cost ? `£${player.cost}m` : '£0.0m';
        const projectedPoints = player.projected_points || 0;
        
        // Position badge colors and display
        const positionMap = {
            'GKP': { display: 'GKP', class: 'bg-secondary text-dark' },
            'DEF': { display: 'DEF', class: 'bg-warning' },
            'MID': { display: 'MID', class: 'bg-success' },
            'FWD': { display: 'FWD', class: 'bg-primary' }
        };
        
        const posMap = positionMap[position] || { display: position, class: 'bg-secondary' };
        
        return `
            <div class="player-card">
                <div class="player-info">
                    <div class="player-name">${name} <span class="badge ${posMap.class} ms-2">${posMap.display}</span></div>
                    <div class="player-team">${team}</div>
                </div>
                <div class="player-stats">
                    <div class="player-price">${cost}</div>
                    <div class="player-points"> 📊 ${eloRating}</div>
                    <div class="player-projected">⭐ ${projectedPoints}pts</div>
                </div>
                <button class="add-btn" onclick="addPlayer('${player.id || name}', '${name}')">+</button>
            </div>
        `;
    }).join('');
    
    playersList.innerHTML = playersHTML;
}




function renderSquad(squadData) {
    const squadList = document.getElementById('squad-list');
    squadList.innerHTML = '';
    console.log('Loading Squad');
    if (!squadData || Object.keys(squadData).length === 0) {
        squadList.innerHTML = '<div style="color:#888;text-align:center;width:100%;">No squad data lol available.</div>';
        return;
    }
    if (window.editMode) {
        // Edit the existing header div with id="team-selection-header"
        const editHeaderDiv = document.getElementById('team-selection-header');
        console.log('[renderSquad] Edit mode ON. Header element:', editHeaderDiv);
        if (editHeaderDiv) {
            editHeaderDiv.textContent = 'Team Selection';
            editHeaderDiv.className = 'edit-team-header';
            console.log('[renderSquad] Header updated to Team Selection, class set to edit-team-header');
        } else {
            console.warn('[renderSquad] Edit mode ON but header element not found');
        }
    } else {
        const headerDiv = document.getElementById('team-selection-header');
        console.log('[renderSquad] Edit mode OFF. Header element:', headerDiv);
        if (headerDiv) {
            headerDiv.textContent = 'Fantasy 11';
            headerDiv.className = '';
            console.log('[renderSquad] Header updated to Fantasy 11, class cleared');
        } else {
            console.warn('[renderSquad] Edit mode OFF but header element not found');
        }
    }

    // Calculate squad attributes
    let totalPoints = 0, totalCost = 0, totalElo = 0, playerCount = 0, subsCount = 0;
    ['goalkeepers','defenders','midfielders','forwards'].forEach(pos => {
        const players = squadData[pos] || [];
        players.forEach((p, idx) => {
            // Assume first 11 are starters, rest are subs
            if (playerCount >= 11) subsCount++;
            totalPoints += Number(p.projected_points) || 0;
            totalCost += Number(p.cost) || 0;
            totalElo += Number(p.elo !== undefined ? p.elo : (p.elo !== undefined ? p.elo : 0)) || 0;
            playerCount++;
        });
    });

    const positionOrder = [
        { key: 'goalkeepers', label: 'GKP' },
        { key: 'defenders', label: 'DEF' },
        { key: 'midfielders', label: 'MID' },
        { key: 'forwards', label: 'FWD' }
    ];
    positionOrder.forEach(pos => {
        const players = squadData[pos.key] || [];
        if (players.length > 0) {
            const rowDiv = document.createElement('div');
            rowDiv.className = 'squad-row';
            players.forEach(playerObj => {
                const card = document.createElement('div');
                // Show second name if available, otherwise first
                let displayName = '';
                if (playerObj.name) {
                    const nameParts = playerObj.name.trim().split(' ');
                    displayName = nameParts.length > 1 ? nameParts[1] : nameParts[0];
                }
                    if (window.editMode) {
                        card.innerHTML = `
                            <div class="player-png-container" style="position:relative; cursor:pointer;"
                                 onclick="removePlayer('${playerObj.id || playerObj.name}', '${playerObj.name}'); return false;"
                                 title="Remove Player">
                                <img src="/static/img/player.png" width="90" height="90" alt="Player Icon" />
                                <span style="position:absolute;top:4px;right:4px;font-size:18px;color:#c00;">
                                    &times;
                                </span>
                            </div>
                            <div class="player-png-name">${displayName}</div>
                        `;
                    } else {
                        card.innerHTML = `
                            <div class="player-png-container" style="position:relative;">
                                <img src="/static/img/player.png" width="90" height="90" alt="Player Icon" />
                            </div>
                            <div class="player-png-name">${displayName}</div>
                        `;
                    }
                rowDiv.appendChild(card);
            });
            squadList.appendChild(rowDiv);
        }
    });
}

toggleEditMode = function() {
    window.editMode = !window.editMode;
    const makeChangesBtn = document.getElementById('make-changes-btn');
    if (makeChangesBtn) {
        if (window.editMode) {
            makeChangesBtn.classList.add('active-make-changes-btn');
        } else {
            makeChangesBtn.classList.remove('active-make-changes-btn');
        }
    }
    updateSquadDisplay(window.localTeams, window.selectedgw);
    if (typeof updateSquadBadges === 'function') updateSquadBadges();
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

function updateGameweekButtonStates(activeGameweek) {
    const gameweekButtons = document.querySelectorAll('[id^="btn-gw-"]');

    gameweekButtons.forEach(button => {
        const gw = parseInt(button.id.replace('btn-gw-', ''), 10);
        const isCurrentGameweek = button.id === 'btn-gw-success';

        button.classList.toggle('btn-success', gw === activeGameweek && !isCurrentGameweek);
        button.classList.toggle('btn-outline-success', gw !== activeGameweek && !isCurrentGameweek);
        button.classList.toggle('btn-warning', isCurrentGameweek); // Make current gameweek orange
        button.classList.remove('btn-success', isCurrentGameweek); // Ensure it doesn't appear active
    });
}


document.addEventListener('DOMContentLoaded', function() {
    const currentGameweek = Number(window.gw) || 1;

    function setupGameweekButton(btn, gw) {
        if (!btn) return;
        btn.textContent = `Gameweek ${gw}`;
        btn.onclick = () => handleGameweekClick(gw);
    }

    function handleGameweekClick(gw) {
        window.selectedgw = gw;
        let squads = window.localTeams || window.squads || {};
        let found = squads[gw];
        if (!found) {
            // Try previous GWs
            let prev = Object.keys(squads).map(Number).filter(n => n < gw).sort((a, b) => b - a);
            found = prev.map(p => squads[p]).find(Boolean);
            squads[gw] = found ? {...JSON.parse(JSON.stringify(found)), isEmpty: false} : {goalkeepers:[], defenders:[], midfielders:[], forwards:[], isEmpty:true};
        } else {
            squads[gw].isEmpty = false;
        }
        updateSquadDisplay(squads, gw);
        setActiveGameweekButton(gw);
    }

    function setActiveGameweekButton(gw) {
        const gameweekButtons = document.querySelectorAll('[id^="btn-gw-"]');
        const currentGameweek = Number(window.gw) || 1;

        // Remove active classes from all buttons
        gameweekButtons.forEach(btn => {
            btn.classList.remove('btn-success');
            btn.classList.add('btn-info');
        });

        let activeButton;
        if (gw === currentGameweek) {
            // Current gameweek: use btn-gw-success
            activeButton = document.getElementById('btn-gw-success');
        } else {
            // Find button by text content
            activeButton = Array.from(gameweekButtons).find(btn => {
                const btnGw = Number(btn.textContent.replace(/\D/g, ''));
                return btnGw === gw;
            });
        }

        if (activeButton) {
            activeButton.classList.add('btn-success');
            activeButton.classList.remove('btn-info');
        }
    }

    // Setup next 3 gameweek buttons
    for (let i = 1; i <= 3; i++) {
        const btn = document.getElementById('btn-gw-' + i);
        const gw = currentGameweek + i;
        setupGameweekButton(btn, gw);
    }

    // Setup current gameweek button
    const currentGwBtn = document.getElementById('btn-gw-success');
    if (currentGwBtn) {
        currentGwBtn.onclick = () => {
            updateSquadDisplay(window.squads, currentGameweek);
            setActiveGameweekButton(currentGameweek);
        };
    }

    // Add click listeners for active class toggling
    const gameweekButtons = document.querySelectorAll('[id^="btn-gw-"]');
    gameweekButtons.forEach(button => {
        button.addEventListener('click', function() {
            setActiveGameweekButton(Number(this.textContent.replace(/\D/g, '')));
        });
    });
});