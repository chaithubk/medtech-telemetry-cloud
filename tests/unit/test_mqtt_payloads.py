"""Unit tests for MQTT payload Pydantic model validation."""

import time
import pytest
from pydantic import ValidationError

from api.models.mqtt_payload import VitalPayload, PredictionPayload


class TestVitalPayload:
    def test_valid_vital(self):
        v = VitalPayload(
            timestamp=int(time.time() * 1000),
            hr=75,
            bp_sys=120,
            bp_dia=80,
            o2_sat=98,
            temperature=37.0,
            quality=95,
            source="device",
        )
        assert v.hr == 75
        assert v.source == "device"

    def test_minimal_vital_only_timestamp(self):
        v = VitalPayload(timestamp=1_000_000)
        assert v.hr is None
        assert v.source == "device"

    def test_missing_timestamp_raises(self):
        with pytest.raises(ValidationError):
            VitalPayload(hr=75)

    def test_negative_timestamp_raises(self):
        with pytest.raises(ValidationError):
            VitalPayload(timestamp=-1, hr=75)

    def test_zero_timestamp_is_valid(self):
        v = VitalPayload(timestamp=0)
        assert v.timestamp == 0

    def test_hr_too_high_raises(self):
        with pytest.raises(ValidationError):
            VitalPayload(timestamp=1000, hr=500)

    def test_hr_zero_raises(self):
        with pytest.raises(ValidationError):
            VitalPayload(timestamp=1000, hr=0)

    def test_o2_sat_above_100_raises(self):
        with pytest.raises(ValidationError):
            VitalPayload(timestamp=1000, o2_sat=110)

    def test_o2_sat_negative_raises(self):
        with pytest.raises(ValidationError):
            VitalPayload(timestamp=1000, o2_sat=-1)

    def test_invalid_type_for_hr_raises(self):
        with pytest.raises(ValidationError):
            VitalPayload(timestamp=1000, hr="not-a-number")

    def test_future_timestamp_is_valid(self):
        future_ts = int(time.time() * 1000) + 10_000_000
        v = VitalPayload(timestamp=future_ts)
        assert v.timestamp == future_ts

    def test_model_dump_roundtrip(self):
        v = VitalPayload(timestamp=5000, hr=80, o2_sat=97)
        d = v.model_dump()
        v2 = VitalPayload(**d)
        assert v2.hr == v.hr


class TestPredictionPayload:
    def test_valid_prediction(self):
        p = PredictionPayload(
            timestamp=1_000_000,
            risk_score=45.0,
            risk_level="LOW",
            confidence=0.75,
            model_latency_ms=87.5,
        )
        assert p.risk_score == 45.0
        assert p.risk_level == "LOW"

    def test_risk_level_normalized_to_uppercase(self):
        p = PredictionPayload(timestamp=1000, risk_score=20, risk_level="low", confidence=0.8)
        assert p.risk_level == "LOW"

    def test_medium_risk_level(self):
        p = PredictionPayload(timestamp=1000, risk_score=50, risk_level="MEDIUM", confidence=0.7)
        assert p.risk_level == "MEDIUM"

    def test_invalid_risk_level_raises(self):
        with pytest.raises(ValidationError):
            PredictionPayload(timestamp=1000, risk_score=20, risk_level="CRITICAL", confidence=0.8)

    def test_risk_score_above_100_raises(self):
        with pytest.raises(ValidationError):
            PredictionPayload(timestamp=1000, risk_score=150, risk_level="HIGH", confidence=0.8)

    def test_risk_score_negative_raises(self):
        with pytest.raises(ValidationError):
            PredictionPayload(timestamp=1000, risk_score=-5, risk_level="LOW", confidence=0.8)

    def test_confidence_above_1_raises(self):
        with pytest.raises(ValidationError):
            PredictionPayload(timestamp=1000, risk_score=50, risk_level="MEDIUM", confidence=1.5)

    def test_confidence_negative_raises(self):
        with pytest.raises(ValidationError):
            PredictionPayload(timestamp=1000, risk_score=50, risk_level="MEDIUM", confidence=-0.1)

    def test_negative_timestamp_raises(self):
        with pytest.raises(ValidationError):
            PredictionPayload(timestamp=-1, risk_score=20, risk_level="LOW", confidence=0.8)

    def test_missing_required_fields_raises(self):
        with pytest.raises(ValidationError):
            PredictionPayload(timestamp=1000)

    def test_optional_model_latency(self):
        p = PredictionPayload(timestamp=1000, risk_score=30, risk_level="LOW", confidence=0.9)
        assert p.model_latency_ms is None
