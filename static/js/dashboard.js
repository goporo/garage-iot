// Dashboard JavaScript for IoT Garage System

class GarageDashboard {
  constructor() {
    this.refreshInterval = null;
    this.init();
  }

  async init() {
    await this.refreshData();
    this.startAutoRefresh();
  }

  async refreshData() {
    try {
      await Promise.all([
        this.updateSummary(),
        this.updateGarageMap(),
        this.updateCarLog(),
        this.updateOccupancyHistory()
      ]);
    } catch (error) {
      console.error('Error refreshing data:', error);
      this.showError('Failed to refresh data. Please try again.');
    }
  }

  async updateSummary() {
    try {
      const response = await fetch('/api/summary');
      if (!response.ok) throw new Error('Failed to fetch summary');

      const data = await response.json();

      document.getElementById('total-slots').textContent = data.total;
      document.getElementById('occupied-slots').textContent = data.occupied;
      document.getElementById('available-slots').textContent = data.available;
      document.getElementById('occupancy-rate').textContent = `${data.occupancy_rate}%`;
    } catch (error) {
      console.error('Error updating summary:', error);
    }
  }

  async updateGarageMap() {
    try {
      const response = await fetch('/api/map');
      if (!response.ok) throw new Error('Failed to fetch map');

      const data = await response.json();
      this.renderGarageMap(data);
    } catch (error) {
      console.error('Error updating garage map:', error);
      document.getElementById('garage-map').innerHTML = '<div class="loading">Error loading garage map</div>';
    }
  }

  renderGarageMap(mapData) {
    const container = document.getElementById('garage-map');

    // Set grid layout
    container.style.gridTemplateColumns = `repeat(${mapData.cols}, 1fr)`;
    container.style.gridTemplateRows = `repeat(${mapData.rows}, 1fr)`;

    // Create a 2D array to organize slots
    const grid = Array(mapData.rows).fill().map(() => Array(mapData.cols).fill(null));

    // Fill grid with slots
    mapData.slots.forEach(slot => {
      if (slot.x < mapData.cols && slot.y < mapData.rows) {
        grid[slot.y][slot.x] = slot;
      }
    });

    // Render grid
    container.innerHTML = '';
    grid.forEach((row, y) => {
      row.forEach((slot, x) => {
        const slotElement = document.createElement('div');
        slotElement.className = 'parking-slot';

        if (slot) {
          slotElement.textContent = slot.slot_id;
          slotElement.classList.add(slot.occupied ? 'occupied' : 'available');
          slotElement.title = `${slot.slot_id}: ${slot.occupied ? 'Occupied' : 'Available'}`;

          // Add click handler for slot details
          slotElement.addEventListener('click', () => {
            this.showSlotDetails(slot);
          });
        } else {
          slotElement.style.visibility = 'hidden';
        }

        container.appendChild(slotElement);
      });
    });
  }

  async updateCarLog() {
    try {
      const response = await fetch('/api/car_log?limit=10');
      if (!response.ok) throw new Error('Failed to fetch car log');

      const data = await response.json();
      this.renderCarLog(data);
    } catch (error) {
      console.error('Error updating car log:', error);
      document.getElementById('car-log').innerHTML = '<div class="loading">Error loading car events</div>';
    }
  }

  renderCarLog(events) {
    const container = document.getElementById('car-log');

    if (events.length === 0) {
      container.innerHTML = '<div class="loading">No car events recorded</div>';
      return;
    }

    container.innerHTML = events.map(event => `
            <div class="log-entry">
                <div>
                    <span class="log-plate">${event.plate}</span>
                    <span class="log-event ${event.event}">${event.event}</span>
                </div>
                <div class="log-time">${this.formatTime(event.timestamp)}</div>
            </div>
        `).join('');
  }

  async updateOccupancyHistory() {
    try {
      const response = await fetch('/api/history?limit=15');
      if (!response.ok) throw new Error('Failed to fetch history');

      const data = await response.json();
      this.renderOccupancyHistory(data);
    } catch (error) {
      console.error('Error updating occupancy history:', error);
      document.getElementById('occupancy-history').innerHTML = '<div class="loading">Error loading occupancy history</div>';
    }
  }

  renderOccupancyHistory(history) {
    const container = document.getElementById('occupancy-history');

    if (history.length === 0) {
      container.innerHTML = '<div class="loading">No occupancy changes recorded</div>';
      return;
    }

    container.innerHTML = history.map(entry => `
            <div class="log-entry">
                <div>
                    <span class="log-plate">${entry.slot_id}</span>
                    <span class="log-event ${entry.occupied ? 'enter' : 'exit'}">
                        ${entry.occupied ? 'Occupied' : 'Available'}
                    </span>
                </div>
                <div class="log-time">${this.formatTime(entry.timestamp)}</div>
            </div>
        `).join('');
  }

  showSlotDetails(slot) {
    const status = slot.occupied ? 'Occupied' : 'Available';
    const lastUpdate = slot.updated_at ? this.formatTime(slot.updated_at) : 'Unknown';

    alert(`Slot Details:\n\nSlot ID: ${slot.slot_id}\nStatus: ${status}\nPosition: (${slot.x}, ${slot.y})\nLast Updated: ${lastUpdate}`);
  }

  formatTime(timestamp) {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;

    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }

  startAutoRefresh() {
    // Refresh every 30 seconds
    this.refreshInterval = setInterval(() => {
      this.refreshData();
    }, 30000);
  }

  stopAutoRefresh() {
    if (this.refreshInterval) {
      clearInterval(this.refreshInterval);
      this.refreshInterval = null;
    }
  }

  showError(message) {
    // Simple error notification
    const errorDiv = document.createElement('div');
    errorDiv.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #e74c3c;
            color: white;
            padding: 1rem;
            border-radius: 5px;
            z-index: 1000;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        `;
    errorDiv.textContent = message;
    document.body.appendChild(errorDiv);

    setTimeout(() => {
      document.body.removeChild(errorDiv);
    }, 5000);
  }
}

// Global function for refresh button
function refreshData() {
  if (window.dashboard) {
    window.dashboard.refreshData();
  }
}

// Initialize dashboard when page loads
document.addEventListener('DOMContentLoaded', () => {
  window.dashboard = new GarageDashboard();
});

// Clean up on page unload
window.addEventListener('beforeunload', () => {
  if (window.dashboard) {
    window.dashboard.stopAutoRefresh();
  }
});