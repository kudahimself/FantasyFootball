// Team Selection JavaScript for managing current squad
console.log("team_selection.js loaded successfully");

let currentSquad = {};
let allPlayers = {};

// Load all available players from the server
function loadAllPlayers() {
    console.log("Loading all available players from server...");
    
    fetch('/api/all-players/')
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                showStatusMessage(data.error, 'error');
                return;
            }
            allPlayers = data.players;
            console.log("All players loaded:", allPlayers);
            loadPlayersForPosition(); // Load players for the currently selected position
            showStatusMessage('Players loaded successfully!', 'success');
        })
        .catch(error => {
            console.error('Error loading players:', error);
            showStatusMessage('Error loading players. Please try again.', 'error');
        });
}

// Load players for the selected position into the dropdown
function loadPlayersForPosition() {
    const position = document.getElementById('player-position').value;
    const playerSelect = document.getElementById('player-select');
    const playerInfo = document.getElementById('player-info');
    
    // Clear previous options
    playerSelect.innerHTML = '<option value="">Select a player...</option>';
    playerInfo.innerHTML = '';
    
    if (!allPlayers[position]) {
        playerSelect.innerHTML = '<option value="">No players available</option>';
        return;
    }
    
    // Add players to dropdown
    allPlayers[position].forEach(player => {
        const option = document.createElement('option');
        option.value = player.name;
        option.textContent = `${player.name} (Elo: ${player.elo.toFixed(1)}, Cost: £${player.cost}m)`;
        option.dataset.player = JSON.stringify(player);
        playerSelect.appendChild(option);
    });
    
    // Add change event to show player info
    playerSelect.onchange = function() {
        if (this.value && this.selectedOptions[0].dataset.player) {
            const player = JSON.parse(this.selectedOptions[0].dataset.player);
            playerInfo.innerHTML = `
                <strong>${player.name}</strong><br>
                Team: ${player.team} | Elo Rating: ${player.elo.toFixed(1)} | Cost: £${player.cost}m
            `;
        } else {
            playerInfo.innerHTML = '';
        }
    };
}

// Load the current squad from the server
function loadCurrentSquad() {
    console.log("Loading current squad from server...");
    
    fetch('/api/current_squad/')
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            currentSquad = data.current_squad;
            console.log("Current squad loaded:", currentSquad);
            displayCurrentSquad();
        })
        .catch(error => {
            console.error('Error loading current squad:', error);
            showStatusMessage('Error loading squad. Please try again.', 'error');
        });
}

// Display the current squad using the formation layout
function displayCurrentSquad() {
    console.log('displayCurrentSquad called, currentSquad:', currentSquad);
    const squadContent = document.getElementById("squad-content");
    
    if (Object.keys(currentSquad).length === 0) {
        squadContent.innerHTML = `<p>No squad data available.</p>`;
        return;
    }
    
    // Use formation structure: [goalkeepers, defenders, midfielders, forwards]
    const positions = [
        currentSquad.goalkeepers?.length || 0,
        currentSquad.defenders?.length || 0,
        currentSquad.midfielders?.length || 0,
        currentSquad.forwards?.length || 0
    ];
    
    generateFormationGrid(positions, currentSquad, squadContent);
    
    // Calculate and update team totals
    updateTeamTotals();
}

// Calculate and display team totals (Elo and Cost)
function updateTeamTotals() {
    console.log('updateTeamTotals called');
    
    // Debug: Check if currentSquad is populated
    if (!currentSquad || Object.keys(currentSquad).length === 0) {
        console.log('No squad data available for calculation');
        return;
    }
    
    // Check if DOM elements exist
    const teamEloElement = document.getElementById('team-elo');
    const teamCostElement = document.getElementById('team-cost');
    
    if (!teamEloElement || !teamCostElement) {
        console.log('DOM elements not found:', {
            teamElo: !!teamEloElement,
            teamCost: !!teamCostElement
        });
        // Retry in 100ms if elements not found
        setTimeout(updateTeamTotals, 100);
        return;
    }
    
    let totalElo = 0;
    let totalCost = 0;
    let playerCount = 0;
    
    // Calculate totals from all positions
    const positions = ['goalkeepers', 'defenders', 'midfielders', 'forwards'];
    
    positions.forEach(position => {
        if (currentSquad[position]) {
            currentSquad[position].forEach(player => {
                if (player && player.elo !== undefined && player.cost !== undefined) {
                    totalElo += parseFloat(player.elo);
                    totalCost += parseFloat(player.cost);
                    playerCount++;
                }
            });
        }
    });
    
    // Calculate average Elo (more meaningful than total Elo)
    const avgElo = playerCount > 0 ? totalElo / playerCount : 0;
    
    console.log(`Updating totals: ${playerCount} players, Avg Elo: ${avgElo.toFixed(1)}, Total Cost: £${totalCost.toFixed(1)}m`);
    
    // Update display
    teamEloElement.textContent = playerCount > 0 ? avgElo.toFixed(1) : '--';
    teamCostElement.textContent = playerCount > 0 ? totalCost.toFixed(1) : '--';
    
    console.log('Display updated successfully');
}

// Generate formation grid (reused from squads.js but adapted for current squad)
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
                
                // Create player name label with remove button
                const playerName = document.createElement('div');
                playerName.classList.add('player-name');
                
                if (row.players && row.players[i]) {
                    const playerNameText = document.createElement('span');
                    playerNameText.textContent = row.players[i].name;
                    
                    const removeButton = document.createElement('button');
                    removeButton.textContent = '×';
                    removeButton.style.cssText = 'margin-left: 5px; background: #dc3545; color: white; border: none; border-radius: 50%; width: 16px; height: 16px; font-size: 10px; cursor: pointer;';
                    removeButton.onclick = () => removePlayerFromSquad(getPositionKey(row.label), row.players[i].name);
                    
                    playerName.appendChild(playerNameText);
                    playerName.appendChild(removeButton);
                } else {
                    playerName.textContent = `Empty ${row.label}`;
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

// Helper function to convert label to position key
function getPositionKey(label) {
    const labelMap = {
        'GK': 'goalkeepers',
        'DEF': 'defenders',
        'MID': 'midfielders',
        'FWD': 'forwards'
    };
    return labelMap[label];
}

// Add the selected player to the squad
function addSelectedPlayerToSquad() {
    const position = document.getElementById('player-position').value;
    const playerSelect = document.getElementById('player-select');
    const playerName = playerSelect.value;
    
    if (!playerName) {
        showStatusMessage('Please select a player.', 'error');
        return;
    }
    
    console.log(`Adding ${playerName} to ${position}...`);
    
    fetch('/api/add-player/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({
            position: position,
            player_name: playerName
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showStatusMessage(data.error, 'error');
        } else {
            showStatusMessage(data.message, 'success');
            currentSquad = data.squad;
            displayCurrentSquad();
            // Reset the dropdown
            document.getElementById('player-select').value = '';
            document.getElementById('player-info').innerHTML = '';
        }
    })
    .catch(error => {
        console.error('Error adding player:', error);
        showStatusMessage('Error adding player. Please try again.', 'error');
    });
}

// Remove a player from the squad
function removePlayerFromSquad(position, playerName) {
    if (!confirm(`Remove ${playerName} from ${position}?`)) {
        return;
    }
    
    console.log(`Removing ${playerName} from ${position}...`);
    
    fetch('/api/remove-player/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({
            position: position,
            player_name: playerName
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showStatusMessage(data.error, 'error');
        } else {
            showStatusMessage(data.message, 'success');
            currentSquad = data.squad;
            displayCurrentSquad();
        }
    })
    .catch(error => {
        console.error('Error removing player:', error);
        showStatusMessage('Error removing player. Please try again.', 'error');
    });
}

// Show status messages
function showStatusMessage(message, type) {
    const statusDiv = document.getElementById('status-message');
    statusDiv.textContent = message;
    statusDiv.style.display = 'block';
    
    if (type === 'success') {
        statusDiv.style.backgroundColor = '#d4edda';
        statusDiv.style.color = '#155724';
        statusDiv.style.border = '1px solid #c3e6cb';
    } else if (type === 'error') {
        statusDiv.style.backgroundColor = '#f8d7da';
        statusDiv.style.color = '#721c24';
        statusDiv.style.border = '1px solid #f5c6cb';
    }
    
    // Hide message after 5 seconds
    setTimeout(() => {
        statusDiv.style.display = 'none';
    }, 5000);
}

// Get CSRF token for Django
function getCsrfToken() {
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
    if (csrfToken) {
        return csrfToken.value;
    }
    
    // Try to get from cookie
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
        const [name, value] = cookie.trim().split('=');
        if (name === 'csrftoken') {
            return value;
        }
    }
    return '';
}

// Load squad and players when page loads
window.onload = function() {
    console.log('Page loaded, initializing...');
    loadCurrentSquad();
    loadAllPlayers();
};

// Also try with DOMContentLoaded as backup
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, initializing...');
    setTimeout(function() {
        loadCurrentSquad();
        loadAllPlayers();
    }, 500); // Small delay to ensure elements are ready
});