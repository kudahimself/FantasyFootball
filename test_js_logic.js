// Test JavaScript logic with actual data structure
console.log("🧪 Testing JavaScript squad processing logic...");

// Simulate the data structure returned by the backend
const sampleSquad = {
    squad_number: 1,
    positions: [1, 3, 4, 3],
    goalkeepers: [
        { name: "David Raya", elo: 1314.0, cost: 5.5, team: "Arsenal" }
    ],
    defenders: [
        { name: "Virgil van Dijk", elo: 1450.0, cost: 6.5, team: "Liverpool" },
        { name: "Ruben Dias", elo: 1420.0, cost: 6.0, team: "Man City" },
        { name: "John Stones", elo: 1380.0, cost: 5.5, team: "Man City" }
    ],
    midfielders: [
        { name: "Kevin De Bruyne", elo: 1580.0, cost: 12.0, team: "Man City" },
        { name: "Bruno Fernandes", elo: 1520.0, cost: 8.5, team: "Man United" },
        { name: "Mohamed Salah", elo: 1650.0, cost: 13.0, team: "Liverpool" },
        { name: "Bukayo Saka", elo: 1480.0, cost: 10.0, team: "Arsenal" }
    ],
    forwards: [
        { name: "Erling Haaland", elo: 1750.0, cost: 15.0, team: "Man City" },
        { name: "Harry Kane", elo: 1680.0, cost: 12.5, team: "Bayern Munich" },
        { name: "Alexander Isak", elo: 1420.0, cost: 8.5, team: "Newcastle" }
    ]
};

// Test the data access pattern used in generateFormationGrid
const positions = sampleSquad.positions;
const data = sampleSquad; // This is the key change - passing squad directly instead of squad.players

console.log("📊 Testing data access:");
console.log("Positions:", positions);
console.log("Goalkeepers:", data?.goalkeepers);
console.log("Defenders:", data?.defenders);
console.log("Midfielders:", data?.midfielders);
console.log("Forwards:", data?.forwards);

// Simulate the rows array construction
const rows = [
    { label: 'GK', count: positions[0], players: data?.goalkeepers },
    { label: 'DEF', count: positions[1], players: data?.defenders },
    { label: 'MID', count: positions[2], players: data?.midfielders },
    { label: 'FWD', count: positions[3], players: data?.forwards }
];

console.log("\n🔍 Testing row construction:");
rows.forEach(row => {
    console.log(`${row.label}: count=${row.count}, players=${row.players?.length || 0}`);
    if (row.players && row.players.length > 0) {
        console.log(`  Sample player: ${row.players[0].name}`);
    } else {
        console.log(`  ❌ No players found for ${row.label}`);
    }
});

console.log("\n✅ JavaScript logic test completed!");