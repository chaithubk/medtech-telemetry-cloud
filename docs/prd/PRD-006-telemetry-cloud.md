# PRD-006 — MedTech Telemetry Cloud (Population Health Backend)

| Field | Value |
|---|---|
| **Document ID** | PRD-006 |
| **Product** | MedTech Telemetry Cloud |
| **Repo** | `chaithubk/medtech-telemetry-cloud` |
| **Author** | MedTech R&D |
| **Status** | Active |
| **Last Updated** | 2026-05-13 |

> **Zero PHI Declaration:** All data ingested by this cloud backend originates from the MedTech Vitals Publisher using fully synthetic, Synthea-modeled profiles. No real patient data, PHI, or PII is collected, processed, stored, or transmitted. This service is an educational R&D prototype only. In a production system, this backend would require a formal HIPAA Business Associate Agreement (BAA), end-to-end encryption, and de-identification pipeline before any real patient data could be ingested.

---

## 1. Opportunity

Individual bedside sepsis detection addresses a single patient's risk at a single point in time. But a health delivery organization (HDO) managing dozens of ICU beds and hundreds of ward patients needs **population-level visibility**: Which unit has the highest sepsis incidence this quarter? Which patient cohort is most at risk? Where is the model underperforming — and why?

On-device TFLite inference answers "Is this patient deteriorating right now?" The cloud backend answers "What is the sepsis risk landscape across my hospital network, and how do I improve it?"

The **MedTech Telemetry Cloud** is the optional multi-hospital cloud backend that aggregates device telemetry and predictions from all deployed MedTech devices, stores time-series vitals in InfluxDB, persists structured prediction events in PostgreSQL, and exposes a FastAPI analytics API for clinical informatics dashboards and population health reporting.

It is architecturally decoupled from device inference: devices operate fully offline, and the cloud backend ingests asynchronously. A network partition never degrades bedside alarm performance.

### Clinical & Business Value

| Value | Description |
|---|---|
| **Population sepsis surveillance** | HDO-wide risk score trends, unit-level incidence dashboards |
| **Model performance monitoring** | Track precision/recall trends across real-world deployments to inform model retraining |
| **Retrospective audit** | Time-series vitals and prediction history for post-event clinical review |
| **Multi-site fleet visibility** | Which hospitals are running which model versions; alert on model version skew |
| **Research data pipeline** | Aggregate synthetic/anonymized data for prospective model improvement (with IRB governance in production) |

---

## 2. Target Audience

### Primary Users

| Persona | Need |
|---|---|
| **Clinical Informatics Analyst** | A REST API and dashboard to query sepsis event frequency, risk score distributions, and model performance by unit and time period |
| **Population Health Manager** | Hospital-wide and network-wide sepsis incidence trend reports |
| **ML Operations Engineer** | Model version deployment tracking, performance metric aggregation, and trigger criteria for model retraining pipeline |
| **Hospital IT / Security** | A HIPAA-compliant (in production) cloud ingestion endpoint with audit logging and role-based access control |

### Secondary Users

| Persona | Need |
|---|---|
| **Clinical Researcher** | Time-series vitals and prediction data for retrospective sepsis onset characterization (synthetic data in prototype) |
| **Regulatory Affairs** | Audit trail of prediction events with timestamps, model version, and device ID for post-market surveillance |

---

## 3. Product Vision

> Provide a scalable, multi-hospital cloud backend that aggregates MedTech device telemetry and sepsis predictions into population health analytics and model performance monitoring — fully decoupled from device inference so that cloud availability never affects bedside alarm delivery.

---

## 4. Success Metrics

| Metric | Target | Measurement Method |
|---|---|---|
| MQTT-to-cloud ingestion latency (p99) | **< 2 seconds** | End-to-end timestamp delta in integration test |
| Data ingest availability | **≥ 99.9% uptime** | API uptime monitoring |
| Query API response time (p95, population query) | **< 500 ms** | API load test |
| FHIR export completeness | **100% of prediction events** exportable as FHIR `RiskAssessment` resources | FHIR validation pipeline |
| Multi-hospital isolation | **Zero data cross-contamination** between hospital tenants | Integration test with multiple synthetic tenants |
| Audit log completeness | **100% of API calls** logged with user, timestamp, and resource | Audit log assertion test |

---

## 5. Scope

### In Scope

- FastAPI REST backend for:
  - Vitals ingestion endpoint
  - Prediction event ingestion endpoint
  - Population health query API
  - Model performance metrics API
- InfluxDB time-series storage for vitals
- PostgreSQL relational storage for prediction events, model versions, device registry
- MQTT bridge consumer (subscribes to device topics, POSTs to FastAPI)
- FHIR R4 `RiskAssessment` export endpoint
- Multi-tenant data isolation (by hospital/unit ID)
- Role-based access control (clinician, analyst, admin)
- Audit log for all data access events

### Out of Scope (prototype)

- Real PHI ingestion (synthetic data only)
- HIPAA BAA and formal security controls (required before production)
- EHR direct integration (Epic/Cerner HL7 v2.x ADT feeds)
- Model retraining pipeline (downstream ML Ops concern)
- Data retention policies and automated purge

---

## 6. Functional Requirements

### FR-001: Vitals Ingestion API

`POST /api/v1/vitals` MUST:
- Accept the telemetry contract vitals payload
- Validate against the versioned telemetry contract schema
- Write to InfluxDB with tags: `device_id`, `hospital_id`, `unit_id`
- Return HTTP 201 on success, HTTP 422 on schema validation failure

### FR-002: Prediction Event Ingestion API

`POST /api/v1/predictions` MUST:
- Accept the telemetry contract prediction payload
- Validate against the telemetry contract prediction schema
- Write to PostgreSQL `prediction_events` table with: `device_id`, `hospital_id`, `model_version`, `risk_level`, `risk_score`, `confidence`, `model_latency_ms`, `timestamp`
- Return HTTP 201 on success

### FR-003: Population Health Query API

`GET /api/v1/analytics/sepsis-summary` MUST return:
- `total_predictions` count in time window
- `high_critical_rate` (% of predictions with `risk_level` in `high|critical`)
- `by_unit` breakdown
- `by_model_version` breakdown
- Optional filters: `hospital_id`, `unit_id`, `from_dt`, `to_dt`

### FR-004: FHIR R4 Export

`GET /api/v1/fhir/RiskAssessment/{prediction_id}` MUST return a FHIR R4-compliant `RiskAssessment` resource with:
- `subject` (synthetic patient reference)
- `occurrenceDateTime` mapped from `timestamp`
- `prediction[0].outcome` from `risk_level`
- `prediction[0].probabilityDecimal` from `risk_score`
- `note` referencing model version

### FR-005: Audit Logging

Every API call MUST be logged with: `user_id`, `endpoint`, `method`, `timestamp`, `response_status`, `client_ip`. Audit logs MUST be append-only and tamper-evident.

---

## 7. Non-Functional Requirements

| ID | Requirement | Standard Reference |
|---|---|---|
| NFR-001 | MQTT-to-cloud ingestion latency MUST NOT affect device alarm latency | Architectural decoupling requirement |
| NFR-002 | Multi-tenant isolation MUST be enforced at the database query level, not application layer | HIPAA §164.312 (access control) |
| NFR-003 | All API endpoints MUST require authentication (JWT or mTLS in production) | HIPAA §164.312; NIST SP 800-63 |
| NFR-004 | FHIR export MUST pass FHIR R4 validator | HL7 FHIR R4 specification |
| NFR-005 | InfluxDB retention policy MUST be configurable (default: 90 days) | Data governance; IEC 62304 §9 |
| NFR-006 | PostgreSQL schema changes MUST be managed via versioned migrations | IEC 62304 §8 (configuration management) |

---

## 8. Regulatory & Standards Alignment

| Standard | Relevance to This Product |
|---|---|
| **HL7 FHIR R4** | FHIR `RiskAssessment` export enables EHR integration via SMART on FHIR. FHIR `Observation` resources map vitals fields to LOINC codes (`hr` → 8867-4, `o2_sat` → 2708-6). Population query API is structurally aligned with FHIR `MeasureReport` for quality reporting. |
| **HL7 v2.x ORU^R01** | Inbound MQTT payloads are structurally equivalent to HL7 OBX observation segments, enabling straightforward HL7 v2.x bridge adapters for legacy hospital systems. |
| **ISO 14971:2019** | Cloud-stored prediction events constitute post-market surveillance data. Audit logs and FHIR export constitute the post-market risk monitoring record. |
| **HIPAA §164.312 (Technical Safeguards)** | Multi-tenant isolation, audit logging, and authentication requirements address HIPAA technical safeguard requirements. These are architectural controls, not post-hoc compliance add-ons. (Note: formal HIPAA compliance requires BAA and formal security assessment before any real PHI is processed.) |
| **IEC 60601-1-8:2006+AMD1:2012** | The cloud backend MUST NOT introduce feedback latency that delays device alarm delivery. Architectural decoupling (MQTT bridge is async; device inference is local) is the risk control. |
| **FDA Post-Market Surveillance Guidance** | Aggregated prediction event data, model version tracking, and performance metrics support the FDA's recommended post-market performance monitoring for AI/ML-based SaMD. |

---

## 9. Risks & Mitigations (ISO 14971 Format)

| Risk | Likelihood | Severity | Risk Control |
|---|---|---|---|
| Cloud outage delays vitals ingestion | High | Low (device alarm unaffected by design) | MQTT bridge uses at-least-once delivery; device operates fully offline |
| Multi-tenant data leak (hospital A sees hospital B data) | Low | Critical (HIPAA violation in production) | Tenant isolation enforced at DB query level + integration test |
| FHIR export fails FHIR validator | Medium | Medium (EHR integration blocked) | FHIR validation in CI pipeline |
| Model performance regression undetected at fleet scale | Medium | High (widespread missed alarms) | Population-level precision/recall API + alerting on threshold breach |
| Audit log tampered post-incident | Low | High (regulatory and legal exposure) | Append-only log storage; planned cryptographic log chaining |

---

## 10. Dependencies

| Dependency | Repo | Note |
|---|---|---|
| Telemetry Contract | `medtech-telemetry-contract` | Schema used for inbound payload validation |
| Vitals Publisher | `medtech-vitals-publisher` | MQTT source (via bridge) |
| Edge Analytics | `medtech-edge-analytics` | Prediction event source (via bridge) |
| Platform | `medtech-platform` | Optional compose profile for local cloud backend testing |

---

## 11. Open Questions

1. Should the FastAPI backend expose a WebSocket endpoint for real-time population dashboard updates?
2. Should model retraining triggers be part of this repo's scope or a separate `medtech-ml-ops` repo?
3. Should FHIR `Device` and `Practitioner` resources be included in the export schema for full EHR context?
4. What is the synthetic data generation strategy for multi-hospital load testing (scale to 100+ simulated devices)?
