// Player Ratings JavaScript Functions

// Global variables for sorting and filtering
let currentSort = { column: '', direction: 'desc' };

/**
 * Sort table by specified column and type
 * @param {string} column - The column to sort by
 * @param {string} type - The data type ('number' or 'string')
 * @param {string} forcedDirection - Optional: force a specific direction ('asc' or 'desc')
 */
function sortTable(column, type, forcedDirection = null) {
    const tbody = document.getElementById('players-tbody');
    const rows = Array.from(tbody.querySelectorAll('tr.player-row'));
    
    // Determine sort direction
    if (forcedDirection) {
        currentSort.direction = forcedDirection;
        currentSort.column = column;
    } else if (currentSort.column === column) {
        currentSort.direction = currentSort.direction === 'asc' ? 'desc' : 'asc';
    } else {
        // Default direction for different columns
        if (column === 'elo' || column === 'cost' || column === 'projectedPoints') {
            currentSort.direction = 'desc'; // Highest first for numeric values
        } else {
            currentSort.direction = 'asc'; // A-Z for text values
        }
        currentSort.column = column;
    }
    
    // Sort rows
    rows.sort((a, b) => {
        let aVal = a.dataset[column];
        let bVal = b.dataset[column];
        
        if (type === 'number') {
            aVal = parseFloat(aVal) || 0;
            bVal = parseFloat(bVal) || 0;
        } else {
            aVal = aVal.toLowerCase();
            bVal = bVal.toLowerCase();
        }
        
        if (aVal < bVal) return currentSort.direction === 'asc' ? -1 : 1;
        if (aVal > bVal) return currentSort.direction === 'asc' ? 1 : -1;
        return 0;
    });
    
    // Update DOM
    rows.forEach(row => tbody.appendChild(row));
    
    // Update header styling
    updateSortHeaders(column);
}

/**
 * Update the visual indicators on table headers
 * @param {string} activeColumn - The currently sorted column
 */
function updateSortHeaders(activeColumn) {
    document.querySelectorAll('.sortable').forEach(th => {
        th.className = 'sortable';
    });
    document.querySelector(`[data-column="${activeColumn}"]`).className = `sortable ${currentSort.direction}`;
}

/**
 * Filter the table based on current filter values
 */
function filterTable() {
    const searchText = document.getElementById('search-player').value.toLowerCase();
    const positionFilter = document.getElementById('filter-position').value;
    const costMin = parseFloat(document.getElementById('filter-cost-min').value) || 0;
    const costMax = parseFloat(document.getElementById('filter-cost-max').value) || 999;
    const eloMin = parseFloat(document.getElementById('filter-elo-min').value) || 0;
    const pointsMin = parseFloat(document.getElementById('filter-points-min').value) || 0;
    
    const rows = document.querySelectorAll('#players-tbody tr.player-row');
    let visibleCount = 0;
    
    rows.forEach(row => {
        const name = row.dataset.name;
        const position = row.dataset.position;
        const cost = parseFloat(row.dataset.cost);
        const elo = parseFloat(row.dataset.elo);
        const projectedPoints = parseFloat(row.dataset.projectedPoints) || 0;
        
        const matchesSearch = !searchText || name.includes(searchText);
        const matchesPosition = !positionFilter || position === positionFilter;
        const matchesCost = cost >= costMin && cost <= costMax;
        const matchesElo = elo >= eloMin;
        const matchesPoints = projectedPoints >= pointsMin;
        
        const shouldShow = matchesSearch && matchesPosition && matchesCost && matchesElo && matchesPoints;
        
        row.style.display = shouldShow ? '' : 'none';
        if (shouldShow) visibleCount++;
    });
    
    updateFilteredCount(visibleCount);
}

/**
 * Update the filtered count display
 * @param {number} count - Number of visible rows
 */
function updateFilteredCount(count) {
    document.getElementById('filtered-count').textContent = count;
}

/**
 * Clear all filters and reset the table
 */
function clearFilters() {
    document.getElementById('search-player').value = '';
    document.getElementById('filter-position').value = '';
    document.getElementById('filter-cost-min').value = '';
    document.getElementById('filter-cost-max').value = '';
    document.getElementById('filter-elo-min').value = '';
    document.getElementById('filter-points-min').value = '';
    filterTable();
}

/**
 * Initialize event listeners for sorting and filtering
 */
function initializeEventListeners() {
    // Add click listeners to sortable headers
    document.querySelectorAll('.sortable').forEach(th => {
        th.addEventListener('click', () => {
            sortTable(th.dataset.column, th.dataset.type);
        });
    });

    // Add event listeners for filters
    document.getElementById('search-player').addEventListener('input', filterTable);
    document.getElementById('filter-position').addEventListener('change', filterTable);
    document.getElementById('filter-cost-min').addEventListener('input', filterTable);
    document.getElementById('filter-cost-max').addEventListener('input', filterTable);
    document.getElementById('filter-elo-min').addEventListener('input', filterTable);
    document.getElementById('filter-points-min').addEventListener('input', filterTable);
}

/**
 * Initialize the page when DOM is loaded
 */
function initializePlayerRatings() {
    initializeEventListeners();
    
    // Initial sort by Projected Points (highest first) - force descending order
    sortTable('projectedPoints', 'number', 'desc');
    
    console.log('Player Ratings page initialized - sorted by Projected Points (highest to lowest)');
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', initializePlayerRatings);