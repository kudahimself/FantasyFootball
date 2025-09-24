// Game Week Manager JavaScript

document.addEventListener('DOMContentLoaded', function() {
    initializeGameWeekManager();
    // Add event listener for Refresh Player Data button
    const refreshBtn = document.getElementById('refresh-player-data-btn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', function() {
            refreshBtn.disabled = true;
            const originalText = refreshBtn.innerHTML;
            refreshBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Refreshing...';
            fetch('/api/refresh_players/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken()
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showStatusMessage(data.message || 'Player data refreshed!', 'success');
                } else {
                    showStatusMessage(data.error || 'Failed to refresh player data.', 'error');
                }
                // Optionally update last update timestamp
                if (data.stats && data.stats.last_update) {
                    const lastUpdateElement = document.getElementById('last-update');
                    if (lastUpdateElement) {
                        lastUpdateElement.textContent = data.stats.last_update;
                    }
                } else if (data.last_update) {
                    const lastUpdateElement = document.getElementById('last-update');
                    if (lastUpdateElement) {
                        lastUpdateElement.textContent = data.last_update;
                    }
                }
            })
            .catch(error => {
                showStatusMessage('Error refreshing player data.', 'error');
            })
            .finally(() => {
                refreshBtn.disabled = false;
                refreshBtn.innerHTML = originalText;
            });
        });
    }
});

function initializeGameWeekManager() {
    // Set up event listeners
    setupEventListeners();
    
    // Initialize activity log
    logActivity('Game Week Manager initialized', 'info');
    
    console.log('Game Week Manager page initialized');
}

function setupEventListeners() {
    // Game week form submission
    const gameweekForm = document.getElementById('gameweek-form');
    if (gameweekForm) {
        gameweekForm.addEventListener('submit', handleGameWeekSubmit);
    }
    
    // Data refresh buttons
    const refreshPlayersBtn = document.getElementById('refresh-players-btn');
    if (refreshPlayersBtn) {
        refreshPlayersBtn.addEventListener('click', () => refreshData('players'));
    }
    
    const refreshFixturesBtn = document.getElementById('refresh-fixtures-btn');
    if (refreshFixturesBtn) {
        refreshFixturesBtn.addEventListener('click', () => refreshData('fixtures'));
    }
    
    const fullRefreshBtn = document.getElementById('full-refresh-btn');
    if (fullRefreshBtn) {
        fullRefreshBtn.addEventListener('click', () => refreshData('full'));
    }
    
    // Clear log button
    const clearLogBtn = document.getElementById('clear-log-btn');
    if (clearLogBtn) {
        clearLogBtn.addEventListener('click', clearActivityLog);
    }
}

function handleGameWeekSubmit(event) {
    event.preventDefault();
    
    const gameweekInput = document.getElementById('gameweek-input');
    const gameweek = parseInt(gameweekInput.value);
    
    if (!gameweek || gameweek < 1 || gameweek > 38) {
        showStatusMessage('Please enter a valid game week number (1-38)', 'error');
        return;
    }
    
    setGameWeek(gameweek);
}

function setGameWeek(gameweek) {
    const url = '/api/set_gameweek/';
    const data = {
        gameweek: gameweek
    };
    
    logActivity(`Setting game week to ${gameweek}...`, 'info');
    
    fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showStatusMessage(data.message, 'success');
            logActivity(`✓ ${data.message}`, 'success');
            
            // Update the current gameweek display
            const currentGwElement = document.getElementById('current-gw');
            if (currentGwElement) {
                currentGwElement.textContent = data.gameweek;
            }
        } else {
            showStatusMessage(data.error, 'error');
            logActivity(`✗ Failed to set game week: ${data.error}`, 'error');
        }
    })
    .catch(error => {
        console.error('Error setting game week:', error);
        showStatusMessage('Failed to set game week. Please try again.', 'error');
        logActivity(`✗ Error setting game week: ${error.message}`, 'error');
    });
}

function refreshData(type) {
    let url, buttonId, message;
    
    switch (type) {
        case 'players':
            url = '/api/refresh_players/';
            buttonId = 'refresh-players-btn';
            message = 'Refreshing player data...';
            break;
        case 'fixtures':
            url = '/api/refresh_fixtures/';
            buttonId = 'refresh-fixtures-btn';
            message = 'Refreshing fixtures...';
            break;
        case 'full':
            url = '/api/full_refresh/';
            buttonId = 'full-refresh-btn';
            message = 'Performing full data refresh...';
            break;
        default:
            return;
    }
    
    const button = document.getElementById(buttonId);
    if (!button) return;
    
    // Show loading state
    setButtonLoading(button, true);
    logActivity(message, 'info');
    
    fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showStatusMessage(data.message, 'success');
            logActivity(`✓ ${data.message}`, 'success');
            
            // If there are details (for full refresh), log them
            if (data.details && Array.isArray(data.details)) {
                data.details.forEach(detail => {
                    logActivity(detail, detail.includes('✓') ? 'success' : 'error');
                });
            }
            
            // Update last update timestamp if provided
            if (data.last_update) {
                const lastUpdateElement = document.getElementById('last-update');
                if (lastUpdateElement) {
                    lastUpdateElement.textContent = data.last_update;
                }
            }
        } else {
            showStatusMessage(data.error, 'error');
            logActivity(`✗ Refresh failed: ${data.error}`, 'error');
        }
    })
    .catch(error => {
        console.error('Error refreshing data:', error);
        showStatusMessage('Failed to refresh data. Please try again.', 'error');
        logActivity(`✗ Refresh error: ${error.message}`, 'error');
    })
    .finally(() => {
        setButtonLoading(button, false);
    });
}

function setButtonLoading(button, isLoading) {
    const icon = button.querySelector('.fas');
    const originalText = button.dataset.originalText || button.textContent;
    
    if (isLoading) {
        button.dataset.originalText = originalText;
        button.classList.add('btn-loading');
        button.disabled = true;
        if (icon) {
            icon.className = 'fas fa-spinner';
        }
        button.innerHTML = button.innerHTML.replace(originalText.trim(), 'Loading...');
    } else {
        button.classList.remove('btn-loading');
        button.disabled = false;
        button.textContent = originalText;
        // Restore original icon
        if (originalText.includes('Refresh Player Data')) {
            button.innerHTML = '<i class="fas fa-download"></i> Refresh Player Data';
        } else if (originalText.includes('Update Fixtures')) {
            button.innerHTML = '<i class="fas fa-calendar"></i> Update Fixtures';
        } else if (originalText.includes('Full Refresh')) {
            button.innerHTML = '<i class="fas fa-refresh"></i> Full Refresh';
        }
    }
}

function showStatusMessage(message, type = 'info') {
    const container = document.getElementById('status-messages');
    if (!container) return;
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `status-message ${type}`;
    messageDiv.innerHTML = `
        <strong>${type.charAt(0).toUpperCase() + type.slice(1)}:</strong> ${message}
        <button type="button" class="close" style="float: right; border: none; background: none; font-size: 18px;" onclick="this.parentElement.remove()">
            ×
        </button>
    `;
    
    container.appendChild(messageDiv);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (messageDiv.parentElement) {
            messageDiv.classList.add('fadeOut');
            setTimeout(() => {
                if (messageDiv.parentElement) {
                    messageDiv.remove();
                }
            }, 300);
        }
    }, 5000);
}

function logActivity(message, type = 'info') {
    const logContainer = document.getElementById('activity-log');
    if (!logContainer) return;
    
    const timestamp = new Date().toLocaleTimeString();
    const logEntry = document.createElement('div');
    logEntry.className = `log-entry ${type}`;
    logEntry.innerHTML = `
        <span class="timestamp">${timestamp}</span>
        <span class="message">${message}</span>
    `;
    
    // Remove "No recent activity" message if it exists
    const emptyMessage = logContainer.querySelector('.text-muted');
    if (emptyMessage) {
        emptyMessage.remove();
    }
    
    // Add new entry at the top
    logContainer.insertBefore(logEntry, logContainer.firstChild);
    
    // Limit to 50 entries
    const entries = logContainer.querySelectorAll('.log-entry');
    if (entries.length > 50) {
        entries[entries.length - 1].remove();
    }
    
    // Scroll to top
    logContainer.scrollTop = 0;
}

function clearActivityLog() {
    const logContainer = document.getElementById('activity-log');
    if (!logContainer) return;
    
    logContainer.innerHTML = '<p class="text-muted">No recent activity</p>';
    logActivity('Activity log cleared', 'info');
}

function getCsrfToken() {
    const cookieValue = document.cookie
        .split('; ')
        .find(row => row.startsWith('csrftoken='));
    
    if (cookieValue) {
        return cookieValue.split('=')[1];
    }
    
    // Fallback: get from form
    const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
    if (csrfInput) {
        return csrfInput.value;
    }
    
    return '';
}

// Utility function to update page elements
function updatePageData(data) {
    if (data.current_gameweek) {
        const gwElement = document.getElementById('current-gw');
        if (gwElement) {
            gwElement.textContent = data.current_gameweek;
        }
    }
    
    if (data.last_update) {
        const updateElement = document.getElementById('last-update');
        if (updateElement) {
            updateElement.textContent = data.last_update;
        }
    }
    
    if (data.total_players) {
        const playersElement = document.querySelector('.card-text h3');
        if (playersElement) {
            playersElement.textContent = data.total_players;
        }
    }
}

// Handle page unload
window.addEventListener('beforeunload', function() {
    // Cancel any ongoing requests if needed
    console.log('Game Week Manager page unloading');
});