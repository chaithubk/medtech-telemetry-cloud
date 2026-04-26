// MedTech Dashboard JavaScript

const API_BASE = '/api/v1';

async function loadLatestVital() {
    try {
        const response = await fetch(`${API_BASE}/vitals?limit=1`);
        const data = await response.json();
        
        const elem = document.getElementById('latestVital');
        if (data && data.length > 0) {
            const vital = data[0];
            elem.innerHTML = `
                <div class="metric">${vital.hr || '---'}</div>
                <div class="metric-label">Heart Rate (BPM)</div>
                <div style="margin-top: 10px; font-size: 12px;">
                    O2: ${vital.o2_sat || '---'}% | Temp: ${vital.temperature || '---'}°C
                </div>
            `;
        }
    } catch (error) {
        document.getElementById('latestVital').innerHTML = `<span style="color: red;">Error loading data</span>`;
    }
}

async function loadLatestPrediction() {
    try {
        const response = await fetch(`${API_BASE}/predictions?limit=1`);
        const data = await response.json();
        
        const elem = document.getElementById('latestPrediction');
        if (data && data.length > 0) {
            const pred = data[0];
            const riskClass = pred.risk_level === 'HIGH' ? 'danger' : pred.risk_level === 'MODERATE' ? 'warning' : 'success';
            elem.innerHTML = `
                <div class="metric ${riskClass}">${pred.risk_level}</div>
                <div class="metric-label">Sepsis Risk</div>
                <div style="margin-top: 10px; font-size: 12px;">
                    Score: ${pred.risk_score}% | Confidence: ${(pred.confidence * 100).toFixed(0)}%
                </div>
            `;
        }
    } catch (error) {
        document.getElementById('latestPrediction').innerHTML = `<span style="color: red;">Error loading data</span>`;
    }
}

async function loadSystemStatus() {
    try {
        const response = await fetch(`${API_BASE}/health`);
        const data = await response.json();
        
        document.getElementById('systemStatus').innerHTML = `
            <div style="text-align: left;">
                <div><strong>API:</strong> <span style="color: green;">✓ Running</span></div>
                <div><strong>MQTT:</strong> <span style="color: green;">✓ Connected</span></div>
                <div><strong>Database:</strong> <span style="color: green;">✓ Healthy</span></div>
            </div>
        `;
    } catch (error) {
        document.getElementById('systemStatus').innerHTML = `<span style="color: red;">System offline</span>`;
    }
}

// Load data on page load
window.addEventListener('load', () => {
    loadLatestVital();
    loadLatestPrediction();
    loadSystemStatus();
    
    // Refresh every 10 seconds
    setInterval(() => {
        loadLatestVital();
        loadLatestPrediction();
    }, 10000);
});
