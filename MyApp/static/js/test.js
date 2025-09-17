console.log("🧪 Simple JavaScript test - this should appear in browser console");

// Test if the DOM elements exist
document.addEventListener('DOMContentLoaded', function() {
    console.log("🔍 DOM loaded, checking elements...");
    
    const squadContent = document.getElementById("squad-content");
    const generateBtn = document.getElementById("btn-generate-squads");
    const formationSelect = document.getElementById("formation-select");
    
    console.log("Elements found:", {
        squadContent: !!squadContent,
        generateBtn: !!generateBtn,
        formationSelect: !!formationSelect
    });
    
    if (squadContent) {
        squadContent.innerHTML = "<p>🧪 JavaScript is working! This is a test message.</p>";
        console.log("✅ Test message added to squad-content");
    } else {
        console.error("❌ squad-content element not found!");
    }
    
    // Test if the global fantasysquads variable exists
    if (typeof fantasysquads !== 'undefined') {
        console.log("📊 fantasysquads variable exists:", fantasysquads);
    } else {
        console.log("⚠️ fantasysquads variable not defined yet");
    }
});