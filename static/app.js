const API_URL = window.location.origin + '/api';
let autoMode = false;
let crops = [];
let sensors = [];
let currentSensorForExport = null;
let loggedIn = false;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    checkLogin();
    setupEventListeners();
});

function setupEventListeners() {
    const loginBtn = document.getElementById('loginBtn');
    if (loginBtn) {
        loginBtn.addEventListener('click', login);
    }
    
    const passwordInput = document.getElementById('password');
    if (passwordInput) {
        passwordInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') login();
        });
    }
    
    document.getElementById('autoModeCard')?.addEventListener('click', toggleAutoMode);
    document.getElementById('scheduleCard')?.addEventListener('click', () => openModal('scheduleModal'));
    document.getElementById('exportBtn')?.addEventListener('click', exportData);
    document.getElementById('addScheduleBtn')?.addEventListener('click', addSchedule);
    document.getElementById('getStartedBtn')?.addEventListener('click', () => {
        document.querySelector('.sensors-section')?.scrollIntoView({ behavior: 'smooth' });
    });
}

function checkLogin() {
    const loginModal = document.getElementById('loginModal');
    if (!loggedIn) {
        loginModal.classList.add('active');
    }
}

async function login() {
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    
    if (!username || !password) {
        alert('Please enter username and password');
        return;
    }
    
    try {
        const response = await fetch(`${API_URL}/login`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({username, password}),
            credentials: 'include'
        });
        
        const data = await response.json();
        if (data.success) {
            loggedIn = true;
            closeModal('loginModal');
            document.getElementById('userProfile').innerHTML = `<span class="user-avatar">👤</span>`;
            await init();
        } else {
            alert('Invalid username or password');
        }
    } catch (error) {
        console.error('Login error:', error);
        alert('Login failed. Please try again.');
    }
}

async function init() {
    try {
        await fetchCrops();
        await fetchSensors();
        await fetchStats();
        startLiveUpdates();
    } catch (error) {
        console.error('Initialization error:', error);
    }
}

async function fetchStats() {
    try {
        const response = await fetch(`${API_URL}/stats`);
        const data = await response.json();
        document.getElementById('avgMoisture').textContent = data.avg_moisture + '%';
        document.getElementById('activeSensors').textContent = data.total_sensors;
        document.getElementById('todayWatering').textContent = data.today_watering;
    } catch (error) {
        console.error('Error fetching stats:', error);
    }
}

async function fetchCrops() {
    try {
        const response = await fetch(`${API_URL}/crops`);
        crops = await response.json();
    } catch (error) {
        console.error('Error fetching crops:', error);
    }
}

async function fetchSensors() {
    try {
        const response = await fetch(`${API_URL}/sensors`);
        sensors = await response.json();
        updateDashboard();
        renderSensors();
    } catch (error) {
        console.error('Error fetching sensors:', error);
    }
}

function updateDashboard() {
    if (sensors.length > 0) {
        const avgMoisture = sensors.reduce((sum, s) => sum + s.current_moisture, 0) / sensors.length;
        document.getElementById('avgMoisture').textContent = avgMoisture.toFixed(1) + '%';
        document.getElementById('activeSensors').textContent = sensors.length;
    }
    fetchStats();
}

function renderSensors() {
    const grid = document.getElementById('sensorsGrid');
    
    grid.innerHTML = sensors.map(sensor => {
        const status = getMoistureStatus(sensor.current_moisture, sensor.min_moisture, sensor.max_moisture);
        const fillClass = sensor.current_moisture < sensor.min_moisture ? 'low' : '';
        
        return `
            <div class="sensor-card">
                <div class="sensor-header">
                    <h3 class="sensor-title">Sensor ${sensor.id}</h3>
                    <span class="sensor-badge badge-${status}">${status.toUpperCase()}</span>
                </div>
                
                <div class="moisture-display">
                    <div class="moisture-value">${sensor.current_moisture.toFixed(1)}%</div>
                    <div class="moisture-bar">
                        <div class="moisture-fill ${fillClass}" style="width: ${sensor.current_moisture}%"></div>
                    </div>
                </div>
                
                <div class="crop-info">
                    <p><strong>Crop:</strong> ${sensor.crop_name}</p>
                    <p><strong>Optimal Range:</strong> ${sensor.min_moisture}% - ${sensor.max_moisture}%</p>
                    <p><strong>Water Amount:</strong> ${sensor.water_amount}ml</p>
                    <select class="crop-select" onchange="changeCrop(${sensor.id}, this.value)">
                        ${crops.map(crop => `
                            <option value="${crop.id}" ${crop.id === sensor.crop_id ? 'selected' : ''}>
                                ${crop.name}
                            </option>
                        `).join('')}
                    </select>
                </div>
                
                <div class="sensor-actions">
                    <button class="btn btn-water" onclick="waterPlant(${sensor.id})">💧 Water Now</button>
                    <button class="btn btn-history" onclick="showHistory(${sensor.id})">📊 History</button>
                </div>
            </div>
        `;
    }).join('');
}

function getMoistureStatus(moisture, minMoisture, maxMoisture) {
    if (moisture >= minMoisture && moisture <= maxMoisture) return 'optimal';
    if (moisture < minMoisture) return moisture < minMoisture * 0.7 ? 'critical' : 'low';
    return 'optimal';
}

async function waterPlant(sensorId) {
    try {
        const response = await fetch(`${API_URL}/sensor/${sensorId}/water`, {
            method: 'POST'
        });
        const data = await response.json();
        
        if (data.success) {
            alert(`Watered! ${data.moisture_before}% → ${data.moisture_after}%`);
            await fetchSensors();
        }
    } catch (error) {
        alert('Watering failed');
    }
}

async function changeCrop(sensorId, cropId) {
    try {
        await fetch(`${API_URL}/sensor/${sensorId}/crop`, {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({crop_id: cropId})
        });
        await fetchSensors();
    } catch (error) {
        alert('Update failed');
    }
}

async function toggleAutoMode() {
    autoMode = !autoMode;
    try {
        await fetch(`${API_URL}/auto-mode`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({enabled: autoMode})
        });
        
        document.getElementById('autoStatus').textContent = autoMode ? 'ON' : 'OFF';
    } catch (error) {
        alert('Failed to toggle');
    }
}

async function showHistory(sensorId) {
    currentSensorForExport = sensorId;
    try {
        const response = await fetch(`${API_URL}/history/${sensorId}`);
        const history = await response.json();
        
        const content = document.getElementById('historyContent');
        content.innerHTML = history.map(log => `
            <div class="history-item">
                <strong>${new Date(log.timestamp).toLocaleString()}</strong><br>
                Moisture: ${log.moisture_before.toFixed(1)}% → ${log.moisture_after.toFixed(1)}%<br>
                Amount: ${log.amount}ml
            </div>
        `).join('');
        
        openModal('historyModal');
    } catch (error) {
        alert('Failed to load history');
    }
}

async function exportData() {
    if (currentSensorForExport) {
        window.location.href = `${API_URL}/export/${currentSensorForExport}`;
    }
}

async function addSchedule() {
    const sensorId = document.getElementById('scheduleSensor').value;
    const time = document.getElementById('scheduleTime').value;
    const days = document.getElementById('scheduleDays').value;
    
    try {
        await fetch(`${API_URL}/schedules`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({sensor_id: sensorId, time, days})
        });
        loadSchedules();
    } catch (error) {
        alert('Failed to add schedule');
    }
}

async function loadSchedules() {
    try {
        const response = await fetch(`${API_URL}/schedules`);
        const schedules = await response.json();
        
        const select = document.getElementById('scheduleSensor');
        select.innerHTML = sensors.map(s => 
            `<option value="${s.id}">Sensor ${s.id} - ${s.crop_name}</option>`
        ).join('');
        
        const list = document.getElementById('scheduleList');
        list.innerHTML = schedules.map(sch => `
            <div class="schedule-item">
                <div>
                    <strong>Sensor ${sch.sensor_id}</strong> at ${sch.time}<br>
                    Days: ${sch.days}
                </div>
                <button class="btn btn-secondary" onclick="deleteSchedule(${sch.id})">Delete</button>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading schedules:', error);
    }
}

async function deleteSchedule(scheduleId) {
    try {
        await fetch(`${API_URL}/schedules/${scheduleId}`, {method: 'DELETE'});
        loadSchedules();
    } catch (error) {
        alert('Failed to delete');
    }
}

function openModal(modalId) {
    const modal = document.getElementById(modalId);
    modal.classList.add('active');
    if (modalId === 'scheduleModal') {
        loadSchedules();
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    modal.classList.remove('active');
}

function startLiveUpdates() {
    setInterval(async () => {
        for (let sensor of sensors) {
            try {
                await fetch(`${API_URL}/sensor/${sensor.id}/moisture`);
            } catch (error) {
                console.error('Error updating moisture:', error);
            }
        }
        await fetchSensors();
        await fetchStats();
    }, 30000);
}
