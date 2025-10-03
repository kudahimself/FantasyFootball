// squads.js

/**
 * Updates the projected points display for a specific player.
 * @param {object} player The player object containing projected points data.
 * @param {number} selectedGw The currently selected Gameweek.
 */
function updateProjectedPoints(player, selectedGw) {
    // 1. Construct the unique ID for the player's points element
    const pointsElementId = `projected-points-${player.id}`;
    const pointsElement = document.getElementById(pointsElementId);

    if (pointsElement) {
        // 2. Safely access the points using bracket notation and the GW number
        const pointsData = player.projected_points_by_gw || {};
        const points = pointsData[selectedGw] || 0; // Default to 0 if not found
        
        // 3. Update the element's content
        pointsElement.textContent = points;
    }
}

// Example usage:
// updateProjectedPoints(myPlayerObject, window.selectedgw);