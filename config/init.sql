-- Vitals table
CREATE TABLE IF NOT EXISTS vitals (
    id SERIAL PRIMARY KEY,
    timestamp BIGINT NOT NULL UNIQUE,
    hr FLOAT,
    bp_sys FLOAT,
    bp_dia FLOAT,
    o2_sat FLOAT,
    temperature FLOAT,
    quality INT,
    source VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Predictions table
CREATE TABLE IF NOT EXISTS predictions (
    id SERIAL PRIMARY KEY,
    timestamp BIGINT NOT NULL UNIQUE,
    risk_score FLOAT NOT NULL,
    risk_level VARCHAR(50) NOT NULL,
    confidence FLOAT NOT NULL,
    model_latency_ms FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Alerts table
CREATE TABLE IF NOT EXISTS alerts (
    id SERIAL PRIMARY KEY,
    vital_id INT REFERENCES vitals(id),
    prediction_id INT REFERENCES predictions(id),
    alert_type VARCHAR(100) NOT NULL,
    message TEXT,
    severity VARCHAR(50),
    acknowledged BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    acknowledged_at TIMESTAMP
);

-- Sessions table (for future auth)
CREATE TABLE IF NOT EXISTS sessions (
    id SERIAL PRIMARY KEY,
    device_id VARCHAR(255) UNIQUE,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_vitals_timestamp ON vitals(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_vitals_created_at ON vitals(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_predictions_timestamp ON predictions(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_predictions_created_at ON predictions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_created_at ON alerts(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts(severity);

-- Views for aggregation
CREATE OR REPLACE VIEW v_vitals_latest AS
SELECT * FROM vitals
ORDER BY timestamp DESC
LIMIT 1;

CREATE OR REPLACE VIEW v_predictions_latest AS
SELECT * FROM predictions
ORDER BY timestamp DESC
LIMIT 1;

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO medtech;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO medtech;
