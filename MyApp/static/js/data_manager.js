document.addEventListener('DOMContentLoaded', function() {
    // Load gameweek information on page load
    loadGameweekInfo();
    
    // Refresh Gameweek Info functionality
    document.getElementById('refresh-gameweek-btn').addEventListener('click', function() {
        loadGameweekInfo();
    });
    
    // Function to load and display gameweek information
    function loadGameweekInfo() {
        const gameweekDiv = document.getElementById('gameweek-info');
        
        gameweekDiv.innerHTML = `
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <p class="mt-2">Loading gameweek information...</p>
        `;
        
        fetch('/api/gameweek_info/')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const statusBadge = getStatusBadge(data.finished, data.is_current);
                    const deadlineDate = new Date(data.deadline_time).toLocaleString();
                    
                    gameweekDiv.innerHTML = `
                        <div class="text-center">
                            <h2 class="display-4 text-primary mb-3">${data.current_gameweek}</h2>
                            <h5 class="mb-3">${data.gameweek_name}</h5>
                            <div class="mb-3">${statusBadge}</div>
                            <div class="row text-center">
                                <div class="col-12 mb-2">
                                    <small class="text-muted">Deadline:</small><br>
                                    <strong>${deadlineDate}</strong>
                                </div>
                                ${data.average_entry_score ? `
                                <div class="col-6">
                                    <small class="text-muted">Avg Score:</small><br>
                                    <strong>${data.average_entry_score}</strong>
                                </div>
                                <div class="col-6">
                                    <small class="text-muted">High Score:</small><br>
                                    <strong>${data.highest_score}</strong>
                                </div>
                                ` : ''}
                            </div>
                        </div>
                    `;
                } else {
                    gameweekDiv.innerHTML = `
                        <div class="alert alert-danger">
                            <i class="fas fa-exclamation-triangle"></i>
                            Failed to load gameweek info: ${data.error}
                        </div>
                    `;
                }
            })
            .catch(error => {
                gameweekDiv.innerHTML = `
                    <div class="alert alert-danger">
                        <i class="fas fa-exclamation-triangle"></i>
                        Error loading gameweek information
                    </div>
                `;
                console.error('Error:', error);
            });
    }
    
    // Helper function to get status badge
    function getStatusBadge(finished, isCurrent) {
        if (finished) {
            return '<span class="badge bg-secondary">Finished</span>';
        } else if (isCurrent) {
            return '<span class="badge bg-success">Live</span>';
        } else {
            return '<span class="badge bg-primary">Upcoming</span>';
        }
    }
    
    // Import Current Gameweek functionality
    document.getElementById('import-gameweek-btn').addEventListener('click', function() {
        const btn = this;
        const originalText = btn.innerHTML;
        const statusDiv = document.getElementById('refresh-status');
        
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Importing...';
        statusDiv.innerHTML = '<div class="alert alert-info">Importing current gameweek data...</div>';
        
        fetch('/api/import_gameweek/', {method: 'POST'})
            .then(response => response.json())
            .then(data => {
                btn.disabled = false;
                btn.innerHTML = originalText;
                
                if (data.success) {
                    statusDiv.innerHTML = `
                        <div class="alert alert-success">
                            <strong>Gameweek Import Complete!</strong><br>
                            • New matches added: ${data.new_matches}<br>
                            • Matches updated: ${data.updated_matches}<br>
                            • Matches skipped: ${data.skipped_matches}<br>
                            • Players processed: ${data.total_players}<br>
                            • Current gameweek: ${data.gameweek}<br>
                            • Duration: ${data.duration}
                        </div>
                    `;
                } else {
                    statusDiv.innerHTML = `
                        <div class="alert alert-danger">
                            <strong>Import Failed:</strong> ${data.error}
                        </div>
                    `;
                }
            })
            .catch(error => {
                btn.disabled = false;
                btn.innerHTML = originalText;
                statusDiv.innerHTML = `
                    <div class="alert alert-danger">
                        <strong>Error:</strong> Failed to import gameweek data
                    </div>
                `;
                console.error('Error:', error);
            });
    });
    
    // Import Full Season functionality
    document.getElementById('import-season-btn').addEventListener('click', function() {
        const btn = this;
        const originalText = btn.innerHTML;
        const statusDiv = document.getElementById('refresh-status');
        
        // Confirm before proceeding
        if (!confirm('This will import all gameweeks for the 2025-26 season. This may take several minutes. Continue?')) {
            return;
        }
        
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Importing Season...';
        statusDiv.innerHTML = '<div class="alert alert-info">Importing full season data from FPL API... This may take several minutes.</div>';
        
        fetch('/api/import_season/', {method: 'POST'})
            .then(response => response.json())
            .then(data => {
                btn.disabled = false;
                btn.innerHTML = originalText;
                
                if (data.success) {
                    statusDiv.innerHTML = `
                        <div class="alert alert-success">
                            <strong>Season Import Complete!</strong><br>
                            • Season: ${data.season}<br>
                            • Gameweeks processed: ${data.gameweeks_processed.length}<br>
                            • New matches added: ${data.total_new_matches}<br>
                            • Matches updated: ${data.total_updated_matches}<br>
                            • Matches skipped: ${data.total_skipped_matches}<br>
                            • Errors: ${data.total_errors}<br>
                            • Duration: ${data.duration}
                        </div>
                    `;
                } else {
                    statusDiv.innerHTML = `
                        <div class="alert alert-danger">
                            <strong>Season Import Failed:</strong> ${data.error}
                        </div>
                    `;
                }
            })
            .catch(error => {
                btn.disabled = false;
                btn.innerHTML = originalText;
                statusDiv.innerHTML = `
                    <div class="alert alert-danger">
                        <strong>Error:</strong> Failed to import season data
                    </div>
                `;
                console.error('Error:', error);
            });
    });
    
    // Refresh Fixtures functionality
    document.getElementById('refresh-fixtures-btn').addEventListener('click', function() {
        const statusDiv = document.getElementById('refresh-status');
        statusDiv.innerHTML = '<div class="alert alert-info">Refreshing fixtures...</div>';
        
        fetch('/api/refresh_fixtures/', {method: 'POST'})
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                statusDiv.innerHTML = `<div class="alert alert-success">${data.message}</div>`;
            } else {
                statusDiv.innerHTML = `<div class="alert alert-danger">Error: ${data.error}</div>`;
            }
        })
        .catch(error => {
            statusDiv.innerHTML = `<div class="alert alert-danger">Error: ${error}</div>`;
        });
    });
    
    // Update Positions functionality
    document.getElementById('update-positions-btn').addEventListener('click', function() {
        const statusDiv = document.getElementById('position-status');
        statusDiv.innerHTML = '<div class="alert alert-info">Updating positions and teams...</div>';
        
        fetch('/api/update_positions/', {method: 'POST'})
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                statusDiv.innerHTML = `<div class="alert alert-success">${data.message}</div>`;
            } else {
                statusDiv.innerHTML = `<div class="alert alert-danger">Error: ${data.error}</div>`;
            }
        })
        .catch(error => {
            statusDiv.innerHTML = `<div class="alert alert-danger">Error: ${error}</div>`;
        });
    });
    
    // Update Costs functionality
    document.getElementById('update-costs-btn').addEventListener('click', function() {
        const statusDiv = document.getElementById('position-status');
        statusDiv.innerHTML = '<div class="alert alert-info">Updating player costs from FPL...</div>';
        
        fetch('/api/update_costs/', {method: 'POST'})
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                statusDiv.innerHTML = `<div class="alert alert-success">${data.message}</div>`;
            } else {
                statusDiv.innerHTML = `<div class="alert alert-danger">Error: ${data.error}</div>`;
            }
        })
        .catch(error => {
            statusDiv.innerHTML = `<div class="alert alert-danger">Error: ${error}</div>`;
        });
    });
    
    // Recalculate Elos functionality
    document.getElementById('recalculate-elos-btn').addEventListener('click', function() {
        const statusDiv = document.getElementById('elo-status');
        statusDiv.innerHTML = '<div class="alert alert-info">Recalculating Elo ratings...</div>';
        
        fetch('/api/recalculate_elos/', {method: 'POST'})
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                statusDiv.innerHTML = `<div class="alert alert-success">${data.message}</div>`;
            } else {
                statusDiv.innerHTML = `<div class="alert alert-danger">Error: ${data.error}</div>`;
            }
        })
        .catch(error => {
            statusDiv.innerHTML = `<div class="alert alert-danger">Error: ${error}</div>`;
        });
    });
    
    // Calculate Projected Points functionality
    document.getElementById('calculate-projected-btn').addEventListener('click', function() {
        const btn = this;
        const originalText = btn.innerHTML;
        const statusDiv = document.getElementById('projected-status');
        
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Calculating...';
        statusDiv.innerHTML = '<div class="alert alert-info">Calculating projected points for all players...</div>';
        
        fetch('/api/calculate_projected_points/', {method: 'POST'})
        .then(response => response.json())
        .then(data => {
            btn.disabled = false;
            btn.innerHTML = originalText;
            
            if (data.success) {
                statusDiv.innerHTML = `
                    <div class="alert alert-success">
                        <strong>Projected Points Calculation Complete!</strong><br>
                        • Fixtures created: ${data.fixtures_created}<br>
                        • Total projections: ${data.total_projections}<br>
                        • Successful players: ${data.successful_players}<br>
                        • Failed players: ${data.failed_players}<br>
                        • Total players: ${data.total_players}
                    </div>
                `;
            } else {
                statusDiv.innerHTML = `
                    <div class="alert alert-danger">
                        <strong>Error:</strong> ${data.error}
                    </div>
                `;
            }
        })
        .catch(error => {
            btn.disabled = false;
            btn.innerHTML = originalText;
            statusDiv.innerHTML = `<div class="alert alert-danger">Error: ${error}</div>`;
        });
    });
    
    // Recalculate Difficulty Multipliers functionality
    document.getElementById('recalculate-multipliers-btn').addEventListener('click', function() {
        const btn = this;
        const originalText = btn.innerHTML;
        const statusDiv = document.getElementById('multipliers-status');
        
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Recalculating...';
        statusDiv.innerHTML = '<div class="alert alert-info">Recalculating difficulty multipliers using current season data...</div>';
        
        fetch('/api/recalculate_multipliers/', {method: 'POST'})
        .then(response => response.json())
        .then(data => {
            btn.disabled = false;
            btn.innerHTML = originalText;
            
            if (data.success) {
                statusDiv.innerHTML = `
                    <div class="alert alert-success">
                        <strong>Difficulty Multipliers Recalculated!</strong><br>
                        • Matches processed: ${data.matches_processed}<br>
                        • Multipliers updated:<br>
                        ${Object.entries(data.multipliers).map(([diff, mult]) => 
                            `&nbsp;&nbsp;Difficulty ${diff}: ${mult}x`
                        ).join('<br>')}
                    </div>
                `;
            } else {
                statusDiv.innerHTML = `
                    <div class="alert alert-danger">
                        <strong>Error:</strong> ${data.error}
                    </div>
                `;
            }
        })
        .catch(error => {
            btn.disabled = false;
            btn.innerHTML = originalText;
            statusDiv.innerHTML = `<div class="alert alert-danger">Error: ${error}</div>`;
        });
    });
});