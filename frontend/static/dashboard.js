/* MedTech Dashboard – WebSocket + Chart.js real-time display */

const API_BASE = '/api/v1';
const WS_PROTO = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
const WS_URL = `${WS_PROTO}//${window.location.host}/api/v1/stream`;

let wsConnection = null;
let hrChart = null;
let o2Chart = null;
let reconnectTimer = null;

// ── Chart initialisation ──────────────────────────────────────────
function initCharts() {
    const baseOptions = {
        responsive: true,
        animation: { duration: 300 },
        scales: {
            x: { ticks: { color: '#6b7280', maxTicksLimit: 8 }, grid: { color: '#1f2937' } },
            y: { ticks: { color: '#6b7280' }, grid: { color: '#1f2937' } }
        },
        plugins: { legend: { display: false } }
    };

    hrChart = new Chart(document.getElementById('hrChart'), {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'HR (BPM)', data: [],
                borderColor: '#7eb8f7', backgroundColor: 'rgba(126,184,247,0.1)',
                tension: 0.3, pointRadius: 2
            }]
        },
        options: {
            ...baseOptions,
            scales: { ...baseOptions.scales, y: { ...baseOptions.scales.y, suggestedMin: 40, suggestedMax: 160 } }
        }
    });

    o2Chart = new Chart(document.getElementById('o2Chart'), {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'SpO2 (%)', data: [],
                borderColor: '#4ade80', backgroundColor: 'rgba(74,222,128,0.1)',
                tension: 0.3, pointRadius: 2
            }]
        },
        options: {
            ...baseOptions,
            scales: { ...baseOptions.scales, y: { ...baseOptions.scales.y, suggestedMin: 80, suggestedMax: 100 } }
        }
    });
}

function pushToChart(chart, timestamp, value) {
    if (value == null) return;
    chart.data.labels.push(new Date(timestamp).toLocaleTimeString());
    chart.data.datasets[0].data.push(value);
    if (chart.data.labels.length > 144) {
        chart.data.labels.shift();
        chart.data.datasets[0].data.shift();
    }
    chart.update('none');
}

// ── Data display ──────────────────────────────────────────────────
function displayVital(vital) {
    if (vital.hr != null)
        document.getElementById('hrValue').textContent = vital.hr.toFixed(0);
    if (vital.bp_sys != null && vital.bp_dia != null)
        document.getElementById('bpValue').textContent =
            `${vital.bp_sys.toFixed(0)}/${vital.bp_dia.toFixed(0)}`;
    if (vital.o2_sat != null)
        document.getElementById('o2Value').textContent = vital.o2_sat.toFixed(1);
    if (vital.temperature != null)
        document.getElementById('tempValue').textContent = vital.temperature.toFixed(1);
    if (vital.timestamp) {
        pushToChart(hrChart, vital.timestamp, vital.hr);
        pushToChart(o2Chart, vital.timestamp, vital.o2_sat);
    }
    document.getElementById('lastUpdate').textContent =
        `Updated: ${new Date().toLocaleTimeString()}`;
}

function displayPrediction(pred) {
    const level = pred.risk_level || 'UNKNOWN';
    const card = document.getElementById('riskCard');
    card.className = `card risk-card risk-${level}`;
    document.getElementById('riskLevel').textContent = level;
    document.getElementById('riskScore').textContent =
        `Score: ${pred.risk_score != null ? pred.risk_score.toFixed(1) : '---'}`;
    document.getElementById('riskConfidence').textContent =
        `Confidence: ${pred.confidence != null ? (pred.confidence * 100).toFixed(0) + '%' : '---'}`;
}

// ── WebSocket ─────────────────────────────────────────────────────
function connectWebSocket() {
    if (wsConnection) { wsConnection.close(); }
    try {
        wsConnection = new WebSocket(WS_URL);
    } catch (e) {
        scheduleReconnect();
        return;
    }

    wsConnection.onopen = () => {
        document.getElementById('wsStatus').className = 'status-indicator status-connected';
        document.getElementById('wsStatus').textContent = '🟢 WebSocket: Connected';
        document.getElementById('wsStatusText').textContent = 'Connected';
        document.getElementById('wsStatusText').style.color = '#4ade80';
        if (reconnectTimer) { clearTimeout(reconnectTimer); reconnectTimer = null; }
    };

    wsConnection.onmessage = (event) => {
        try {
            const msg = JSON.parse(event.data);
            if (msg.type === 'vital') displayVital(msg.data);
            else if (msg.type === 'prediction') displayPrediction(msg.data);
        } catch (e) { console.error('WS parse error:', e); }
    };

    wsConnection.onclose = () => {
        document.getElementById('wsStatus').className = 'status-indicator status-disconnected';
        document.getElementById('wsStatus').textContent = '⚪ WebSocket: Disconnected';
        document.getElementById('wsStatusText').textContent = 'Disconnected';
        document.getElementById('wsStatusText').style.color = '#f87171';
        scheduleReconnect();
    };

    wsConnection.onerror = () => { wsConnection.close(); };
}

function scheduleReconnect() {
    if (!reconnectTimer) {
        reconnectTimer = setTimeout(() => { reconnectTimer = null; connectWebSocket(); }, 5000);
    }
}

// ── REST API calls ────────────────────────────────────────────────
async function loadLatestData() {
    try {
        const [vRes, pRes] = await Promise.all([
            fetch(`${API_BASE}/vitals/latest`),
            fetch(`${API_BASE}/predictions/latest`)
        ]);
        if (vRes.ok) displayVital(await vRes.json());
        if (pRes.ok) displayPrediction(await pRes.json());
    } catch (e) { /* ignore – WebSocket is primary */ }
}

async function loadAlerts() {
    try {
        const res = await fetch(`${API_BASE}/alerts?acknowledged=false&limit=10`);
        if (!res.ok) return;
        const alerts = await res.json();
        document.getElementById('alertCount').textContent = alerts.length;
        const container = document.getElementById('alertsList');
        if (alerts.length === 0) { container.innerHTML = 'No active alerts'; return; }
        container.innerHTML = alerts.map(a => `
            <div class="alert-item severity-${a.severity}">
                <span>${a.message}</span>
                <button class="btn-ack" onclick="acknowledgeAlert(${a.id})">Ack</button>
            </div>
        `).join('');
    } catch (e) { /* ignore */ }
}

async function acknowledgeAlert(id) {
    await fetch(`${API_BASE}/alerts/${id}/acknowledge`, { method: 'POST' });
    loadAlerts();
}

async function loadSystemStatus() {
    try {
        const res = await fetch(`${API_BASE}/health`);
        const ok = res.ok;
        document.getElementById('apiStatus').textContent = ok ? '✓ Running' : '✗ Error';
        document.getElementById('apiStatus').style.color = ok ? '#4ade80' : '#f87171';
        document.getElementById('mqttStatus').textContent = ok ? '✓ Connected' : '✗ Unknown';
        document.getElementById('mqttStatus').style.color = ok ? '#4ade80' : '#f87171';
    } catch (e) {
        document.getElementById('apiStatus').textContent = '✗ Offline';
        document.getElementById('apiStatus').style.color = '#f87171';
    }
}

async function refreshCharts() {
    try {
        const [hrRes, o2Res] = await Promise.all([
            fetch(`${API_BASE}/analytics/trends?metric=hr&hours=24`),
            fetch(`${API_BASE}/analytics/trends?metric=o2_sat&hours=24`)
        ]);
        if (hrRes.ok) {
            const pts = await hrRes.json();
            hrChart.data.labels = pts.map(p => new Date(p.timestamp).toLocaleTimeString());
            hrChart.data.datasets[0].data = pts.map(p => p.value);
            hrChart.update();
        }
        if (o2Res.ok) {
            const pts = await o2Res.json();
            o2Chart.data.labels = pts.map(p => new Date(p.timestamp).toLocaleTimeString());
            o2Chart.data.datasets[0].data = pts.map(p => p.value);
            o2Chart.update();
        }
    } catch (e) { console.error('Chart refresh error:', e); }
}

// ── Bootstrap ─────────────────────────────────────────────────────
window.addEventListener('load', () => {
    initCharts();
    connectWebSocket();
    loadLatestData();
    loadAlerts();
    loadSystemStatus();
    refreshCharts();

    // Periodic REST fallback & alert polling
    setInterval(loadLatestData, 30_000);
    setInterval(loadAlerts, 15_000);
    setInterval(loadSystemStatus, 30_000);
    setInterval(refreshCharts, 300_000);  // Every 5 min
});
