// Team Selection JavaScript for managing current squad
console.log("team_selection.js loaded successfully");

let currentSquad = {};
let allPlayers = {};
let allPlayersFlat = []; // Flat array for search

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
            
            // Create flat array for searching
            allPlayersFlat = [];
            Object.keys(allPlayers).forEach(position => {
                allPlayers[position].forEach(player => {
                    allPlayersFlat.push({
                        ...player,
                        position: position
                    });
                });
            });
            
            console.log("All players loaded:", allPlayers);
            console.log("Flat players array:", allPlayersFlat);
            showStatusMessage('Players loaded successfully!', 'success');
        })
        .catch(error => {
            console.error('Error loading players:', error);
            showStatusMessage('Error loading players. Please try again.', 'error');
        });
}

// Intelligent player search function
function searchPlayers(query) {
    const resultsContainer = document.getElementById('player-search-results');
    const positionFilterElement = document.getElementById('player-position');
    
    // Check if elements exist (they might not if using new interface)
    if (!resultsContainer || !positionFilterElement) {
        console.log('Old search elements not found - probably using new interface');
        return;
    }
    
    const positionFilter = positionFilterElement.value;
    
    if (!query || query.length < 2) {
        resultsContainer.style.display = 'none';
        return;
    }
    
    // Filter players based on search query and position
    let filteredPlayers = allPlayersFlat.filter(player => {
        const matchesQuery = player.name.toLowerCase().includes(query.toLowerCase()) ||
                           player.team.toLowerCase().includes(query.toLowerCase());
        const matchesPosition = !positionFilter || player.position === positionFilter;
        return matchesQuery && matchesPosition;
    });
    
    // Sort by relevance (exact matches first, then starts with, then contains)
    filteredPlayers.sort((a, b) => {
        const aName = a.name.toLowerCase();
        const bName = b.name.toLowerCase();
        const queryLower = query.toLowerCase();
        
        if (aName === queryLower) return -1;
        if (bName === queryLower) return 1;
        if (aName.startsWith(queryLower)) return -1;
        if (bName.startsWith(queryLower)) return 1;
        return aName.localeCompare(bName);
    });
    
    // Limit results to prevent UI lag
    filteredPlayers = filteredPlayers.slice(0, 10);
    
    displaySearchResults(filteredPlayers);
}

// Display search results
function displaySearchResults(players) {
    const resultsContainer = document.getElementById('player-search-results');
    
    // Check if element exists
    if (!resultsContainer) {
        console.log('Search results container not found - probably using new interface');
        return;
    }
    
    if (players.length === 0) {
        resultsContainer.innerHTML = '<div style="padding: 10px; color: #666; text-align: center;">No players found</div>';
        resultsContainer.style.display = 'block';
        return;
    }
    
    resultsContainer.innerHTML = '';
    
    players.forEach(player => {
        const resultItem = document.createElement('div');
        resultItem.style.cssText = 'padding: 10px; border-bottom: 1px solid #eee; cursor: pointer; transition: background-color 0.2s;';
        resultItem.onmouseover = () => resultItem.style.backgroundColor = '#f8f9fa';
        resultItem.onmouseout = () => resultItem.style.backgroundColor = 'white';
        
        resultItem.innerHTML = `
            <div style="font-weight: bold; margin-bottom: 4px;">${player.name}</div>
            <div style="font-size: 12px; color: #666;">
                <span style="margin-right: 15px;"><i class="fas fa-tshirt"></i> ${player.team}</span>
                <span style="margin-right: 15px;"><i class="fas fa-chart-line"></i> ELO: ${player.elo.toFixed(1)}</span>
                <span style="margin-right: 15px;"><i class="fas fa-pound-sign"></i> £${player.cost}m</span>
                <span style="margin-right: 15px;"><i class="fas fa-running"></i> ${getPositionDisplay(player.position)}</span>
            </div>
        `;
        
        resultItem.onclick = () => selectPlayerFromSearch(player);
        resultsContainer.appendChild(resultItem);
    });
    
    resultsContainer.style.display = 'block';
}

// Select player from search results
function selectPlayerFromSearch(player) {
    selectedPlayer = player;
    
    const searchInput = document.getElementById('player-search-input');
    const searchResults = document.getElementById('player-search-results');
    const playerInfo = document.getElementById('player-info');
    
    // Check if elements exist
    if (searchInput) {
        searchInput.value = player.name;
    }
    if (searchResults) {
        searchResults.style.display = 'none';
    }
    
    // Update player info display if element exists
    if (playerInfo) {
        playerInfo.innerHTML = `
            <strong>${player.name}</strong><br>
            Team: ${player.team} | Position: ${getPositionDisplay(player.position)} | ELO Rating: ${player.elo.toFixed(1)} | Cost: £${player.cost}m
        `;
    }
}

// Show search results when input is focused
function showSearchResults() {
    const searchInput = document.getElementById('player-search-input');
    if (searchInput) {
        const query = searchInput.value;
        if (query.length >= 2) {
            searchPlayers(query);
        }
    }
}

// Update search when position filter changes
function updatePlayerSearch() {
    const searchInput = document.getElementById('player-search-input');
    if (searchInput) {
        const query = searchInput.value;
        if (query.length >= 2) {
            searchPlayers(query);
        }
    }
}

// Get display name for position
function getPositionDisplay(position) {
    const positionMap = {
        'goalkeepers': 'GK',
        'defenders': 'DEF',
        'midfielders': 'MID',
        'forwards': 'FWD'
    };
    return positionMap[position] || position;
}

// Hide search results when clicking outside
document.addEventListener('click', function(event) {
    const searchContainer = event.target.closest('#player-search-input, #player-search-results');
    if (!searchContainer) {
        const searchResults = document.getElementById('player-search-results');
        if (searchResults) {
            searchResults.style.display = 'none';
        }
    }
});

// Load players for the selected position into the dropdown (legacy function for compatibility)
function loadPlayersForPosition() {
    // This function is kept for backward compatibility but is no longer needed
    // The intelligent search handles all filtering
    updatePlayerSearch();
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
            
            // Refresh the player selection pane if it exists
            if (typeof refreshPlayerPane === 'function') {
                refreshPlayerPane();
            }
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

    // Define the order and display names for positions
    const positionOrder = [
        { key: 'goalkeepers', label: 'GK' },
        { key: 'defenders', label: 'DEF' },
        { key: 'midfielders', label: 'MID' },
        { key: 'forwards', label: 'FWD' }
    ];

    squadContent.innerHTML = '';

    // Flatten squad to a single array for display
    const flatSquad = [];
        positionOrder.forEach(pos => {
            const players = currentSquad[pos.key] || [];
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
                    // Add badge for position (match template logic)
                    const badge = document.createElement('span');
                    badge.className = 'badge ms-2';
                    if (pos.label === 'GK') badge.classList.add('bg-warning', 'text-dark');
                    if (pos.label === 'DEF') badge.classList.add('bg-primary');
                    if (pos.label === 'MID') badge.classList.add('bg-success');
                    if (pos.label === 'FWD') badge.classList.add('bg-danger');
                    badge.textContent = pos.label;
                    name.appendChild(badge);
                    info.appendChild(name);

                    // .player-team
                    const team = document.createElement('div');
                    team.className = 'player-team';
                    team.textContent = '\ud83d\udccd ' + (player.team || '');
                    info.appendChild(team);

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
                    points.textContent = player.elo !== undefined ? `📊 ${player.elo_rating !== undefined ? player.elo_rating : player.elo.toFixed(1)}` : '';
                    stats.appendChild(points);

                    // .player-projected (projected points)
                    const proj = document.createElement('div');
                    proj.className = 'player-projected';
                    if (player.projected_points !== undefined) {
                        proj.textContent = `⭐ ${player.projected_points}pts`;
                    } else {
                        proj.textContent = '';
                    }
                    stats.appendChild(proj);

                    card.appendChild(stats);

                    // Remove button (styled like add-btn)
                    const removeButton = document.createElement('button');
                    removeButton.textContent = '×';
                    removeButton.className = 'add-btn';
                    removeButton.onclick = () => removePlayerFromSquad(pos.key, player.name);
                    card.appendChild(removeButton);

                    squadContent.appendChild(card);
                });
            }
        });
}
// Generate formation grid (reused from squads.js but adapted for current squad)

// Generate formation grid (reused from squads.js but adapted for current squad)


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
    if (!selectedPlayer) {
        showStatusMessage('Please search and select a player first.', 'error');
        return;
    }
    
    const playerName = selectedPlayer.name;
    const position = selectedPlayer.position;
    
    console.log(`Adding ${playerName} (${position}) to squad...`);
    
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
            
            // Reset the search elements if they exist
            const searchInput = document.getElementById('player-search-input');
            const playerInfo = document.getElementById('player-info');
            const searchResults = document.getElementById('player-search-results');
            
            if (searchInput) {
                searchInput.value = '';
            }
            if (playerInfo) {
                playerInfo.innerHTML = '';
            }
            if (searchResults) {
                searchResults.style.display = 'none';
            }
            
            selectedPlayer = null;
            
            // Refresh the player selection pane if it exists
            if (typeof refreshPlayerPane === 'function') {
                refreshPlayerPane();
            }
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
            
            // Refresh the player selection pane if it exists
            if (typeof refreshPlayerPane === 'function') {
                refreshPlayerPane();
            }
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
    // Load recommendations after squad is loaded
    setTimeout(function() {
        loadSubstituteRecommendations();
    }, 2000);
};

// Also try with DOMContentLoaded as backup
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, initializing...');
    setTimeout(function() {
        loadCurrentSquad();
        loadAllPlayers();
        // Load recommendations after squad is loaded
        setTimeout(function() {
            loadSubstituteRecommendations();
        }, 2500);
    }, 500); // Small delay to ensure elements are ready
});

// SUBSTITUTE RECOMMENDATIONS FUNCTIONALITY

let recommendationsVisible = true;

function loadSubstituteRecommendations() {
    console.log('Loading substitute recommendations...');
    
    // Show loading state
    document.getElementById('recommendations-loading').style.display = 'block';
    document.getElementById('recommendations-empty').style.display = 'none';
    document.getElementById('recommendations-list').style.display = 'none';
    document.getElementById('recommendations-error').style.display = 'none';
    
    fetch('/api/test/recommend_substitutes/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({
            max_recommendations: 4,
            budget_constraint: 82.5
        })
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('recommendations-loading').style.display = 'none';
        
        if (data.success) {
            displaySubstituteRecommendations(data);
        } else {
            showRecommendationsError(data.error || 'Failed to get recommendations');
        }
    })
    .catch(error => {
        console.error('Error loading recommendations:', error);
        document.getElementById('recommendations-loading').style.display = 'none';
        showRecommendationsError('Network error while loading recommendations');
    });
}

function displaySubstituteRecommendations(data) {
    // Show recommendations list
    document.getElementById('recommendations-list').style.display = 'block';
    
    // Store current recommendations package globally
    currentRecommendationPackage = data.recommended_substitutes || [];
    
    // Update summary with package information
    const summaryElement = document.getElementById('recommendations-summary');
    const totalCostUsed = data.current_total_cost + (data.total_cost_change || 0);
    
    summaryElement.innerHTML = `
        <div class="row">
            <div class="col-md-2">
                <strong>Current Points:</strong> ${data.current_total_points}
            </div>
            <div class="col-md-3">
                <strong>Package Improvement:</strong> <span class="text-success">+${data.total_potential_improvement}</span>
            </div>
            <div class="col-md-3">
                <strong>Projected Total:</strong> ${data.projected_new_total}
            </div>
            <div class="col-md-2">
                <strong>Budget Used:</strong> £${totalCostUsed.toFixed(1)}m
            </div>
            <div class="col-md-2">
                <strong>Substitutions:</strong> ${data.number_of_recommendations}
            </div>
        </div>
        <div class="row mt-2">
            <div class="col-12">
                <div class="alert alert-info mb-0">
                    <i class="fas fa-lightbulb"></i>
                    <strong>Optimized Package:</strong> This recommendation uses linear programming to find the best combination of ${data.number_of_recommendations} substitutions that maximizes your points within the £82.5 budget.
                </div>
            </div>
        </div>
    `;
    
    // Clear and populate recommendations cards
    const cardsContainer = document.getElementById('recommendations-cards');
    cardsContainer.innerHTML = '';
    
    if (data.recommended_substitutes && data.recommended_substitutes.length > 0) {
        // Create a single card with all transfers
        const transfersCardHtml = createCombinedTransfersCard(data.recommended_substitutes, data.total_potential_improvement);
        cardsContainer.innerHTML += transfersCardHtml;
    } else {
        cardsContainer.innerHTML = `
            <div class="col-12">
                <div class="alert alert-info text-center">
                    <i class="fas fa-check-circle"></i>
                    Your squad is already optimized! No improvements found within budget constraints.
                </div>
            </div>
        `;
    }
}

function createCombinedTransfersCard(recommendations, totalImprovement) {
    let transfersHtml = '';
    
    recommendations.forEach((rec, index) => {
        const current = rec.current_player;
        const substitute = rec.substitute;
        const improvement = rec.improvement;
        const costDiff = rec.cost_difference;
        const position = rec.position;
        
        const costColor = costDiff > 0 ? 'text-danger' : costDiff < 0 ? 'text-success' : 'text-muted';
        const costSign = costDiff > 0 ? '+' : '';
        
        transfersHtml += `
            <div class="row align-items-center mb-2 pb-2 ${index < recommendations.length - 1 ? 'border-bottom' : ''}">
                <div class="col-md-5">
                    <div class="d-flex align-items-center">
                        <div class="text-danger mr-2">
                            <i class="fas fa-minus-circle"></i>
                        </div>
                        <div>
                            <div class="font-weight-bold" style="font-size: 0.85em;">${current.name}</div>
                            <small class="text-muted" style="font-size: 0.7em;">${current.team} • ${current.projected_points} pts • £${current.cost}m</small>
                        </div>
                    </div>
                </div>
                <div class="col-md-2 text-center">
                    <i class="fas fa-arrow-right text-primary"></i>
                </div>
                <div class="col-md-5">
                    <div class="d-flex align-items-center justify-content-between">
                        <div class="d-flex align-items-center">
                            <div class="text-success mr-2">
                                <i class="fas fa-plus-circle"></i>
                            </div>
                            <div>
                                <div class="font-weight-bold" style="font-size: 0.85em;">${substitute.name}</div>
                                <small class="text-muted" style="font-size: 0.7em;">${substitute.team} • ${substitute.projected_points} pts • £${substitute.cost}m</small>
                            </div>
                        </div>
                        <div class="text-right">
                            <div class="badge badge-success" style="font-size: 0.7em;">+${improvement} pts</div>
                            <div><small class="${costColor}" style="font-size: 0.65em;">${costSign}£${Math.abs(costDiff)}m</small></div>
                            <button class="btn btn-xs btn-outline-primary mt-1 py-0 px-1" style="font-size: 0.65em;"
                                    onclick="makeSubstitution('${current.name}', '${substitute.name}', '${position}')"
                                    title="Make this substitution">
                                <i class="fas fa-exchange-alt"></i>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    });
    
    return `
        <div class="col-12 mb-3">
            <div class="card border-success">
                <div class="card-header bg-success text-white">
                    <div class="d-flex justify-content-between align-items-center">
                        <h5 class="mb-0">
                            <i class="fas fa-exchange-alt"></i>
                            Recommended Transfers
                        </h5>
                        <span class="badge badge-light text-success">
                            Total: +${totalImprovement} pts
                        </span>
                    </div>
                </div>
                <div class="card-body py-2">
                    ${transfersHtml}
                </div>
            </div>
        </div>
    `;
}

function createRecommendationCard(recommendation, index, isPackage = false) {
    const current = recommendation.current_player;
    const substitute = recommendation.substitute;
    const improvement = recommendation.improvement;
    const costDiff = recommendation.cost_difference;
    const position = recommendation.position;
    
    const costColor = costDiff > 0 ? 'text-danger' : costDiff < 0 ? 'text-success' : 'text-muted';
    const costSign = costDiff > 0 ? '+' : '';
    
    const packageNote = isPackage ? `
        <div class="badge badge-success mb-1" style="font-size: 0.7em;">
            <i class="fas fa-puzzle-piece"></i> Part ${index + 1}
        </div>
    ` : '';
    
    return `
        <div class="col-md-6 mb-2">
            <div class="card h-100 ${isPackage ? 'border-success' : 'border-left-primary'}" style="${isPackage ? 'border: 2px solid #28a745;' : 'border-left: 4px solid #007bff;'}">
                <div class="card-body py-2 px-3">
                    ${packageNote}
                    <div class="d-flex justify-content-between align-items-start mb-1">
                        <h6 class="card-title mb-0" style="font-size: 0.9em;">
                            <i class="fas fa-arrow-right ${isPackage ? 'text-success' : 'text-primary'}"></i>
                            ${position.charAt(0).toUpperCase() + position.slice(1)} ${isPackage ? 'Swap' : 'Upgrade'}
                        </h6>
                        <span class="badge ${isPackage ? 'badge-success' : 'badge-primary'}" style="font-size: 0.7em;">+${improvement} pts</span>
                    </div>
                    
                    <div class="mb-1">
                        <div class="d-flex justify-content-between align-items-center">
                            <small class="text-muted" style="font-size: 0.7em;">Out:</small>
                            <small class="text-muted" style="font-size: 0.7em;">${current.projected_points} pts • £${current.cost}m</small>
                        </div>
                        <div class="font-weight-bold text-danger" style="font-size: 0.85em;">
                            <i class="fas fa-minus-circle"></i> ${current.name}
                        </div>
                        <small class="text-muted" style="font-size: 0.7em;">${current.team}</small>
                    </div>
                    
                    <div class="text-center mb-1">
                        <i class="fas fa-arrow-down ${isPackage ? 'text-success' : 'text-primary'}" style="font-size: 0.9em;"></i>
                    </div>
                    
                    <div class="mb-2">
                        <div class="d-flex justify-content-between align-items-center">
                            <small class="text-muted" style="font-size: 0.7em;">In:</small>
                            <small class="text-muted" style="font-size: 0.7em;">${substitute.projected_points} pts • £${substitute.cost}m</small>
                        </div>
                        <div class="font-weight-bold text-success" style="font-size: 0.85em;">
                            <i class="fas fa-plus-circle"></i> ${substitute.name}
                        </div>
                        <small class="text-muted" style="font-size: 0.7em;">${substitute.team}</small>
                    </div>
                    
                    <div class="d-flex justify-content-between align-items-center">
                        <small class="text-muted" style="font-size: 0.7em;">
                            Cost: <span class="${costColor}">${costSign}£${Math.abs(costDiff)}m</span>
                        </small>
                        ${!isPackage ? `
                            <button class="btn btn-sm btn-outline-primary py-1 px-2" style="font-size: 0.7em;"
                                    onclick="makeSubstitution('${current.name}', '${substitute.name}', '${position}')"
                                    title="Make this substitution">
                                <i class="fas fa-exchange-alt"></i> Swap
                            </button>
                        ` : `
                            <span class="badge badge-light" style="font-size: 0.65em;">
                                <i class="fas fa-box"></i> Package
                            </span>
                        `}
                    </div>
                </div>
            </div>
        </div>
    `;
}

// Global variable to store current recommendations for package application
let currentRecommendationPackage = [];

function applyCompletePackage() {
    if (!currentRecommendationPackage || currentRecommendationPackage.length === 0) {
        showStatusMessage('No package recommendations available', 'error');
        return;
    }
    
    const substitutionCount = currentRecommendationPackage.length;
    const totalImprovement = currentRecommendationPackage.reduce((sum, rec) => sum + rec.improvement, 0);
    
    if (!confirm(`Are you sure you want to apply all ${substitutionCount} substitutions for a total improvement of +${totalImprovement.toFixed(1)} points?`)) {
        return;
    }
    
    console.log(`Applying complete package of ${substitutionCount} substitutions...`);
    
    // Show loading state
    showStatusMessage('Applying substitution package...', 'info');
    
    // Apply all substitutions sequentially
    applySubstitutionsSequentially(currentRecommendationPackage, 0);
}

function applySubstitutionsSequentially(substitutions, index) {
    if (index >= substitutions.length) {
        // All substitutions completed
        showStatusMessage(`Successfully applied all ${substitutions.length} substitutions!`, 'success');
        // Refresh the squad and recommendations
        loadCurrentSquad();
        setTimeout(() => {
            loadSubstituteRecommendations();
        }, 1500);
        return;
    }
    
    const substitution = substitutions[index];
    const currentPlayerName = substitution.current_player.name;
    const substitutePlayerName = substitution.substitute.name;
    const position = substitution.position;
    
    console.log(`Applying substitution ${index + 1}/${substitutions.length}: ${currentPlayerName} → ${substitutePlayerName}`);
    
    // Remove current player
    fetch('/api/remove-player/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({
            position: position,
            player_name: currentPlayerName
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success || !data.error) {
            // Add substitute player
            return fetch('/api/add-player/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken()
                },
                body: JSON.stringify({
                    position: position,
                    player_name: substitutePlayerName
                })
            });
        } else {
            throw new Error(data.error || 'Failed to remove player');
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success || !data.error) {
            // Move to next substitution
            setTimeout(() => {
                applySubstitutionsSequentially(substitutions, index + 1);
            }, 300); // Small delay between operations
        } else {
            throw new Error(data.error || 'Failed to add substitute player');
        }
    })
    .catch(error => {
        console.error(`Error in substitution ${index + 1}:`, error);
        showStatusMessage(`Error in substitution ${index + 1}: ${error.message}`, 'error');
    });
}

function makeSubstitution(currentPlayerName, substitutePlayerName, position) {
    if (!confirm(`Are you sure you want to replace ${currentPlayerName} with ${substitutePlayerName}?`)) {
        return;
    }
    
    console.log(`Making substitution: ${currentPlayerName} → ${substitutePlayerName} (${position})`);
    
    // First remove the current player
    fetch('/api/remove-player/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({
            position: position,
            player_name: currentPlayerName
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success || !data.error) {
            // Then add the substitute
            return fetch('/api/add-player/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken()
                },
                body: JSON.stringify({
                    position: position,
                    player_name: substitutePlayerName
                })
            });
        } else {
            throw new Error(data.error || 'Failed to remove player');
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success || !data.error) {
            showStatusMessage(`Successfully replaced ${currentPlayerName} with ${substitutePlayerName}!`, 'success');
            // Refresh the squad and recommendations
            loadCurrentSquad();
            setTimeout(() => {
                loadSubstituteRecommendations();
            }, 1000);
        } else {
            throw new Error(data.error || 'Failed to add substitute player');
        }
    })
    .catch(error => {
        console.error('Error making substitution:', error);
        showStatusMessage(`Error making substitution: ${error.message}`, 'error');
    });
}

function showRecommendationsError(message) {
    document.getElementById('recommendations-error').style.display = 'block';
    document.getElementById('error-message').textContent = message;
}

function toggleRecommendationsSection() {
    const content = document.getElementById('recommendations-content');
    const icon = document.getElementById('toggle-recommendations-icon');
    
    if (recommendationsVisible) {
        content.style.display = 'none';
        icon.className = 'fas fa-eye-slash';
        recommendationsVisible = false;
    } else {
        content.style.display = 'block';
        icon.className = 'fas fa-eye';
        recommendationsVisible = true;
    }
}