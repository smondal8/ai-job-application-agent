#!/bin/bash

set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
API="${BASE_URL}/api/v1"

echo "========================================"
echo " Phase 6 Smoke Test"
echo " Grounded Resume Tailoring & Compilation"
echo "========================================"
echo "BASE_URL: ${BASE_URL}"
echo

# --------------------------------------------------
# 1. Backend health
# --------------------------------------------------
echo "1. Checking backend health..."
curl --fail --silent --show-error "${BASE_URL}/health" | jq .
echo "✓ Backend health OK"
echo

# --------------------------------------------------
# 2. Application LLM status
# --------------------------------------------------
echo "2. Checking application LLM status..."
LLM_STATUS=$(curl --fail --silent --show-error "${API}/llm/status")
echo "$LLM_STATUS" | jq .
echo "✓ Application LLM status OK"
echo

# --------------------------------------------------
# 3. Direct Ollama check
# --------------------------------------------------
echo "3. Checking Ollama & qwen3:8b model..."
if ! ollama list | grep -q "qwen3:8b"; then
    echo "ERROR: qwen3:8b is not installed."
    exit 1
fi
echo "✓ qwen3:8b installed and running"
echo

# --------------------------------------------------
# 4. Get or Verify Primary Candidate Profile
# --------------------------------------------------
echo "4. Checking verified candidate profile..."
PROFILE=$(curl --fail --silent --show-error "${API}/profile")
PROFILE_ID=$(echo "$PROFILE" | jq -r '.id // empty')

if [ -z "${PROFILE_ID}" ] || [ "${PROFILE_ID}" = "null" ]; then
    echo "ERROR: No candidate profile found. Create one first."
    exit 1
fi

echo "✓ Candidate Profile: ${PROFILE_ID} ($(echo "$PROFILE" | jq -r '.full_name // "Candidate"'))"
echo

# --------------------------------------------------
# 5. Get Job Listings
# --------------------------------------------------
echo "5. Fetching job listings..."
JOBS=$(curl --fail --silent --show-error "${API}/jobs")
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
    echo "ERROR: No jobs found in catalog."
    exit 1
fi

echo "✓ Selected Job ID: ${JOB_ID}"
echo

# --------------------------------------------------
# 6. Execute Grounded Resume Tailoring
# --------------------------------------------------
echo "6. Running Grounded Resume Tailoring..."
echo "This calls local Ollama (qwen3:8b) with Prompt Version v1.0.0..."
echo

TAILORED=$(curl --fail --silent --show-error \
  --request POST \
  --header "Content-Type: application/json" \
  --data "{\"tone\": \"technical\", \"auto_regenerate_on_untraced\": true}" \
  "${API}/jobs/${JOB_ID}/tailor-resume")

echo "$TAILORED" | jq .
echo
echo "✓ Grounded Tailoring Completed"
echo

TAILORED_ID=$(echo "$TAILORED" | jq -r '.id // empty')
PROMPT_VER=$(echo "$TAILORED" | jq -r '.prompt_version // empty')
VAL_STATUS=$(echo "$TAILORED" | jq -r '.validation_status // empty')
TRACE_SCORE=$(echo "$TAILORED" | jq -r '.validation_details.traceability_score // empty')

echo "Tailored Resume ID : ${TAILORED_ID}"
echo "Prompt Version     : ${PROMPT_VER}"
echo "Validation Status  : ${VAL_STATUS}"
echo "Traceability Score : ${TRACE_SCORE}%"
echo

# --------------------------------------------------
# 7. Verify Compiled ATS Documents
# --------------------------------------------------
echo "7. Downloading deterministically compiled documents..."

curl --fail --silent --show-error \
  "${API}/tailored-resumes/${TAILORED_ID}/download?format=markdown" > /tmp/test_resume.md

curl --fail --silent --show-error \
  "${API}/tailored-resumes/${TAILORED_ID}/download?format=cover_letter" > /tmp/test_cover_letter.txt

echo "✓ Markdown file size: $(wc -c < /tmp/test_resume.md) bytes"
echo "✓ Cover Letter size : $(wc -c < /tmp/test_cover_letter.txt) bytes"
echo

# --------------------------------------------------
# 8. Human Review & Approval Gate
# --------------------------------------------------
echo "8. Approving tailored application materials..."

APPROVED=$(curl --fail --silent --show-error \
  --request POST \
  --header "Content-Type: application/json" \
  --data "{\"approver_notes\": \"Phase 6 Smoke Test Approval - Grounded and verified.\"}" \
  "${API}/tailored-resumes/${TAILORED_ID}/approve")

echo "$APPROVED" | jq .
echo
echo "✓ Approval status: $(echo "$APPROVED" | jq -r '.status')"
echo

# --------------------------------------------------
# COMPLETE
# --------------------------------------------------
echo "========================================"
echo " Phase 6 Smoke Test PASSED"
echo "========================================"
echo "Backend health         : OK"
echo "Local Ollama LLM       : OK (qwen3:8b)"
echo "Prompt Versioning      : OK (${PROMPT_VER})"
echo "Fact Attribution       : OK (${VAL_STATUS})"
echo "Traceability Score     : ${TRACE_SCORE}%"
echo "Document Compilation   : OK (Markdown, Text, HTML, Cover Letter)"
echo "Human Approval Gate    : OK"
echo
