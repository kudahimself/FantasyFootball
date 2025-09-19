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
                card.className = 'player-card player-svg-card';
                // Only show first name
                const firstName = playerObj.name ? playerObj.name.split(' ')[0] : '';
                card.innerHTML = `
                    <div class=\"player-svg-container\">
                        <svg viewBox=\"0 0 423.997 423.997\" width=\"54\" height=\"54\" xmlns=\"http://www.w3.org/2000/svg\">
                            <g>
                                <path style=\"fill:#D83935;\" d=\"M343.7,334.607v89.39H80.3v-89.39c0-18.58,6.24-35.69,16.74-49.37c11.9-15.49,29.27-26.56,49.21-30.33c4.91-0.93,9.99-1.42,15.17-1.42h101.16c5.18,0,10.26,0.49,15.17,1.42c19.94,3.77,37.31,14.84,49.21,30.33C337.46,298.917,343.7,316.027,343.7,334.607z\"/>
                                <path style=\"fill:#FFD3AE;\" d=\"M343.697,372.817h-60.081l0,0c-3.166,12.181-3.856,24.873-2.031,37.325l2.031,13.855h60.081l2.545-23.082C347.283,391.473,346.418,381.918,343.697,372.817L343.697,372.817z\"/>
                                <path style=\"fill:#C42C2C;\" d=\"M263.565,254.903v5.68c0,13.79-5.36,26.73-15.11,36.46c-9.73,9.74-22.68,15.1-36.46,15.1c-28.43,0-51.56-23.13-51.56-51.56v-5.68c4.91-0.93,9.99-1.42,15.17-1.42h72.79C253.575,253.483,258.655,253.973,263.565,254.903z\"/>
                                <path style=\"fill:#FFD3AE;\" d=\"M255.565,230.817v29.77c0,12.02-4.87,22.92-12.76,30.8c-7.88,7.88-18.78,12.76-30.81,12.76c-24.06,0-43.56-19.5-43.56-43.56v-29.77H255.565z\"/>
                                <path style=\"fill:#E5B591;\" d=\"M255.565,236.817v24.06c-12.86,7.29-27.73,11.45-43.57,11.45s-30.7-4.16-43.56-11.45v-24.06L255.565,236.817L255.565,236.817z\"/>
                                <g>
                                    <g>
                                        <circle style=\"fill:#E5B591;\" cx=\"131.432\" cy=\"140\" r=\"27.89\"/>
                                        <circle style=\"fill:#E5B591;\" cx=\"292.567\" cy=\"140\" r=\"27.89\"/>
                                    </g>
                                </g>
                                <path style=\"fill:#FFD3AE;\" d=\"M261.36,235.97C247.26,245.46,230.28,251,212,251s-35.26-5.54-49.36-15.03c-0.19-0.13-0.39-0.26-0.58-0.4c-23.28-15.94-38.56-42.72-38.56-73.07V140V88.5C123.5,39.623,163.122,0,212,0l0,0c48.877,0,88.5,39.623,88.5,88.5V140v22.5c0,30.35-15.28,57.13-38.56,73.07C261.75,235.71,261.55,235.84,261.36,235.97z\"/>
                                <g>
                                    <path style=\"fill:#E5B591;\" d=\"M164.869,139.333h35.044c6.522,0,11.81,5.287,11.81,11.81v21.123c0,5.092,4.128,9.22,9.22,9.22h6.748l-2.943,1.044c-7.666,2.72-16.214,0.773-21.946-4.999L164.869,139.333z\"/>
                                </g>
                                <g>
                                    <path style=\"fill:#333333;\" d=\"M178,160.437c-1.58,0-3.13-0.64-4.24-1.75c-1.12-1.12-1.76-2.67-1.76-4.25s0.64-3.12,1.76-4.24c1.39-1.39,3.46-2.03,5.41-1.64c0.39,0.08,0.76,0.19,1.13,0.34c0.36,0.15,0.71,0.34,1.03,0.55c0.33,0.22,0.64,0.47,0.91,0.75c0.28,0.28,0.53,0.58,0.75,0.91s0.4,0.68,0.55,1.04c0.15,0.36,0.27,0.74,0.34,1.12c0.08,0.39,0.12,0.78,0.12,1.17s-0.04,0.79-0.12,1.18c-0.07,0.38-0.19,0.76-0.34,1.12s-0.33,0.71-0.55,1.03c-0.22,0.33-0.47,0.64-0.75,0.92C181.13,159.797,179.58,160.437,178,160.437z\"/>
                                    <path style=\"fill:#333333;\" d=\"M246,160.437c-0.39,0-0.79-0.04-1.17-0.11c-0.38-0.08-0.76-0.2-1.12-0.35c-0.37-0.15-0.71-0.33-1.04-0.55c-0.33-0.22-0.64-0.47-0.91-0.74c-0.28-0.28-0.53-0.59-0.75-0.92c-0.22-0.32-0.4-0.67-0.55-1.03c-0.15-0.36-0.27-0.74-0.34-1.12c-0.08-0.39-0.12-0.79-0.12-1.18s0.04-0.78,0.12-1.17c0.07-0.38,0.19-0.76,0.34-1.12s0.33-0.71,0.55-1.04c0.22-0.33,0.47-0.63,0.75-0.91c0.27-0.28,0.58-0.53,0.91-0.75c0.33-0.21,0.67-0.4,1.04-0.55c0.36-0.15,0.74-0.26,1.12-0.34c1.95-0.39,4.02,0.25,5.41,1.64c0.28,0.28,0.53,0.58,0.75,0.91s0.4,0.68,0.55,1.04c0.15,0.36,0.27,0.74,0.34,1.12c0.08,0.39,0.12,0.78,0.12,1.17s-0.04,0.79-0.12,1.18c-0.07,0.38-0.19,0.76-0.34,1.12s-0.33,0.71-0.55,1.03c-0.22,0.33-0.47,0.64-0.75,0.92C249.13,159.797,247.58,160.437,246,160.437z\"/>
                                </g>
                                <g>
                                    <path style=\"fill:#333333;\" d=\"M188.937,142.333h-21.875c-3.087,0-5.59-2.503-5.59-5.59l0,0c0-3.087,2.503-5.59,5.59-5.59h21.875c3.087,0,5.59,2.503,5.59,5.59l0,0C194.527,139.831,192.025,142.333,188.937,142.333z\"/>
                                    <path style=\"fill:#333333;\" d=\"M256.937,142.333h-21.875c-3.087,0-5.59-2.503-5.59-5.59l0,0c0-3.087,2.503-5.59,5.59-5.59h21.875c3.087,0,5.59,2.503,5.59,5.59l0,0C262.527,139.831,260.025,142.333,256.937,142.333z\"/>
                                </g>
                                <path style=\"fill:#FFFFFF;\" d=\"M237.235,193.997c0,2.98-0.52,5.83-1.48,8.49c-0.45,1.28-1.01,2.51-1.65,3.68c-4.3,7.78-12.58,13.05-22.1,13.05c-9.53,0-17.81-5.27-22.11-13.05c-0.65-1.17-1.21-2.4-1.66-3.68c-0.96-2.66-1.47-5.51-1.47-8.49H237.235z\"/>
                                <path style=\"fill:#333333;\" d=\"M235.76,202.487c-0.45,1.28-1.01,2.51-1.65,3.68c-4.3,7.78-12.58,13.05-22.1,13.05c-9.53,0-17.81-5.27-22.11-13.05c-0.65-1.17-1.21-2.4-1.66-3.68H235.76z\"/>
                                <rect x=\"283.616\" y=\"361.607\" style=\"fill:#C42C2C;\" width=\"60.081\" height=\"11.21\"/>
                                <g>
                                    <path style=\"fill:#FFD3AE;\" d=\"M80.3,372.817h60.081l0,0c3.166,12.181,3.857,24.873,2.031,37.325l-2.031,13.855H80.3l-2.545-23.082C76.714,391.473,77.579,381.918,80.3,372.817L80.3,372.817z\"/>
                                    <rect x=\"80.3\" y=\"361.607\" style=\"fill:#C42C2C;\" width=\"60.081\" height=\"11.21\"/>
                                </g>
                                <rect x=\"155.25\" y=\"398.941\" style=\"fill:#C42C2C;\" width=\"113.5\" height=\"6\"/>
                            </g>
                        </svg>
                    </div>
                    <div class=\"player-svg-name\">${firstName}</div>
                    <div class=\"player-svg-badge\">${pos.label}</div>
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
