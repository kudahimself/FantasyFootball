// Data Management JavaScript for FPL position updates and Elo recalculation

// Get CSRF Token for Django
function getCSRFToken() {
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

// Update player positions from FPL API
function updatePlayerPositions() {
    const button = document.getElementById('btn-update-positions');
    const spinner = button.querySelector('.spinner-border');
    const statusDiv = document.getElementById('data-status-message');
    const statusText = document.getElementById('status-text');
    const statusDetails = document.getElementById('status-details');
    const changesDiv = document.getElementById('position-changes');
    const changesList = document.getElementById('changes-list');
    
    // Show loading state
    button.disabled = true;
    spinner.classList.remove('d-none');
    statusDiv.style.display = 'block';
    statusDiv.className = 'alert alert-info';
    statusText.innerHTML = '<i class="fas fa-sync fa-spin"></i> Updating player positions from FPL API...';
    statusDetails.textContent = 'This may take a few moments. Please wait.';
    changesDiv.style.display = 'none';
    
    fetch('/api/update_positions/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        // Hide loading state
        button.disabled = false;
        spinner.classList.add('d-none');
        
        if (data.success) {
            statusDiv.className = 'alert alert-success';
            statusText.innerHTML = '<i class="fas fa-check-circle"></i> ' + data.message;
            statusDetails.textContent = `Successfully updated ${data.updated_count} players.`;
            
            // Show position changes if any
            if (data.position_changes && data.position_changes.length > 0) {
                changesDiv.style.display = 'block';
                changesList.innerHTML = '';
                
                data.position_changes.forEach(change => {
                    const changeItem = document.createElement('div');
                    changeItem.className = 'change-item';
                    changeItem.innerHTML = `
                        <strong>${change.name}</strong>: 
                        <span class="badge bg-secondary">${change.old_position}</span> 
                        <i class="fas fa-arrow-right mx-2"></i> 
                        <span class="badge bg-primary">${change.new_position}</span>
                    `;
                    changesList.appendChild(changeItem);
                });
            } else {
                statusDetails.textContent += ' No position changes were needed.';
            }
            
            // Show errors if any
            if (data.errors && data.errors.length > 0) {
                statusDetails.textContent += ` Note: ${data.errors.length} minor issues occurred during sync.`;
            }
            
            // Refresh system info and then refresh page
            setTimeout(() => {
                refreshSystemInfo();
                // Auto-refresh page after successful update
                setTimeout(() => {
                    statusText.innerHTML = '<i class="fas fa-sync-alt fa-spin"></i> Refreshing page...';
                    statusDetails.textContent = 'Page will refresh to show updated data.';
                    location.reload();
                }, 2000);
            }, 1000);
            
        } else {
            statusDiv.className = 'alert alert-danger';
            statusText.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Failed to update positions';
            statusDetails.textContent = data.error || 'Unknown error occurred. Please try again.';
        }
    })
    .catch(error => {
        // Hide loading state
        button.disabled = false;
        spinner.classList.add('d-none');
        
        console.error('Error updating positions:', error);
        statusDiv.className = 'alert alert-danger';
        statusText.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Network Error';
        statusDetails.textContent = 'Unable to connect to the server. Please check your connection and try again.';
    });
}

// Recalculate player Elo ratings
function recalculatePlayerElos() {
    const button = document.getElementById('btn-recalculate-elos');
    const spinner = button.querySelector('.spinner-border');
    const statusDiv = document.getElementById('data-status-message');
    const statusText = document.getElementById('status-text');
    const statusDetails = document.getElementById('status-details');
    const changesDiv = document.getElementById('position-changes');
    
    // Show loading state
    button.disabled = true;
    spinner.classList.remove('d-none');
    statusDiv.style.display = 'block';
    statusDiv.className = 'alert alert-info';
    statusText.innerHTML = '<i class="fas fa-calculator fa-pulse"></i> Recalculating Elo ratings...';
    statusDetails.textContent = 'Processing player performance data. This may take several moments.';
    changesDiv.style.display = 'none';
    
    fetch('/api/recalculate_elos/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        // Hide loading state
        button.disabled = false;
        spinner.classList.add('d-none');
        
        if (data.success) {
            statusDiv.className = 'alert alert-success';
            statusText.innerHTML = '<i class="fas fa-check-circle"></i> ' + data.message;
            statusDetails.textContent = `Successfully processed ${data.updated_count} players for gameweek ${data.week}.`;
            
            // Refresh system info and then refresh page
            setTimeout(() => {
                refreshSystemInfo();
                // Auto-refresh page after successful update
                setTimeout(() => {
                    statusText.innerHTML = '<i class="fas fa-sync-alt fa-spin"></i> Refreshing page...';
                    statusDetails.textContent = 'Page will refresh to show updated data.';
                    location.reload();
                }, 2000);
            }, 1000);
            
        } else {
            statusDiv.className = 'alert alert-danger';
            statusText.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Failed to recalculate Elo ratings';
            statusDetails.textContent = data.error || 'Unknown error occurred during calculation.';
        }
    })
    .catch(error => {
        // Hide loading state
        button.disabled = false;
        spinner.classList.add('d-none');
        
        console.error('Error recalculating Elos:', error);
        statusDiv.className = 'alert alert-danger';
        statusText.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Network Error';
        statusDetails.textContent = 'Unable to connect to the server. Please check your connection and try again.';
    });
}

// Hide status message
function hideStatusMessage() {
    const statusDiv = document.getElementById('data-status-message');
    statusDiv.style.display = 'none';
}

// Refresh system information
function refreshSystemInfo() {
    // Fetch real system information from the server
    fetch('/api/system_info/', {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const currentGwElement = document.getElementById('current-gw');
            const totalPlayersElement = document.getElementById('total-players');
            const lastUpdateElement = document.getElementById('last-update');
            
            if (currentGwElement) currentGwElement.textContent = data.current_gameweek || '4';
            if (totalPlayersElement) totalPlayersElement.textContent = data.total_players || '596';
            if (lastUpdateElement) lastUpdateElement.textContent = data.last_update || 'Never';
        }
    })
    .catch(error => {
        console.error('Error fetching system info:', error);
        // Fallback to static values if API fails
        const currentGwElement = document.getElementById('current-gw');
        const totalPlayersElement = document.getElementById('total-players');
        const lastUpdateElement = document.getElementById('last-update');
        
        if (currentGwElement) currentGwElement.textContent = '4';
        if (totalPlayersElement) totalPlayersElement.textContent = '596';
        if (lastUpdateElement) lastUpdateElement.textContent = new Date().toLocaleString();
    });
}

// Initialize page when loaded
window.onload = function() {
    console.log('Data management page loaded');
    refreshSystemInfo();
    
    // Auto-hide status messages after 10 seconds
    setTimeout(() => {
        const statusDiv = document.getElementById('data-status-message');
        if (statusDiv && statusDiv.style.display !== 'none') {
            statusDiv.style.opacity = '0.7';
        }
    }, 10000);
};