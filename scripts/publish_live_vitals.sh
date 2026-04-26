#!/usr/bin/env bash
set -euo pipefail

# Publishes changing vitals to MQTT so the dashboard updates continuously.
#
# Usage examples:
#   bash scripts/publish_live_vitals.sh
#   HOST=localhost PORT=1883 INTERVAL=1 SOURCE=demo COUNT=30 bash scripts/publish_live_vitals.sh

HOST="${HOST:-localhost}"
PORT="${PORT:-1883}"
TOPIC="${TOPIC:-medtech/vitals/latest}"
INTERVAL="${INTERVAL:-1}"
SOURCE="${SOURCE:-live-sim}"
COUNT="${COUNT:-0}"

if ! command -v mosquitto_pub >/dev/null 2>&1; then
  echo "Error: mosquitto_pub not found. Install mosquitto-clients first." >&2
  exit 1
fi

echo "Publishing changing vitals to mqtt://${HOST}:${PORT}/${TOPIC}"
if [[ "$COUNT" == "0" ]]; then
  echo "Mode: continuous (Ctrl+C to stop)"
else
  echo "Mode: ${COUNT} messages"
fi

sent=0
trap 'echo; echo "Stopped after ${sent} messages."; exit 0' INT TERM

while true; do
  ts="$(date +%s%3N)"

  hr=$((65 + RANDOM % 46))
  bp_sys=$((105 + RANDOM % 36))
  bp_dia=$((65 + RANDOM % 21))
  o2_tenths=$((940 + RANDOM % 60))
  temp_tenths=$((360 + RANDOM % 25))
  quality=$((85 + RANDOM % 16))

  o2_sat="$(awk "BEGIN { printf \"%.1f\", ${o2_tenths}/10 }")"
  temperature="$(awk "BEGIN { printf \"%.1f\", ${temp_tenths}/10 }")"

  payload=$(printf '{"timestamp":%s,"hr":%s,"bp_sys":%s,"bp_dia":%s,"o2_sat":%s,"temperature":%s,"quality":%s,"source":"%s"}' \
    "$ts" "$hr" "$bp_sys" "$bp_dia" "$o2_sat" "$temperature" "$quality" "$SOURCE")

  mosquitto_pub -h "$HOST" -p "$PORT" -t "$TOPIC" -m "$payload"
  sent=$((sent + 1))

  echo "[$sent] hr=${hr} bp=${bp_sys}/${bp_dia} spo2=${o2_sat} temp=${temperature} q=${quality}"

  if [[ "$COUNT" != "0" && "$sent" -ge "$COUNT" ]]; then
    echo "Done. Sent ${sent} messages."
    exit 0
  fi

  sleep "$INTERVAL"
done
