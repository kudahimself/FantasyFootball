// Discard local changes and revert to last loaded squad
function discardLocalChanges() {
    if (window.currentSquadData && window.serverPlayers) {
        // Deep copy to avoid reference issues
        window.currentSquad = JSON.parse(JSON.stringify(window.currentSquadData));
        window.editMode = false;

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
            const players = window.currentSquad[dbPosition] || [];
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

        // Update all squad-related UI
        if (typeof updateSquadBadges === 'function') updateSquadBadges();
        if (typeof updateSquadDisplay === 'function') updateSquadDisplay();
        if (typeof displayCurrentSquad === 'function') displayCurrentSquad();

        if (typeof showStatusMessage === 'function') {
            showStatusMessage('Changes discarded. Squad reverted to last loaded state.', 'success');
        }
    } else {
        if (typeof showStatusMessage === 'function') {
            showStatusMessage('No previous squad data to revert to.', 'error');
        }
    }
}
// Update squad display function (uses localTeam)
function updateSquadDisplay(squadData) {
    const squadList = document.getElementById('squad-list');
    squadList.innerHTML = '<div style="color:#888;text-align:center;width:100%;">Loading squad...</div>';
    console.log('Loaded current squad from API:', squadData);
    renderSquad(squadData);
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


/**
 * Display the current squad using the global squad data (window.localTeam).
 * Renders the squad in formation layout.
 */
function displayCurrentSquad() {
    const squadList = document.getElementById('squad-list');
    squadList.innerHTML = '<div style="color:#888;text-align:center;width:100%;">Loading squad...</div>';
    fetch('/api/current_squad/')
        .then(response => response.json())
        .then(data => {
            if (!data || !data.current_squad || Object.keys(data.current_squad).length === 0) {
                squadList.innerHTML = '<div style="color:#888;text-align:center;width:100%;">No squad data available.</div>';
                return;
            }
            window.localTeam = data.current_squad;
            console.log('Loaded current squad from API:', window.localTeam);
            renderSquad(window.localTeam);
        })
        .catch(() => {
            squadList.innerHTML = '<div style="color:#888;text-align:center;width:100%;">No squad data available.</div>';
        });
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
        if (editHeaderDiv) {
            editHeaderDiv.textContent = 'Team Selection';
            editHeaderDiv.className = 'edit-team-header';
        }
    } else {
        const headerDiv = document.getElementById('team-selection-header');
        if (headerDiv) {
            headerDiv.textContent = 'Fantasy 11';
            headerDiv.className = '';
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
    updateSquadDisplay(window.localTeam);
    if (typeof updateSquadBadges === 'function') updateSquadBadges();
}