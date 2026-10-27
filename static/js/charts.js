// ChatBond AI - Chart.js Visualizations
function initDashboardCharts(chartsData) {
  if (!chartsData) return;

  const emeraldGreen = '#128C7E';
  const lightGreen = '#25D366';
  const darkGreen = '#075E54';
  const mintColor = '#D0F5E3';
  const accentYellow = '#F59E0B';
  const palette = ['#128C7E', '#25D366', '#075E54', '#34B7F1', '#E09F3E', '#9B51E0', '#FF6B6B'];

  // 1. Messages per Participant (Bar Chart)
  const participantCanvas = document.getElementById('participantChart');
  if (participantCanvas && chartsData.participant_labels) {
    new Chart(participantCanvas, {
      type: 'bar',
      data: {
        labels: chartsData.participant_labels,
        datasets: [{
          label: 'Total Messages',
          data: chartsData.participant_counts,
          backgroundColor: palette.slice(0, chartsData.participant_labels.length),
          borderRadius: 8,
          borderWidth: 0
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: '#111B21',
            padding: 10,
            cornerRadius: 6
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            grid: { color: '#F0F2F5' }
          },
          x: {
            grid: { display: false }
          }
        }
      }
    });
  }

  // 2. Participant Message Share (Doughnut Chart)
  const shareCanvas = document.getElementById('shareChart');
  if (shareCanvas && chartsData.participant_labels) {
    new Chart(shareCanvas, {
      type: 'doughnut',
      data: {
        labels: chartsData.participant_labels,
        datasets: [{
          data: chartsData.participant_counts,
          backgroundColor: palette.slice(0, chartsData.participant_labels.length),
          borderWidth: 2,
          borderColor: '#FFFFFF'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'bottom',
            labels: {
              boxWidth: 14,
              padding: 16,
              font: { size: 12 }
            }
          }
        },
        cutout: '68%'
      }
    });
  }

  // 3. Daily Messaging Timeline (Line Chart)
  const dailyCanvas = document.getElementById('dailyChart');
  if (dailyCanvas && chartsData.daily_labels) {
    new Chart(dailyCanvas, {
      type: 'line',
      data: {
        labels: chartsData.daily_labels,
        datasets: [{
          label: 'Messages',
          data: chartsData.daily_counts,
          borderColor: emeraldGreen,
          backgroundColor: 'rgba(18, 140, 126, 0.1)',
          fill: true,
          tension: 0.35,
          pointBackgroundColor: emeraldGreen,
          pointBorderColor: '#ffffff',
          pointHoverRadius: 6,
          pointRadius: 4
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false }
        },
        scales: {
          y: {
            beginAtZero: true,
            grid: { color: '#F0F2F5' }
          },
          x: {
            grid: { display: false }
          }
        }
      }
    });
  }

  // 4. Most Used Emojis (Horizontal Bar Chart)
  const emojiCanvas = document.getElementById('emojiChart');
  if (emojiCanvas && chartsData.top_emoji_labels && chartsData.top_emoji_labels.length > 0) {
    new Chart(emojiCanvas, {
      type: 'bar',
      data: {
        labels: chartsData.top_emoji_labels,
        datasets: [{
          label: 'Times Used',
          data: chartsData.top_emoji_counts,
          backgroundColor: '#34B7F1',
          borderRadius: 6
        }]
      },
      options: {
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false }
        },
        scales: {
          x: {
            beginAtZero: true,
            grid: { color: '#F0F2F5' }
          },
          y: {
            grid: { display: false },
            ticks: { font: { size: 18 } }
          }
        }
      }
    });
  }

  // 5. Hourly Activity Heatmap / Bar (24 hours)
  const hourlyCanvas = document.getElementById('hourlyChart');
  if (hourlyCanvas && chartsData.hourly_counts) {
    const hourLabels = [
      '12 AM', '1 AM', '2 AM', '3 AM', '4 AM', '5 AM',
      '6 AM', '7 AM', '8 AM', '9 AM', '10 AM', '11 AM',
      '12 PM', '1 PM', '2 PM', '3 PM', '4 PM', '5 PM',
      '6 PM', '7 PM', '8 PM', '9 PM', '10 PM', '11 PM'
    ];

    new Chart(hourlyCanvas, {
      type: 'bar',
      data: {
        labels: hourLabels,
        datasets: [{
          label: 'Messages',
          data: chartsData.hourly_counts,
          backgroundColor: lightGreen,
          borderRadius: 4
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false }
        },
        scales: {
          y: {
            beginAtZero: true,
            grid: { color: '#F0F2F5' }
          },
          x: {
            grid: { display: false },
            ticks: {
              maxRotation: 45,
              minRotation: 45,
              font: { size: 10 }
            }
          }
        }
      }
    });
  }
}
