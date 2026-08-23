#!/bin/bash

set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
API="${BASE_URL}/api/v1"

echo "========================================"
echo " Phase 5 Smoke Test"
echo "========================================"
echo "BASE_URL: ${BASE_URL}"
echo

# --------------------------------------------------
# 1. Backend health
# --------------------------------------------------

echo "1. Checking backend health..."

curl --fail --silent --show-error \
  "${BASE_URL}/health" | jq .

echo "✓ Backend health OK"
echo


# --------------------------------------------------
# 2. Backend readiness
# --------------------------------------------------

echo "2. Checking backend readiness..."

curl --fail --silent --show-error \
  "${BASE_URL}/health/ready" | jq .

echo "✓ Backend readiness OK"
echo


# --------------------------------------------------
# 3. Application LLM status
# --------------------------------------------------

echo "3. Checking application LLM status..."

LLM_STATUS=$(curl --fail --silent --show-error \
  "${API}/llm/status")

echo "$LLM_STATUS" | jq .

echo "✓ Application LLM status OK"
echo


# --------------------------------------------------
# 4. Direct Ollama check
# --------------------------------------------------

echo "4. Checking Ollama..."

curl --fail --silent --show-error \
  "http://127.0.0.1:11434/api/tags" | jq .

echo "✓ Ollama reachable"
echo


# --------------------------------------------------
# 5. Check Qwen3 8B
# --------------------------------------------------

echo "5. Checking qwen3:8b..."

if ! ollama list | grep -q "qwen3:8b"; then
    echo "ERROR: qwen3:8b is not installed."
    exit 1
fi

echo "✓ qwen3:8b installed"
echo


# --------------------------------------------------
# 6. Get jobs
# --------------------------------------------------

echo "6. Fetching jobs..."

JOBS=$(curl --fail --silent --show-error \
  "${API}/jobs")

echo "$JOBS" | jq .

echo "✓ Jobs endpoint OK"
echo


# --------------------------------------------------
# 7. Extract first Job ID
# --------------------------------------------------

JOB_ID=$(echo "$JOBS" | jq -r '
    if type == "array" then
        .[0].id
    elif .items then
        .items[0].id
    elif .data then
        .data[0].id
    else
        empty
    end
')

if [ -z "${JOB_ID}" ] || [ "${JOB_ID}" = "null" ]; then
    echo "ERROR: No job found."
    echo "Run the Phase 3 fixture ingestion first."
    exit 1
fi

echo "✓ Selected Job ID: ${JOB_ID}"
echo


# --------------------------------------------------
# 8. Get selected job
# --------------------------------------------------

echo "7. Fetching selected job..."

curl --fail --silent --show-error \
  "${API}/jobs/${JOB_ID}" | jq .

echo "✓ Job retrieved"
echo


# --------------------------------------------------
# 9. Run JD analysis
# --------------------------------------------------

echo "8. Running JD analysis..."
echo
echo "This calls the local Ollama / Qwen3 8B model."
echo

ANALYSIS_RESPONSE=$(curl --fail --silent --show-error \
  --request POST \
  "${API}/jobs/${JOB_ID}/analyze")

echo "$ANALYSIS_RESPONSE" | jq .

echo
echo "✓ JD analysis completed"
echo


# --------------------------------------------------
# 10. Retrieve persisted analysis
# --------------------------------------------------

echo "9. Retrieving persisted analysis..."

PERSISTED_ANALYSIS=$(curl --fail --silent --show-error \
  "${API}/jobs/${JOB_ID}/analysis")

echo "$PERSISTED_ANALYSIS" | jq .

echo
echo "✓ Persisted analysis retrieved"
echo


# --------------------------------------------------
# 11. List analyses
# --------------------------------------------------

echo "10. Listing analyses..."

ANALYSES=$(curl --fail --silent --show-error \
  "${API}/analyses")

echo "$ANALYSES" | jq .

echo
echo "✓ Analysis list endpoint OK"
echo


# --------------------------------------------------
# 12. Extract analysis ID
# --------------------------------------------------

ANALYSIS_ID=$(echo "$PERSISTED_ANALYSIS" | jq -r '
    .id // .analysis_id // .data.id // empty
')

if [ -n "${ANALYSIS_ID}" ] && [ "${ANALYSIS_ID}" != "null" ]; then

    echo "11. Fetching analysis ID: ${ANALYSIS_ID}"

    curl --fail --silent --show-error \
      "${API}/analyses/${ANALYSIS_ID}" | jq .

    echo
    echo "✓ Analysis-by-ID endpoint OK"

else

    echo "WARNING: Could not extract analysis ID."
    echo "Skipping GET /api/v1/analyses/{id}"
fi


# --------------------------------------------------
# 13. Check Ollama process
# --------------------------------------------------

echo
echo "12. Checking loaded Ollama models..."

ollama ps

echo


# --------------------------------------------------
# COMPLETE
# --------------------------------------------------

echo "========================================"
echo " Phase 5 Smoke Test PASSED"
echo "========================================"
echo
echo "Backend health     : OK"
echo "Backend readiness  : OK"
echo "Application LLM    : OK"
echo "Ollama             : OK"
echo "Qwen3 8B           : OK"
echo "Jobs API           : OK"
echo "JD Analysis        : OK"
echo "Analysis storage   : OK"
echo
echo "Job ID: ${JOB_ID}"
echo
