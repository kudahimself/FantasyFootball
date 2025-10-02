// Update Squad Badges
function updateSquadBadges() {
    // Support both array and grouped object formats for localTeam
    let squad = [];
    if (Array.isArray(window.localTeam)) {
        squad = window.localTeam;
    } else if (window.localTeam && typeof window.localTeam === 'object') {
        squad = [].concat(
            window.localTeam.goalkeepers || [],
            window.localTeam.defenders || [],
            window.localTeam.midfielders || [],
            window.localTeam.forwards || []
        );
    }
    console.log('updateSquadBadges: squad', squad);
    console.log('updateSquadBadges: localTeam', window.localTeam);

    const avgEloElem = document.getElementById('squad-avg-elo');
    const projElem = document.getElementById('squad-projected-points');
    const costElem = document.getElementById('squad-total-cost');
    if (!avgEloElem || !projElem || !costElem) return;
    if (!squad.length) {
        avgEloElem.textContent = '--';
        projElem.textContent = '--';
        costElem.textContent = '--';
        console.log('updateSquadBadges: squad empty');
        return;
    }
    const totalElo = squad.reduce((sum, p) => sum + (p.elo || 0), 0);
    const avgElo = totalElo / squad.length;
    const projectedPoints = squad.reduce((sum, p) => sum + (p.projected_points || 0), 0);
    const totalCost = squad.reduce((sum, p) => sum + (p.cost || 0), 0);
    avgEloElem.textContent = avgElo ? Math.round(avgElo * 10) / 10 : '--';
    projElem.textContent = projectedPoints ? Math.round(projectedPoints * 10) / 10 : '--';
    costElem.textContent = totalCost ? Math.round(totalCost * 10) / 10 : '--';
    console.log('updateSquadBadges:', { squad, avgElo, projectedPoints, totalCost });
}



// Add player function for grouped localTeam object
function addPlayer(playerId, playerName) {
    if (!window.editMode) {
        alert('Edit mode is not enabled. Please toggle edit mode to make changes.');
        return;
    }
    window.localTeam = window.localTeams[window.selectedgw] || window.localTeams['current'];
    console.log('➕ Adding player:', playerName, 'ID:', playerId);
    console.log('📊 dynamicAllPlayers array length:', dynamicAllPlayers.length);

    // Find the player in dynamicAllPlayers array
    const player = dynamicAllPlayers.find(p => p.id == playerId || p.name === playerName);

    if (!player) {
        console.error('❌ Player not found in dynamicAllPlayers array:', playerId, playerName);
        alert('Player not found!');
        return;
    }

    console.log('✅ Found player:', player);

    // Determine position group
    let posGroup = '';
    switch (player.position) {
        case 'GKP': posGroup = 'goalkeepers'; break;
        case 'DEF': posGroup = 'defenders'; break;
        case 'MID': posGroup = 'midfielders'; break;
        case 'FWD': posGroup = 'forwards'; break;
        default:
            showStatusMessage('Unknown player position: ' + player.position, 'error');
            return;
    }

    // Prevent adding the same player twice (by id or name)
    if (window.localTeam[posGroup].some(p => p.id == player.id || p.name === player.name)) {
        showStatusMessage(`${playerName} is already in your team!`, 'error');
        return;
    }

    // Check total team size limit (11 players)
    const totalPlayers = ['goalkeepers', 'defenders', 'midfielders', 'forwards']
        .reduce((sum, key) => sum + (window.localTeam[key]?.length || 0), 0);
    if (totalPlayers >= 11) {
        showStatusMessage('Your team is full! (11 players maximum)', 'error');
        return;
    }

    // Add player to correct position group
    window.localTeam[posGroup].push(player);
    window.localTeams[window.selectedgw] = window.localTeam;
    updateSquadDisplay(window.localTeams, window.selectedgw);
    console.log(`✅ Added ${playerName} to team (${posGroup}). Team size: ${totalPlayers + 1}`);
    showStatusMessage(`Added ${playerName} to your team.`, 'success');
}

function removePlayer(playerId, playerName) {
    if (!window.editMode) {
        return;
    }
    window.localTeam = window.localTeams[window.selectedgw];
    // If localTeam is an object with position arrays
    let removed = null;
    let changed = false;
    for (const pos of ['goalkeepers', 'defenders', 'midfielders', 'forwards']) {
        if (Array.isArray(window.localTeam[pos])) {
            const idx = window.localTeam[pos].findIndex(
                p => p.id == playerId || p.name === playerName
            );
            if (idx > -1) {
                removed = window.localTeam[pos].splice(idx, 1)[0];
                changed = true;
                console.log(`🗑️ Removed ${playerName} from ${pos}.`);
                break;
            }
        }
    }
    if (changed) {
        window.localTeams[window.selectedgw] = window.localTeam;
        updateSquadDisplay(window.localTeams, window.selectedgw);
        console.log(`🗑️ Removed ${playerName} from local team.`);
    }
}

function applyChangesToBackend() {
    // Save the entire localTeam as the new current squad, grouped by position with full player objects
    if (
        !window.localTeam ||
        (
            Array.isArray(window.localTeam) && window.localTeam.length === 0
        ) ||
        (
            typeof window.localTeam === 'object' &&
            ['goalkeepers', 'defenders', 'midfielders', 'forwards'].every(
                pos => !window.localTeam[pos] || window.localTeam[pos].length === 0
            )
        )
    ) {
        alert('No players in your squad to save!');
        return;
    }
    const gameweek = window.selectedgw;
    // Flatten grouped localTeam object into a single array
    const squadToSend = []
        .concat(
            window.localTeam.goalkeepers || [],
            window.localTeam.defenders || [],
            window.localTeam.midfielders || [],
            window.localTeam.forwards || []
        )
        .map(player => {
            const playerObj = {};
            ['id','name','position','team','cost','elo','projected_points'].forEach(k => {
                if (player[k] !== undefined) playerObj[k] = player[k];
            });
            return playerObj;
        });
    const btn = document.getElementById('apply-changes-btn');
    if (btn) btn.disabled = true;
    fetch(`/api/update_current_squad/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || '',
            'Gameweek': gameweek // Add gameweek to the headers
        },
        body: JSON.stringify({ squad: squadToSend })
    })
    .then(response => response.json())
    .then(data => {
        if (btn) btn.disabled = false;
        if (data.success) {
            // Refresh the page after successful save
            location.reload();
            window.localTeams[window.selectedgw] = window.localTeam;
            window.squads = {};
            window.squads = JSON.parse(JSON.stringify(window.localTeams));
        } else {
            // Optionally show a non-intrusive error message
            showStatusMessage('Error saving squad: ' + (data.error || 'Unknown error'), 'error');
        }
    })
    .catch(error => {
        if (btn) btn.disabled = false;
        showStatusMessage('Error saving squad: ' + (error.message || error), 'error');
    });
}