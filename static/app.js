const API_URL = 'http://localhost:5000/api';
let autoMode = false;
let crops = [];
let sensors = [];
let currentSensorForExport = null;
let loggedIn = false;

async function checkLogin() {
    const loginModal = document.getElementById('loginModal');
    if (!loggedIn) {
        loginModal.style.display = 'block';
    }
}

async function login() {
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    
    const response = await fetch(`${API_URL}/login`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({username, password})
    });
    
    const data = await response.json();
    if (data.success) {
        loggedIn = true;
        document.getElementById('loginModal').style.display = 'none';
        document.getElementById('userInfo').innerHTML = `👤 ${data.username} | <a href="#" onclick="logout()" style="color:white">Logout</a>`;
        init();
    } else {
        alert('Invalid credentials');
    }
}

async function logout() {
    await fetch(`${API_URL}/logout`, {method: 'POST'});
    loggedIn = false;
    location.reload();
}

async function fetchWeather() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(async (position) => {
            const response = await fetch(`${API_URL}/weather?lat=${position.coords.latitude}&lon=${position.coords.longitude}`);
            const data = await response.json();
            
            document.getElementById('weatherWidget').innerHTML = `
                <div class="weather-item">
                    <div class="value">🌡️ ${data.temperature}°C</div>
                    <div class="label">Temperature</div>
                </div>
                <div class="weather-item">
                    <div class="value">💧 ${data.precipitation}mm</div>
                    <div class="label">Precipitation</div>
                </div>
                <div class="weather-item">
                    <div class="value">💨 ${data.windspeed}km/h</div>
                    <div class="label">Wind Speed</div>
                </div>
            `;
        });
    }
}

async function fetchCrops() {
    const response = await fetch(`${API_URL}/crops`);
    crops = await response.json();
}

async function fetchSensors() {
    const response = await fetch(`${API_URL}/sensors`);
    sensors = await response.json();
    renderSensors();
}

async function updateMoisture(sensorId) {
    const response = await fetch(`${API_URL}/sensor/${sensorId}/moisture`);
    const data = await response.json();
    return data.moisture;
}

async function waterPlant(sensorId) {
    const response = await fetch(`${API_URL}/sensor/${sensorId}/water`, {
        method: 'POST'
    });
    const data = await response.json();
    
    if (data.success) {
        alert(`Watered! ${data.moisture_before}% → ${data.moisture_after}%`);
        await fetchSensors();
    }
}

async function toggleAutoMode() {
    autoMode = !autoMode;
    await fetch(`${API_URL}/auto-mode`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({enabled: autoMode})
    });
    
    const btn = document.getElementById('autoModeBtn');
    btn.textContent = `Auto Mode: ${autoMode ? 'ON' : 'OFF'}`;
    btn.classList.toggle('active', autoMode);
}

async function changeCrop(sensorId, cropId) {
    await fetch(`${API_URL}/sensor/${sensorId}/crop`, {
        method: 'PUT',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({crop_id: cropId})
    });
    await fetchSensors();
}

async function showHistory(sensorId) {
    currentSensorForExport = sensorId;
    const response = await fetch(`${API_URL}/history/${sensorId}`);
    const history = await response.json();
    
    const modal = document.getElementById('historyModal');
    const content = document.getElementById('historyContent');
    
    content.innerHTML = history.map(log => `
        <div class="history-item">
            <strong>${new Date(log.timestamp).toLocaleString()}</strong><br>
            Moisture: ${log.moisture_before.toFixed(1)}% → ${log.moisture_after.toFixed(1)}%<br>
            Amount: ${log.amount}ml
        </div>
    `).join('');
    
    modal.style.display = 'block';
}

async function exportData() {
    if (currentSensorForExport) {
        window.location.href = `${API_URL}/export/${currentSensorForExport}`;
    }
}

async function showSchedules() {
    const response = await fetch(`${API_URL}/schedules`);
    const schedules = await response.json();
    
    const modal = document.getElementById('scheduleModal');
    const list = document.getElementById('scheduleList');
    const select = document.getElementById('scheduleSensor');
    
    select.innerHTML = sensors.map(s => `<option value="${s.id}">Sensor ${s.id} - ${s.crop_name}</option>`).join('');
    
    list.innerHTML = schedules.map(sch => `
        <div class="schedule-item">
            <div>
                <strong>Sensor ${sch.sensor_id}</strong> at ${sch.time}<br>
                Days: ${sch.days}
            </div>
            <button onclick="deleteSchedule(${sch.id})">Delete</button>
        </div>
    `).join('');
    
    modal.style.display = 'block';
}

async function addSchedule() {
    const sensorId = document.getElementById('scheduleSensor').value;
    const time = document.getElementById('scheduleTime').value;
    const days = document.getElementById('scheduleDays').value;
    
    await fetch(`${API_URL}/schedules`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({sensor_id: sensorId, time, days})
    });
    
    showSchedules();
}

async function deleteSchedule(scheduleId) {
    await fetch(`${API_URL}/schedules/${scheduleId}`, {method: 'DELETE'});
    showSchedules();
}

async function showNotifications() {
    const response = await fetch(`${API_URL}/notifications`);
    const notifs = await response.json();
    
    const modal = document.getElementById('notifModal');
    const content = document.getElementById('notifContent');
    
    content.innerHTML = notifs.map(n => `
        <div class="notif-item">
            <strong>${new Date(n.timestamp).toLocaleString()}</strong><br>
            ${n.message}
        </div>
    `).join('');
    
    modal.style.display = 'block';
}

function getMoistureStatus(moisture, minMoisture, maxMoisture) {
    if (moisture >= minMoisture && moisture <= maxMoisture) return 'optimal';
    if (moisture < minMoisture) return moisture < minMoisture * 0.7 ? 'critical' : 'low';
    return 'optimal';
}

function renderSensors() {
    const grid = document.getElementById('sensorsGrid');
    
    grid.innerHTML = sensors.map(sensor => {
        const status = getMoistureStatus(sensor.current_moisture, sensor.min_moisture, sensor.max_moisture);
        const fillClass = sensor.current_moisture < sensor.min_moisture ? 'low' : 
                         sensor.current_moisture < sensor.max_moisture ? 'medium' : '';
        
        return `
            <div class="sensor-card">
                <div class="sensor-header">
                    <h3>Sensor ${sensor.id}</h3>
                    <select class="crop-select" onchange="changeCrop(${sensor.id}, this.value)">
                        ${crops.map(crop => `
                            <option value="${crop.id}" ${crop.id === sensor.crop_id ? 'selected' : ''}>
                                ${crop.name}
                            </option>
                        `).join('')}
                    </select>
                </div>
                
                <div class="moisture-display">
                    <div class="moisture-value">${sensor.current_moisture.toFixed(1)}%</div>
                    <div class="moisture-bar">
                        <div class="moisture-fill ${fillClass}" style="width: ${sensor.current_moisture}%">
                            ${sensor.current_moisture.toFixed(0)}%
                        </div>
                    </div>
                    <span class="status-badge status-${status}">${status.toUpperCase()}</span>
                </div>
                
                <div class="crop-info">
                    <p><strong>Crop:</strong> ${sensor.crop_name}</p>
                    <p><strong>Optimal Range:</strong> ${sensor.min_moisture}% - ${sensor.max_moisture}%</p>
                    <p><strong>Water Amount:</strong> ${sensor.water_amount}ml</p>
                </div>
                
                <div class="sensor-actions">
                    <button class="btn btn-water" onclick="waterPlant(${sensor.id})">💧 Water</button>
                    <button class="btn btn-history" onclick="showHistory(${sensor.id})">📊 History</button>
                    <button class="btn btn-export" onclick="exportData()">📥 Export</button>
                </div>
                
                <div class="last-reading">
                    Last: ${new Date(sensor.last_reading).toLocaleString()}
                </div>
            </div>
        `;
    }).join('');
}

async function init() {
    await fetchWeather();
    await fetchCrops();
    await fetchSensors();
    
    document.getElementById('autoModeBtn').addEventListener('click', toggleAutoMode);
    document.getElementById('refreshBtn').addEventListener('click', async () => {
        for (let sensor of sensors) {
            await updateMoisture(sensor.id);
        }
        await fetchSensors();
    });
    
    document.getElementById('scheduleBtn').addEventListener('click', showSchedules);
    document.getElementById('notifBtn').addEventListener('click', showNotifications);
    document.getElementById('exportBtn').addEventListener('click', exportData);
    document.getElementById('addScheduleBtn').addEventListener('click', addSchedule);
    document.getElementById('loginBtn').addEventListener('click', login);
    
    document.querySelectorAll('.close').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.getElementById(e.target.dataset.modal).style.display = 'none';
        });
    });
    
    setInterval(async () => {
        for (let sensor of sensors) {
            await updateMoisture(sensor.id);
        }
        await fetchSensors();
    }, 30000);
}

checkLogin();
