# MedTech Telemetry Cloud

Open-source cloud backend for real-time medical IoT device data collection, storage, and visualization.

## Architecture

```mermaid
flowchart TD
    A[Devices - QEMU/Docker/Hardware] -->|MQTT publish| B[MQTT Broker - Mosquitto]

    subgraph Cloud [MQTT Cloud Backend]
        B --> C[FastAPI Server]
        C --> D[PostgreSQL - vitals, predictions, alerts]
        C --> E[InfluxDB - time-series trends]
        C --> F[Redis - WebSocket session store]
        C -->|WebSocket broadcast| G[Web Dashboard - HTML/JS]
    end
```

## Features

- **MQTT Ingestion** — Receives vitals and predictions from devices via Mosquitto
- **Time-Series Storage** — InfluxDB for trend queries
- **Relational Storage** — PostgreSQL for vitals, predictions, and alerts
- **REST API** — FastAPI with full OpenAPI docs at `/docs`
- **Real-Time Streaming** — WebSocket endpoint pushes live updates to the dashboard
- **Alert Engine** — Automatic risk threshold alerts stored in PostgreSQL
- **Web Dashboard** — Live visualization served by Nginx
- **Docker Compose** — Single-command startup
- **Zero Cost** — All open-source components, fully self-hosted

## Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Message Broker | Mosquitto (MQTT) | Device data ingestion |
| Time-Series DB | InfluxDB 2.7 | Vital-sign trend queries |
| Relational DB | PostgreSQL 15 | Vitals, predictions, alerts |
| Cache / Session | Redis 7 | WebSocket session store |
| API Server | Python 3.10 / FastAPI | REST + WebSocket endpoints |
| Frontend | HTML / CSS / JavaScript | Web dashboard |
| Orchestration | Docker Compose | Local deployment |

## Quick Start

```bash
# Build and start all services
docker compose up --build

# Run in the background
docker compose up -d --build

# Services available at:
# MQTT (TCP):   localhost:1883
# MQTT (WS):    localhost:9001
# InfluxDB:     http://localhost:8086
# PostgreSQL:   localhost:5432
# Redis:        localhost:6379
# API:          http://localhost:8000
# API Docs:     http://localhost:8000/docs
# Dashboard:    http://localhost:3000
```

## MQTT Topics

| Topic | Direction | Description |
|-------|-----------|-------------|
| `medtech/vitals/latest` | Device → Cloud | Current vital readings |
| `medtech/predictions/sepsis` | Device → Cloud | Sepsis risk predictions |

### Example Payload — Vitals

```json
{
  "timestamp": 1712973600000,
  "hr": 92,
  "bp_sys": 135,
  "bp_dia": 85,
  "o2_sat": 98,
  "temperature": 37.2,
  "quality": 95,
  "source": "device-001"
}
```

### Example Payload — Predictions

```json
{
  "timestamp": 1712973600000,
  "risk_score": 45,
  "risk_level": "LOW",
  "confidence": 0.75,
  "model_latency_ms": 87.5
}
```

## REST API Endpoints

```
GET  /health                              - Service health check

GET  /api/v1/vitals                       - Recent vitals (?limit=10&hours=24)
GET  /api/v1/vitals/latest                - Most recent vital reading
GET  /api/v1/vitals/{id}                  - Vital by ID
POST /api/v1/vitals                       - Ingest vital (non-MQTT path)

GET  /api/v1/predictions                  - Recent predictions (?limit=10&hours=24)
GET  /api/v1/predictions/latest           - Most recent prediction
POST /api/v1/predictions                  - Ingest prediction (non-MQTT path)

GET  /api/v1/analytics/summary            - Aggregated stats (?hours=24)
GET  /api/v1/analytics/trends             - Time-series trend (?metric=hr&hours=24)
                                            metric: hr | bp_sys | bp_dia | o2_sat | temperature

GET  /api/v1/alerts                       - List alerts (?limit=20&acknowledged=false)
POST /api/v1/alerts/{id}/acknowledge      - Acknowledge an alert

WS   /api/v1/stream                       - Real-time WebSocket stream
```

Full interactive docs: **http://localhost:8000/docs**

## Web Dashboard

```
Visit: http://localhost:3000

Displays:
- Real-time vital readings (updates via WebSocket)
- Latest sepsis risk prediction
- Historical trend charts
- Summary statistics
```

### Live Changing Demo Data

Use the bundled simulator publisher to continuously send changing vitals.

```bash
# Continuous stream (Ctrl+C to stop)
bash scripts/publish_live_vitals.sh

# Example: send 30 messages, one every second
COUNT=30 INTERVAL=1 SOURCE=demo bash scripts/publish_live_vitals.sh
```

Optional environment variables:

- `HOST` (default: `localhost`)
- `PORT` (default: `1883`)
- `TOPIC` (default: `medtech/vitals/latest`)
- `INTERVAL` in seconds (default: `1`)
- `SOURCE` (default: `live-sim`)
- `COUNT` (default: `0`, meaning continuous)

## Integration with Devices

### Publish from QEMU / any host

```bash
# Publish a vital reading
mosquitto_pub -h <cloud-ip> -p 1883 \
  -t medtech/vitals/latest \
  -m '{"timestamp":1712973600000,"hr":92,"bp_sys":135,"bp_dia":85,"o2_sat":98,"temperature":37.2,"quality":95,"source":"device-001"}'

# Publish a prediction
mosquitto_pub -h <cloud-ip> -p 1883 \
  -t medtech/predictions/sepsis \
  -m '{"timestamp":1712973600000,"risk_score":45,"risk_level":"LOW","confidence":0.75,"model_latency_ms":87.5}'
```

### From another Docker Compose project

Set the MQTT broker host to the cloud IP and publish to the topics above; vitals and predictions sync automatically.

## Testing

Tests are organised into three levels. The test runner is `pytest`; async tests use `pytest-asyncio`.

### Unit Tests (no external services required)

```bash
# Run all unit tests
docker compose exec api pytest tests/unit -v

# Run a specific test module
docker compose exec api pytest tests/unit/test_api_endpoints.py -v
docker compose exec api pytest tests/unit/test_alert_engine.py -v
docker compose exec api pytest tests/unit/test_mqtt_payloads.py -v
docker compose exec api pytest tests/unit/test_mqtt_client.py -v
docker compose exec api pytest tests/unit/test_database.py -v

# Run with coverage
docker compose exec api pytest tests/unit --cov=api --cov-report=term-missing -v
```

### Integration Tests (require running services)

Start the full stack first (`docker compose up -d`), then:

```bash
# Run all integration tests
docker compose exec api pytest tests/integration -v

# Individual suites
docker compose exec api pytest tests/integration/test_mqtt_to_api.py -v
docker compose exec api pytest tests/integration/test_databases_sync.py -v
docker compose exec api pytest tests/integration/test_websocket_stream.py -v
```

Override service hostnames if running tests from outside the container:

```bash
TEST_MQTT_BROKER=localhost \
TEST_POSTGRES_HOST=localhost \
TEST_INFLUXDB_URL=http://localhost:8086 \
pytest tests/integration -v
```

### Acceptance / End-to-End Tests

```bash
docker compose exec api pytest tests/acceptance -v
```

### Run All Tests

```bash
docker compose exec api pytest -v
```

## Monitoring

```bash
# Tail API logs
docker compose logs -f api

# Tail all service logs
docker compose logs -f

# Watch live MQTT traffic
docker exec telemetry-mqtt mosquitto_sub -t "medtech/#" -v

# Query PostgreSQL
docker exec telemetry-postgres \
  psql -U medtech -d telemetry -c "SELECT * FROM vitals ORDER BY id DESC LIMIT 5;"

# Query InfluxDB health
curl http://localhost:8086/health

# Check Redis
docker exec telemetry-redis redis-cli ping

# Check all container status
docker compose ps
```

## Verify End-to-End

```bash
# 1. Start services
docker compose up -d --build

# 2. Wait for healthy status
docker compose ps

# 3. Health check
curl http://localhost:8000/health

# 4. Push a test vital via MQTT
mosquitto_pub -h localhost -p 1883 \
  -t medtech/vitals/latest \
  -m '{"timestamp":1712973600000,"hr":72,"bp_sys":118,"bp_dia":76,"o2_sat":99,"temperature":36.8,"quality":97,"source":"test"}'

# 5. Confirm it was stored
curl http://localhost:8000/api/v1/vitals/latest

# 6. Push a test prediction
mosquitto_pub -h localhost -p 1883 \
  -t medtech/predictions/sepsis \
  -m '{"timestamp":1712973600001,"risk_score":20,"risk_level":"LOW","confidence":0.90,"model_latency_ms":55}'

# 7. Confirm prediction and check analytics
curl http://localhost:8000/api/v1/predictions/latest
curl "http://localhost:8000/api/v1/analytics/summary?hours=1"

# 8. View the dashboard
curl http://localhost:3000

# 9. Stop services
docker compose down
```