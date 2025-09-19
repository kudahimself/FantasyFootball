

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
