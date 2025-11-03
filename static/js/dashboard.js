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
      console.error('Lỗi làm mới dữ liệu:', error);
      this.showError('Lỗi làm mới dữ liệu. Vui lòng thử lại.');
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
    } catch (error) {
      console.error('Error updating summary:', error);
    }
  }

  async updateGarageMap() {
    try {
      const response = await fetch('/api/map');
      if (!response.ok) throw new Error('Failed to fetch map');

      const slots = await response.json();
      this.renderGarageMap(slots);
    } catch (error) {
      console.error('Lỗi cập nhật sơ đồ garage:', error);
      document.getElementById('garage-map').innerHTML = '<div class="loading">Lỗi tải sơ đồ garage</div>';
    }
  }

  renderGarageMap(mapData) {
    const container = document.getElementById('garage-map');
    container.innerHTML = '';
    // Render all slots in a row
    mapData.forEach(slot => {
      const slotElement = document.createElement('div');
      slotElement.className = 'parking-slot';
      slotElement.textContent = slot.slot_id;
      slotElement.classList.add(slot.occupied ? 'occupied' : 'available');
      slotElement.title = `${slot.slot_id}: ${slot.occupied ? 'Đã có xe' : 'Còn trống'}`;
      slotElement.addEventListener('click', () => {
        this.showSlotDetails(slot);
      });
      container.appendChild(slotElement);
    });
  }

  async updateCarLog() {
    try {
      const response = await fetch('/api/car_log?limit=10');
      if (!response.ok) throw new Error('Failed to fetch car log');

      const data = await response.json();
      this.renderCarLog(data);
    } catch (error) {
      console.error('Lỗi cập nhật nhật ký xe:', error);
      document.getElementById('car-log').innerHTML = '<div class="loading">Lỗi tải sự kiện xe</div>';
    }
  }

  renderCarLog(events) {
    const container = document.getElementById('car-log');

    if (events.length === 0) {
      container.innerHTML = '<div class="loading">Không có sự kiện xe nào được ghi lại</div>';
      return;
    }

    container.innerHTML = events.map((event, idx) => `
      <div class="log-entry">
        <div>
          <span class="log-plate">${event.plate}</span>
          <span class="log-event ${event.event}">${event.event}</span>
        </div>
        <div style="display: flex; align-items: center; gap: 0.5rem; position:relative;">
          <span class="log-time">${this.formatTime(event.timestamp)}</span>
          ${event.image_path ? `
            <button class="view-image-btn" data-img="${event.image_path}">Xem</button>
          ` : ''}
        </div>
      </div>
    `).join('');

    // Modal logic
    const modal = document.getElementById('image-modal');
    const modalImg = document.getElementById('modal-img');
    const closeModal = document.getElementById('close-modal');
    document.querySelectorAll('.view-image-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const imgSrc = btn.getAttribute('data-img');
        modalImg.src = imgSrc;
        modal.style.display = 'flex';
      });
    });
    if (closeModal) {
      closeModal.onclick = () => {
        modal.style.display = 'none';
        modalImg.src = '';
      };
    }
    if (modal) {
      modal.onclick = (e) => {
        if (e.target === modal) {
          modal.style.display = 'none';
          modalImg.src = '';
        }
      };
    }
  }

  async updateOccupancyHistory() {
    try {
      const response = await fetch('/api/history?limit=15');
      if (!response.ok) throw new Error('Failed to fetch history');

      const data = await response.json();
      this.renderOccupancyHistory(data);
    } catch (error) {
      console.error('Lỗi cập nhật lịch sử chỗ:', error);
      document.getElementById('occupancy-history').innerHTML = '<div class="loading">Lỗi tải lịch sử chỗ</div>';
    }
  }

  renderOccupancyHistory(history) {
    const container = document.getElementById('occupancy-history');

    if (history.length === 0) {
      container.innerHTML = '<div class="loading">Không có thay đổi chỗ nào được ghi lại</div>';
      return;
    }

    container.innerHTML = history.map(entry => `
            <div class="log-entry">
                <div>
                    <span class="log-plate">${entry.slot_id}</span>
                    <span class="log-event ${entry.occupied ? 'enter' : 'exit'}">
                        ${entry.occupied ? 'Đã có xe' : 'Còn trống'}
                    </span>
                </div>
                <div class="log-time">${this.formatTime(entry.timestamp)}</div>
            </div>
        `).join('');
  }

  showSlotDetails(slot) {
    const status = slot.occupied ? 'Đã có xe' : 'Còn trống';
    const lastUpdate = slot.updated_at ? this.formatTime(slot.updated_at) : 'Không rõ';

    alert(`Chi tiết chỗ:\n\nID chỗ: ${slot.slot_id}\nTrạng thái: ${status}\nCập nhật lần cuối: ${lastUpdate}`);
  }

  formatTime(timestamp) {
    const date = new Date(timestamp);
    // Vietnamese format: HH:mm DD/MM/YYYY (no seconds)
    const pad = n => n.toString().padStart(2, '0');
    const hours = pad(date.getHours());
    const minutes = pad(date.getMinutes());
    const day = pad(date.getDate());
    const month = pad(date.getMonth() + 1);
    const year = date.getFullYear().toString().slice(-2);
    return `${hours}:${minutes} ${day}/${month}/${year}`;
  }

  startAutoRefresh() {
    // Get refresh interval from environment or fallback to 3000ms
    const refreshInterval = window.ENV?.REFRESH_INTERVAL || 3000;
    this.refreshInterval = setInterval(() => {
      this.refreshData();
    }, refreshInterval);
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