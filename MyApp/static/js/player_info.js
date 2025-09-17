// player_info.js
// Requires Chart.js to be loaded in the template

document.addEventListener('DOMContentLoaded', function() {
    // Debug: log the Elo data to the console
    console.log('Elo Data:', window.eloData);
    // If Chart.js didn't load for any reason, show fallback and bail out gracefully
    if (typeof Chart === 'undefined') {
        console.error('Chart.js is not available. Ensure the CDN script is loading.');
        const eloDataElem = document.getElementById('eloChart');
        const fallbackElem = document.getElementById('eloChartFallback');
        if (eloDataElem) eloDataElem.style.display = 'none';
        if (fallbackElem) {
            fallbackElem.textContent = 'Chart library failed to load. Please refresh or check your network.';
            fallbackElem.style.display = '';
        }
        return;
    }
    // Elo History Chart
    const eloDataElem = document.getElementById('eloChart');
    const fallbackElem = document.getElementById('eloChartFallback');
    if (eloDataElem && window.eloData && Array.isArray(window.eloData.dates) && window.eloData.dates.length > 0) {
        if (fallbackElem) fallbackElem.style.display = 'none';
        eloDataElem.style.display = '';
        const ctx = eloDataElem.getContext('2d');
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: window.eloData.dates,
                datasets: [{
                    label: 'Elo Rating',
                    data: window.eloData.elos,
                    borderColor: 'rgb(75, 192, 192)',
                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 4,
                    pointHoverRadius: 6
                }]
            },
            options: {
                responsive: true,
                interaction: {
                    intersect: false,
                    mode: 'nearest',
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    title: {
                        display: true,
                        text: window.playerName + ' - Elo Rating Progression'
                    },
                    tooltip: {
                        enabled: true,
                        callbacks: {
                            label: function(context) {
                                const date = context.label;
                                const elo = context.parsed.y;
                                return `Date: ${date} | Elo: ${elo}`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        display: true,
                        title: {
                            display: true,
                            text: 'Match Date'
                        }
                    },
                    y: {
                        display: true,
                        title: {
                            display: true,
                            text: 'Elo Rating'
                        }
                    }
                }
            }
        });
    } else if (eloDataElem && fallbackElem) {
        eloDataElem.style.display = 'none';
        fallbackElem.style.display = '';
    }

    // Match search functionality
    const matchSearch = document.getElementById('matchSearch');
    if (matchSearch) {
        matchSearch.addEventListener('keyup', function() {
            const searchTerm = this.value.toLowerCase();
            const tableRows = document.querySelectorAll('#matchesTable tbody tr');
            tableRows.forEach(row => {
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(searchTerm) ? '' : 'none';
            });
        });
    }
});
