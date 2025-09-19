// Initialize when page loads
document.addEventListener('DOMContentLoaded', function() {
    console.log('✅ DOM loaded, setting up dynamic player search...');
    
    // Ensure allPlayers is populated for addPlayer function
    if (typeof window.serverPlayers !== 'undefined' && Array.isArray(window.serverPlayers)) {
        dynamicAllPlayers = window.serverPlayers;
        window.dynamicAllPlayers = dynamicAllPlayers;
        console.log(`✅ Global dynamicAllPlayers populated with ${dynamicAllPlayers.length} players`);
    }
    
    
    // Initialize with server data instead of API call
    initializeWithServerData();
    
    // Setup search input
    const searchInput = document.getElementById('player-search');
    if (searchInput) {
        searchInput.addEventListener('input', handleSearch);
        searchInput.addEventListener('focus', function() {
            if (this.value.length >= 2) {
                handleSearch();
            }
        });
        console.log('✅ Search input setup complete');
    }
    
    // Setup position tabs
    setupPositionTabs();
    console.log('✅ Position tabs setup complete');
    
    // Setup reset button
    const resetBtn = document.getElementById('reset-filters-btn');
    if (resetBtn) {
        resetBtn.addEventListener('click', resetFilters);
        console.log('✅ Reset button setup complete');
    }
    
    console.log('🎉 Dynamic player search functionality ready!');
});

// Dynamic search functionality
function handleSearch() {
    const searchInput = document.getElementById('player-search');
    const searchTerm = searchInput.value.toLowerCase().trim();
    
    console.log('🔍 Searching for:', searchTerm);
    // Filter players based on search term
    filterPlayers(searchTerm);
}

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



// Also try with DOMContentLoaded as backup
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, initializing...');
    setTimeout(function() {
        loadCurrentSquadFromDatabase();
        loadAllPlayers();
        // Load recommendations after squad is loaded
        setTimeout(function() {
            loadSubstituteRecommendations();
        }, 2500);
    }, 500); // Small delay to ensure elements are ready
});

// SUBSTITUTE RECOMMENDATIONS FUNCTIONALITY


document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('player-search');
    const positionTabs = document.querySelectorAll('.position-tab');
    const playerCards = document.querySelectorAll('.player-card');
    const playerCounter = document.getElementById('player-counter');
    const resetBtn = document.getElementById('reset-filters-btn');

    let currentPositionFilter = 'all';

    function filterAndRender() {
        const searchTerm = searchInput.value.toLowerCase().trim();
        let visibleCount = 0;

        playerCards.forEach(card => {
            const name = card.dataset.name || '';
            const team = card.dataset.team || '';
            const playerPosition = card.getAttribute('data-position') || ''; // More direct attribute access

            const matchesSearch = searchTerm === '' || name.includes(searchTerm) || team.includes(searchTerm);
            const matchesPosition = currentPositionFilter === 'all' || playerPosition === currentPositionFilter;

            if (matchesSearch && matchesPosition) {
                card.style.display = 'flex';
                visibleCount++;
            } else {
                card.style.display = 'none';
            }
        });

        playerCounter.textContent = `${visibleCount} of {{ total_players }} players shown`;
    }

    searchInput.addEventListener('input', filterAndRender);

    positionTabs.forEach(tab => {
        tab.addEventListener('click', function() {
            positionTabs.forEach(t => t.classList.remove('active'));
            this.classList.add('active');
            currentPositionFilter = this.dataset.position;
            filterAndRender();
        });
    });

    resetBtn.addEventListener('click', function() {
        searchInput.value = '';
        positionTabs.forEach(t => t.classList.remove('active'));
        document.querySelector('.position-tab[data-position="all"]').classList.add('active');
        currentPositionFilter = 'all';
        filterAndRender();
    });
    

    
    // Load player data for team management
    if (typeof window.serverPlayers === 'undefined' && document.querySelector('script')) {
        // Try to get server data from the second script block
        const scripts = document.querySelectorAll('script');
        for (let script of scripts) {
            if (script.textContent && script.textContent.includes('serverPlayers')) {
                // Data will be loaded by the second script
                break;
            }
        }
    }
});


// Load current squad from database (loads into localTeam)
function loadCurrentSquadFromDatabase() {
    try {
        window.localTeam = [];
        const currentSquadData = window.currentSquadData || {};
        window.currentSquad = currentSquadData;
        console.log('📊 Loading current squad from database:', currentSquadData);
        let playerData = window.serverPlayers;
        if (!playerData) {
            console.error('window.serverPlayers is not defined. Cannot match players.');
            return;
        }
        const positionMapping = {
            'goalkeepers': 'GKP',
            'defenders': 'DEF',
            'midfielders': 'MID',
            'forwards': 'FWD'
        };
        Object.keys(positionMapping).forEach(dbPosition => {
            const players = currentSquadData[dbPosition] || [];
            players.forEach(playerEntry => {
                let playerName = typeof playerEntry === 'string' ? playerEntry : playerEntry.name;
                if (!playerName) return;
                const playerMatch = playerData.find(p => p.name === playerName);
                if (playerMatch) {
                    const expectedPosition = positionMapping[dbPosition];
                    if (playerMatch.position === expectedPosition) {
                        window.localTeam.push(playerMatch);
                    } else {
                        const correctedPlayer = { ...playerMatch, position: expectedPosition };
                        window.localTeam.push(correctedPlayer);
                    }
                    console.log(`✅ Added ${playerName} (${expectedPosition}) to local team`);
                } else {
                    console.warn(`⚠️ Player ${playerName} not found in available players data, skipping.`);
                }
            });
        });
        // Remove any undefined/null entries just in case
        window.localTeam = window.localTeam.filter(Boolean);
        console.log(`📊 Loaded ${window.localTeam.length} players from current squad`);
        updateSquadBadges();
        displayCurrentSquad();
        console.log('✅ Current squad loaded and displayed.');
    } catch (e) {
        console.error('❌ Error loading current squad:', e);
        window.localTeam = [];
        updateSquadBadges();
        displayCurrentSquad();
    }
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', function() {
    loadCurrentSquadFromDatabase();
    setTimeout(updateSquadDisplay, 0);
});



// Filter players based on search term
function filterPlayers(searchTerm = '', positionFilter = 'all') {
    if (dynamicAllPlayers.length === 0) return;

    // Apply search filter
    let filtered = dynamicAllPlayers;
    
    if (searchTerm) {
        filtered = filtered.filter(player => 
            (player.name && player.name.toLowerCase().includes(searchTerm)) || 
            (player.team && player.team.toLowerCase().includes(searchTerm))
        );
    }
    
    // Apply position filter
    if (positionFilter !== 'all') {
        filtered = filtered.filter(player => {
            const playerPos = player.position || '';
            return playerPos === positionFilter;
        });
    }
    
    dynamicFilteredPlayers = filtered;
    renderPlayers();
    updatePlayerCounter(searchTerm, positionFilter);
}



// Update player counter
function updatePlayerCounter(searchTerm = '', positionFilter = 'all') {
    const counter = document.getElementById('player-counter');
    if (!counter) return;
    
    const totalPlayers = dynamicAllPlayers.length;
    const visiblePlayers = dynamicFilteredPlayers.length;
    
    if (searchTerm && positionFilter !== 'all') {
        counter.textContent = `${visiblePlayers} of ${totalPlayers} ${positionFilter} shown`;
    } else if (searchTerm) {
        counter.textContent = `${visiblePlayers} of ${totalPlayers} players shown`;
    } else if (positionFilter !== 'all') {
        counter.textContent = `${visiblePlayers} ${positionFilter} shown`;
    } else {
        counter.textContent = `${totalPlayers} players shown`;
    }
}

// Filter by position (updated for dynamic data)
function filterByPosition(position) {
    console.log('🎯 Position filter:', position);
    
    const searchTerm = document.getElementById('player-search').value.toLowerCase().trim();
    filterPlayers(searchTerm, position);
}

// Position filter functionality
function setupPositionTabs() {
    const tabs = document.querySelectorAll('.position-tab');
    
    tabs.forEach(tab => {
        tab.addEventListener('click', function() {
            // Remove active from all tabs
            tabs.forEach(t => t.classList.remove('active'));
            // Add active to clicked tab
            this.classList.add('active');
            
            const position = this.dataset.position;
            console.log('🎯 Position filter:', position);
            
            filterByPosition(position);
        });
    });
}

// Reset filters (updated for dynamic data)
function resetFilters() {
    console.log('🔄 Resetting filters...');
    
    // Clear search
    document.getElementById('player-search').value = '';
    
    // Reset position tabs
    document.querySelectorAll('.position-tab').forEach(tab => tab.classList.remove('active'));
    document.querySelector('.position-tab[data-position="all"]').classList.add('active');
    
    // Reset to all players
    dynamicFilteredPlayers = [...dynamicAllPlayers];
    renderPlayers();
    updatePlayerCounter();
}




// Filter and render function (corrected version)
function filterAndRender() {
    const searchTerm = searchInput.value.toLowerCase().trim();
    let visibleCount = 0;

    playerCards.forEach(card => {
        const name = card.dataset.name || '';
        const team = card.dataset.team || '';
        const playerPosition = card.getAttribute('data-position') || ''; // More direct attribute access

        const matchesSearch = searchTerm === '' || name.includes(searchTerm) || team.includes(searchTerm);
        const matchesPosition = currentPositionFilter === 'all' || playerPosition === currentPositionFilter;

        if (matchesSearch && matchesPosition) {
            card.style.display = 'flex';
            visibleCount++;
        } else {
            card.style.display = 'none';
        }
    });

    playerCounter.textContent = `${visibleCount} of {{ total_players }} players shown`;
}

// Initialize with server data
function initializeWithServerData() {
    try {
        console.log('📊 Initializing with server data...');
        
        if (typeof window.serverPlayers !== 'undefined' && Array.isArray(window.serverPlayers) && window.serverPlayers.length > 0) {
            // Use all players instead of slicing to 5
            dynamicAllPlayers = window.serverPlayers; 
            dynamicFilteredPlayers = [...dynamicAllPlayers];
            
            // Also update the global reference
            window.dynamicAllPlayers = dynamicAllPlayers;
            
            console.log(`✅ Success! Loaded ${dynamicAllPlayers.length} players.`);
            
            // Render players and update counter
            renderPlayers();
            updatePlayerCounter();
            updateSquadBadges(); // Initialize squad badges

            // Hide the loading indicator that shows "Preparing player data..."
            const initialLoading = document.getElementById('initial-loading');
            if (initialLoading) {
                initialLoading.style.display = 'none';
            }
            
        } else {
            console.warn('⚠️ No player data found from server. `serverPlayers` is either undefined, not an array, or empty.');
            throw new Error('No valid player data was provided by the server.');
        }
        
    } catch (error) {
        console.error('❌ Critical Error: Could not initialize player data.', error);
        
        const playersList = document.getElementById('players-list');
        if (playersList) {
            playersList.innerHTML = `
                <div class="alert alert-danger m-3">
                    <h6><i class="fas fa-exclamation-triangle"></i> Failed to Load Players</h6>
                    <p class="mb-2">There was a JavaScript error while loading player data. Check the browser console for details.</p>
                    <p><em>${error.message}</em></p>
                    <button class="btn btn-sm btn-outline-danger" onclick="location.reload()">🔄 Reload Page</button>
                </div>
            `;
        }
    }
}
