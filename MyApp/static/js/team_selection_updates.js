// Update Squad Badges
function updateSquadBadges() {
    const squad = window.localTeam || [];
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
    const totalElo = squad.reduce((sum, p) => sum + (p.elo_rating || 0), 0);
    const avgElo = totalElo / squad.length;
    const projectedPoints = squad.reduce((sum, p) => sum + (p.projected_points || 0), 0);
    const totalCost = squad.reduce((sum, p) => sum + (p.cost || 0), 0);
    avgEloElem.textContent = avgElo ? Math.round(avgElo * 10) / 10 : '--';
    projElem.textContent = projectedPoints ? Math.round(projectedPoints * 10) / 10 : '--';
    costElem.textContent = totalCost ? Math.round(totalCost * 10) / 10 : '--';
    console.log('updateSquadBadges:', { squad, avgElo, projectedPoints, totalCost });
}



// Add player function
function addPlayer(playerId, playerName) {
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

    // Prevent adding the same player twice (by id or name)
    if (window.localTeam.some(p => p.id == player.id || p.name === player.name)) {
        showStatusMessage(`${playerName} is already in your team!`, 'error');
        return;
    }

    // Check team size limit (11 players)
    if (window.localTeam.length >= 11) {
        showStatusMessage('Your team is full! (11 players maximum)', 'error');
        return;
    }

    // Add player to local team
    window.localTeam.push(player);
    updateSquadBadges();
    updateSquadDisplay();
    console.log(`✅ Added ${playerName} to team. Team size: ${window.localTeam.length}`);
    showStatusMessage(`Added ${playerName} to your team.`, 'success');
}

function removePlayer(playerId, playerName) {
    if (!window.localTeam) return;
    const index = window.localTeam.findIndex(p => p.id == playerId || p.name === playerName);
    if (index > -1) {
        window.localTeam.splice(index, 1);
        updateSquadBadges();
        updateSquadDisplay();
        console.log(`🗑️ Removed ${playerName} from local team. Team size: ${window.localTeam.length}`);
    }
}
// Remove a player from the squad
function removePlayerFromSquad(position, playerName) {
    console.log(`Removing ${playerName} from ${position} (local-only, mirror addPlayer)...`);

    try {
        // Ensure localTeam exists
        if (!window.localTeam || !Array.isArray(window.localTeam)) {
            window.localTeam = [];
        }

        // Find index by name (calls to this function pass name)
        const idx = window.localTeam.findIndex(p => p.name === playerName || String(p.id) === String(playerName));
        if (idx === -1) {
            console.warn('Player not found in localTeam:', playerName);
            alert(`${playerName} was not in your local team.`);
            return;
        }

        const removed = window.localTeam.splice(idx, 1)[0];

        // Use the same render flow as addPlayer
        if (typeof updateSquadBadges === 'function') updateSquadBadges();
        if (typeof updateSquadDisplay === 'function') updateSquadDisplay();
        // Re-render dynamic players list if present
        if (typeof renderPlayers === 'function') renderPlayers();
        if (typeof refreshPlayerPane === 'function') refreshPlayerPane();

        // Focus search input and scroll to player list for consistent UX
        const searchInput = document.getElementById('player-search');
        if (searchInput) searchInput.focus();
        const playersList = document.getElementById('players-list');
        if (playersList) playersList.scrollIntoView({ behavior: 'smooth', block: 'start' });

        // Show the same alert style as addPlayer
        alert(`✅ Removed ${removed.name} from your team!`);
        console.log(`✅ Locally removed ${removed.name}. localTeam size: ${window.localTeam.length}`);
    } catch (err) {
        console.error('Error in local removePlayerFromSquad:', err);
        showStatusMessage('Error removing player locally. See console for details.', 'error');
    }
}

function applyChangesToBackend() {
    // Save the entire localTeam as the new current squad, grouped by position with full player objects
    if (!window.localTeam || window.localTeam.length === 0) {
        alert('No players in your squad to save!');
        return;
    }
    // Send the flat localTeam array; backend will group it
    const squadToSend = window.localTeam.map(player => {
        const playerObj = {};
        ['id','name','position','team','cost','elo','elo_rating','projected_points'].forEach(k => {
            if (player[k] !== undefined) playerObj[k] = player[k];
        });
        if (playerObj.elo_rating && !playerObj.elo) playerObj.elo = playerObj.elo_rating;
        return playerObj;
    });
    const btn = document.getElementById('apply-changes-btn');
    if (btn) btn.disabled = true;
    fetch('/api/update_current_squad/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || ''
        },
        body: JSON.stringify({ squad: squadToSend })
    })
    .then(response => response.json())
    .then(data => {
        if (btn) btn.disabled = false;
        if (data.success) {
            // Refresh the page after successful save
            location.reload();
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
