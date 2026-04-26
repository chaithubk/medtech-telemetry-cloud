# MedTech Telemetry Cloud

Open-source cloud backend for real-time medical IoT device data collection, storage, and visualization.

## Stage 1: Minimal Cloud Backend

### Architecture

```mermaid
flowchart TD
    A[Devices (QEMU/Docker/Hardware)] --> B[MQTT Cloud Backend]

    subgraph B [MQTT Cloud Backend]
        C[MQTT Broker (Mosquitto)]
        D[Time-Series Database (InfluxDB)]
        E[Relational Database (PostgreSQL)]
        F[REST API (Python/FastAPI)]
        G[Web Dashboard (HTML/JavaScript)]
    end
```

### Features

- ✅ **MQTT Ingestion** - Receive data from devices
- ✅ **Time-Series Storage** - InfluxDB for vitals
- ✅ **Relational Storage** - PostgreSQL for metadata
- ✅ **REST API** - Query vitals and predictions
- ✅ **Web Dashboard** - Real-time visualization
- ✅ **Docker Compose** - One-command startup
- ✅ **Zero Cost** - All open-source components
- ✅ **Self-Hosted** - Full control, no external services

### Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Message Broker | Mosquitto (MQTT) | Device data ingestion |
| Time-Series DB | InfluxDB | Store vital signs |
| Relational DB | PostgreSQL | Store alerts, metadata |
| API Server | Python/FastAPI | REST endpoints |
| Frontend | HTML/CSS/JavaScript | Web UI |
| Orchestration | Docker Compose | Local deployment |

### Quick Start

```bash
# Start all services
docker compose up

# Services available at:
# MQTT:       localhost:1883
# InfluxDB:   localhost:8086
# PostgreSQL: localhost:5432
# API:        http://localhost:8000
# Dashboard:  http://localhost:3000
# API Docs:   http://localhost:8000/docs
```

## MQTT Topics (from Device)

### Input Topics:

- medtech/vitals/latest - Current vital readings
- medtech/predictions/sepsis - Sepsis risk predictions

### Example Payload (Vitals):

```
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

### Example Payload (Predictions):

```
{
  "timestamp": 1712973600000,
  "risk_score": 45,
  "risk_level": "LOW",
  "confidence": 0.75,
  "model_latency_ms": 87.5
}
```

### REST API Endpoints

```
GET    /api/v1/health                     - Health check
GET    /api/v1/vitals                     - Get recent vitals
POST   /api/v1/vitals                     - Ingest vital
GET    /api/v1/predictions                - Get predictions
POST   /api/v1/predictions                - Ingest prediction
GET    /api/v1/analytics/summary          - Summary stats
GET    /api/v1/analytics/trends           - Historical trends
```

### Web Dashboard

```
Visit: http://localhost:3000

Shows:

Real-time vital readings
Latest predictions
Historical charts
Summary statistics
```

## Integration with Devices

### From QEMU:

```
# Inside QEMU, connect to cloud
mosquitto_pub -h <cloud-ip> -t medtech/vitals/latest -m '{"hr":92,...}'
```

### From Docker Compose (medtech-platform):

- Configure MQTT broker to point to cloud
- Vitals and predictions auto-sync

## Monitoring

```
# Check MQTT topics
docker exec telemetry-mqtt mosquitto_sub -t "medtech/#" -v

# View InfluxDB data
curl http://localhost:8086/query?q=SELECT%20*%20FROM%20vitals

# Check PostgreSQL
docker exec telemetry-postgres psql -U medtech -d telemetry -c "SELECT * FROM vitals LIMIT 5;"

# View logs
docker compose logs -f api
docker compose logs -f mqtt
```

## Verify Locally

```
cd ~/projects/medtech-telemetry-cloud

# Test docker-compose
docker compose config

# Start services (optional)
docker compose up -d

# Check status
docker compose ps

# View logs
docker compose logs

# Test API
curl http://localhost:8000/api/v1/health

# Test dashboard
curl http://localhost:3000

# Stop services
docker compose down
```