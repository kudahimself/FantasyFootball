// Render a squad object to the squad-list element
function renderSquad(squadData) {
    const squadList = document.getElementById('squad-list');
    squadList.innerHTML = '';
    if (!squadData || Object.keys(squadData).length === 0) {
        squadList.innerHTML = '<div style="color:#888;text-align:center;width:100%;">No squad data available.</div>';
        return;
    }

    // Update squad attribute cards
    const attrPoints = document.getElementById('attr-projected-points');
    const attrCost = document.getElementById('attr-team-cost');
    const attrElo = document.getElementById('attr-avg-elo');
    const attrSubs = document.getElementById('attr-subs');

    // Calculate squad attributes
    let totalPoints = 0, totalCost = 0, totalElo = 0, playerCount = 0, subsCount = 0;
    ['goalkeepers','defenders','midfielders','forwards'].forEach(pos => {
        const players = squadData[pos] || [];
        players.forEach((p, idx) => {
            // Assume first 11 are starters, rest are subs
            if (playerCount >= 11) subsCount++;
            totalPoints += Number(p.projected_points) || 0;
            totalCost += Number(p.cost) || 0;
            totalElo += Number(p.elo_rating !== undefined ? p.elo_rating : (p.elo !== undefined ? p.elo : 0)) || 0;
            playerCount++;
        });
    });
    if (attrPoints) attrPoints.textContent = totalPoints ? totalPoints.toFixed(1) : '--';
    if (attrCost) attrCost.textContent = totalCost ? '£' + totalCost.toFixed(1) + 'm' : '--';
    if (attrElo) attrElo.textContent = playerCount ? Math.round(totalElo / playerCount) : '--';
    if (attrSubs) attrSubs.textContent = subsCount;
    const positionOrder = [
        { key: 'goalkeepers', label: 'GKP' },
        { key: 'defenders', label: 'DEF' },
        { key: 'midfielders', label: 'MID' },
        { key: 'forwards', label: 'FWD' }
    ];
    positionOrder.forEach(pos => {
        const players = squadData[pos.key] || [];
        if (players.length > 0) {
            const rowDiv = document.createElement('div');
            rowDiv.className = 'squad-row';
            players.forEach(playerObj => {
                const card = document.createElement('div');
                // Only show first name
                // Only show last name
                let lastName = '';
                if (playerObj.name) {
                    const nameParts = playerObj.name.trim().split(' ');
                    lastName = nameParts.length > 1 ? nameParts[nameParts.length - 1] : nameParts[0];
                }
                card.innerHTML = `
                    <div class="player-svg-container">
                        <img src="/static/img/player.png" width="90" height="90" alt="Player Icon" />
                    </div>
                    <div class="player-svg-name">${lastName}</div>
                `;
                rowDiv.appendChild(card);
            });
            squadList.appendChild(rowDiv);
        }
    });
}
// Fantasy Football Home Page JS

document.addEventListener('DOMContentLoaded', function() {
    fetchAndRenderSquad();
});

function fetchAndRenderSquad() {
    const squadList = document.getElementById('squad-list');
    squadList.innerHTML = '<div style="color:#888;text-align:center;width:100%;">Loading squad...</div>';
    fetch('/api/current_squad/')
        .then(response => response.json())
        .then(data => {
            if (!data || !data.current_squad || Object.keys(data.current_squad).length === 0) {
                squadList.innerHTML = '<div style="color:#888;text-align:center;width:100%;">No squad data available.</div>';
                return;
            }
            renderSquad(data.current_squad);
        })
        .catch(() => {
            squadList.innerHTML = '<div style="color:#888;text-align:center;width:100%;">No squad data available.</div>';
        });
}

function renderSquadFromApi(squadData) {
    const squadList = document.getElementById('squad-list');
    squadList.innerHTML = '';
    const positionMap = {
        'goalkeepers': 'GKP',
        'defenders': 'DEF',
        'midfielders': 'MID',
        'forwards': 'FWD'
    };
    Object.keys(positionMap).forEach(posKey => {
        const players = squadData[posKey] || [];
        players.forEach(playerObj => {
            const card = document.createElement('div');
            card.className = 'player-card';
            card.innerHTML = `
                <div class="player-name">${playerObj.name} <span class="player-badge">${positionMap[posKey]}</span></div>
                <div class="player-team">${playerObj.team || ''}</div>
                <div class="player-meta">ELO: ${playerObj.elo_rating !== undefined ? playerObj.elo_rating : (playerObj.elo !== undefined ? playerObj.elo : '--')}</div>
                <div class="player-meta">Cost: £${playerObj.cost !== undefined ? playerObj.cost : '--'}m</div>
                <div class="player-meta">Projected: ${playerObj.projected_points !== undefined ? playerObj.projected_points : '--'} pts</div>
            `;
            squadList.appendChild(card);
        });
    });
}
