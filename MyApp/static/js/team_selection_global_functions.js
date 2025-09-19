// Load squad and players when page loads
window.onload = function() {
    console.log('Page loaded, initializing...');
    loadCurrentSquadFromDatabase();
    loadAllPlayers();
    // Load recommendations after squad is loaded
    setTimeout(function() {
        loadSubstituteRecommendations();
    }, 2000);
};

// Global functions for testing
window.dynamicSearch = {
    filterByPosition,
    resetFilters,
    initializeWithServerData,
    dynamicAllPlayers,
    dynamicFilteredPlayers,
    serverPlayers: window.serverPlayers
};

console.log('✅ Server-based player search script loaded!');