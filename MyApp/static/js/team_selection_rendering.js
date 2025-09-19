// Update squad display function (uses localTeam)
initializeWithServerData();
function updateSquadDisplay() {
    const squadContent = document.getElementById('squad-content');
    if (!squadContent) return;
    const team = window.localTeam || [];
    // Group players by position
    const positionOrder = ['GKP', 'DEF', 'MID', 'FWD'];
    const positionBadges = {
        GKP: '<span class="badge bg-warning text-dark ms-2">GKP</span>',
        DEF: '<span class="badge bg-primary ms-2">DEF</span>',
        MID: '<span class="badge bg-success ms-2">MID</span>',
        FWD: '<span class="badge bg-danger ms-2">FWD</span>'
    };
    const grouped = { GKP: [], DEF: [], MID: [], FWD: [] };
    team.forEach(player => {
        if (grouped[player.position]) {
            grouped[player.position].push(player);
        }
    });
    let squadHTML = `<div class="squad-formation">`;
    squadHTML += `<div class="text-center mb-3"><small class="text-muted">${team.length}/11 players selected</small></div>`;
    if (team.length === 0) {
        squadHTML += `<div class="text-center py-4"><i class="fas fa-users fa-3x text-muted mb-3"></i><p class="text-muted">No players selected yet. Click "+ Add" on any player to start building your team.</p></div>`;
    } else {
        positionOrder.forEach(pos => {
            if (grouped[pos].length > 0) {
                squadHTML += `<div class="position-group mb-2">`;
                squadHTML += `<div class="position-label mb-1">${pos}</div>`;
                grouped[pos].forEach(player => {
                    squadHTML += `<div class="selected-player-card">`;
                    squadHTML += `<div class="player-info">`;
                    squadHTML += `<div class="player-name">${player.name} ${positionBadges[player.position] || ''}</div>`;
                    squadHTML += `<div class="player-team">📍 ${player.team}</div>`;
                    squadHTML += `</div>`;
                    squadHTML += `<div class="player-stats">`;
                    squadHTML += `<div class="player-price">£${player.cost}m</div>`;
                    squadHTML += `<div class="player-points">📊 ${player.elo_rating ? Math.round(player.elo_rating * 10) / 10 : 0}</div>`;
                    squadHTML += `<div class="player-projected">⭐ ${player.projected_points || 0}pts</div>`;
                    squadHTML += `</div>`;
                    squadHTML += `<button class="btn btn-sm btn-outline-danger" onclick="removePlayer('${player.id}', '${player.name}')" title="Remove player"><i class="fas fa-times"></i></button>`;
                    squadHTML += `</div>`;
                });
                squadHTML += `</div>`;
            }
        });
    }
    squadHTML += `</div>`;
    squadContent.innerHTML = squadHTML;
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
        const eloRating = player.elo_rating ? Math.round(player.elo_rating * 10) / 10 : 0;
        const cost = player.cost ? `£${player.cost}m` : '£0.0m';
        const projectedPoints = player.projected_points || 0;
        
        // Position badge colors and display
        const positionMap = {
            'GKP': { display: 'GKP', class: 'bg-warning text-dark' },
            'DEF': { display: 'DEF', class: 'bg-primary' },
            'MID': { display: 'MID', class: 'bg-success' },
            'FWD': { display: 'FWD', class: 'bg-danger' }
        };
        
        const posMap = positionMap[position] || { display: position, class: 'bg-secondary' };
        
        return `
            <div class="player-card">
                <div class="player-info">
                    <div class="player-name">${name} <span class="badge ${posMap.class} ms-2">${posMap.display}</span></div>
                    <div class="player-team">📍 ${team}</div>
                </div>
                <div class="player-stats">
                    <div class="player-price">${cost}</div>
                    <div class="player-points">📊 ${eloRating}</div>
                    <div class="player-projected">⭐ ${projectedPoints}pts</div>
                </div>
                <button class="add-btn" onclick="addPlayer('${player.id || name}', '${name}')">+ Add</button>
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
    const squadContent = document.getElementById("squad-content");
    const team = window.localTeam || [];
    if (!squadContent) return;

    // Define the order and display names for positions
    const positionOrder = [
        { key: 'GKP', label: 'GKP' },
        { key: 'DEF', label: 'DEF' },
        { key: 'MID', label: 'MID' },
        { key: 'FWD', label: 'FWD' }
    ];

    // Group players by position
    const grouped = { GKP: [], DEF: [], MID: [], FWD: [] };
    team.forEach(player => {
        if (grouped[player.position]) {
            grouped[player.position].push(player);
        }
    });

    squadContent.innerHTML = '';

    positionOrder.forEach(pos => {
        const players = grouped[pos.key] || [];
        // Add heading for the position
        const heading = document.createElement('div');
        heading.textContent = pos.label;
        heading.className = 'position-header';
        squadContent.appendChild(heading);

        if (players.length === 0) {
            const empty = document.createElement('div');
            empty.textContent = `No ${pos.label}`;
            empty.style.color = '#888';
            empty.style.padding = '8px 20px';
            squadContent.appendChild(empty);
        } else {
            players.forEach(player => {
                // Use the same HTML structure as the player selection pane
                const card = document.createElement('div');
                card.className = 'player-card';
                card.setAttribute('data-name', (player.name || '').toLowerCase());
                card.setAttribute('data-team', (player.team || '').toLowerCase());
                card.setAttribute('data-position', pos.label);

                // .player-info
                const info = document.createElement('div');
                info.className = 'player-info';

                // .player-name
                const name = document.createElement('div');
                name.className = 'player-name';
                name.textContent = player.name + ' ';
                // Add badge for position
                const badge = document.createElement('span');
                badge.className = 'badge ms-2';
                if (pos.label === 'GKP') badge.classList.add('bg-warning', 'text-dark');
                if (pos.label === 'DEF') badge.classList.add('bg-primary');
                if (pos.label === 'MID') badge.classList.add('bg-success');
                if (pos.label === 'FWD') badge.classList.add('bg-danger');
                badge.textContent = pos.label;
                name.appendChild(badge);
                info.appendChild(name);

                // .player-team
                const teamDiv = document.createElement('div');
                teamDiv.className = 'player-team';
                teamDiv.textContent = '📍 ' + (player.team || '');
                info.appendChild(teamDiv);

                card.appendChild(info);

                // .player-stats
                const stats = document.createElement('div');
                stats.className = 'player-stats';

                // .player-price
                const price = document.createElement('div');
                price.className = 'player-price';
                price.textContent = player.cost !== undefined ? `£${player.cost}m` : '';
                stats.appendChild(price);

                // .player-points (ELO)
                const points = document.createElement('div');
                points.className = 'player-points';
                const elo = player.elo_rating !== undefined ? player.elo_rating : (player.elo !== undefined ? player.elo : 0);
                points.textContent = `📊 ${Math.round(elo * 10) / 10}`;
                stats.appendChild(points);

                // .player-projected (projected points)
                const proj = document.createElement('div');
                proj.className = 'player-projected';
                proj.textContent = `⭐ ${player.projected_points || 0}pts`;
                stats.appendChild(proj);

                card.appendChild(stats);

                // Remove button (styled like add-btn)
                const removeButton = document.createElement('button');
                removeButton.textContent = '×';
                removeButton.className = 'add-btn';
                removeButton.onclick = () => removePlayer(player.id, player.name);
                card.appendChild(removeButton);

                squadContent.appendChild(card);
            });
        }
    });
}