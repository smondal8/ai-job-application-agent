#!/bin/bash

set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
API="${BASE_URL}/api/v1"

echo "========================================"
echo " Phase 7 Smoke Test"
echo " Central Application Dashboard & Review"
echo "========================================"
echo "BASE_URL: ${BASE_URL}"
echo

# --------------------------------------------------
# 1. Backend health & readiness
# --------------------------------------------------
echo "1. Checking backend health & readiness..."
curl --fail --silent --show-error "${BASE_URL}/health" | jq .
curl --fail --silent --show-error "${BASE_URL}/health/ready" | jq .
echo "✓ Backend health and readiness OK"
echo

# --------------------------------------------------
# 2. Get Job Listings
# --------------------------------------------------
echo "2. Fetching jobs..."
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
    echo "ERROR: No jobs found in catalog. Seed fixtures first."
    exit 1
fi

echo "✓ Target Job ID: ${JOB_ID}"
echo

# --------------------------------------------------
# 3. Create Application Linked to Job
# --------------------------------------------------
echo "3. Creating new application linked to job #${JOB_ID}..."
APP_CREATE=$(curl --fail --silent --show-error \
  --request POST \
  --header "Content-Type: application/json" \
  --data "{\"job_id\": ${JOB_ID}, \"portal_type\": \"greenhouse\", \"submission_notes\": \"Phase 7 smoke test application entry.\"}" \
  "${API}/applications")

echo "$APP_CREATE" | jq .
echo

APP_ID=$(echo "$APP_CREATE" | jq -r '.id')
TAILORED_ID=$(echo "$APP_CREATE" | jq -r '.tailored_resume_id // "none"')
APP_STATUS=$(echo "$APP_CREATE" | jq -r '.status')

echo "Application ID      : ${APP_ID}"
echo "Tailored Resume ID  : ${TAILORED_ID}"
echo "Initial Status      : ${APP_STATUS}"
echo "✓ Application created successfully"
echo

# --------------------------------------------------
# 4. List Applications with Filter
# --------------------------------------------------
echo "4. Listing applications..."
APPS_LIST=$(curl --fail --silent --show-error "${API}/applications?page=1&page_size=10")
echo "$APPS_LIST" | jq .
echo "✓ Listed $(echo "$APPS_LIST" | jq -r '.total') applications"
echo

# --------------------------------------------------
# 5. Fetch Full Application Dossier
# --------------------------------------------------
echo "5. Retrieving complete Application Dossier for #${APP_ID}..."
DOSSIER=$(curl --fail --silent --show-error "${API}/applications/${APP_ID}/dossier")

echo "Dossier Aggregation Summary:"
echo "- Job Title     : $(echo "$DOSSIER" | jq -r '.job.title')"
echo "- Company       : $(echo "$DOSSIER" | jq -r '.job.company')"
echo "- Match Score   : $(echo "$DOSSIER" | jq -r '.analysis.fit_score // "N/A"')%"
echo "- Tailored Resume : $(echo "$DOSSIER" | jq -r '.tailored_resume.prompt_version // "None"') (ID: $(echo "$DOSSIER" | jq -r '.tailored_resume.id // "None"'))"
echo "- Candidate     : $(echo "$DOSSIER" | jq -r '.candidate.full_name // "None"')"
echo
echo "✓ Application Dossier retrieved successfully"
echo

# --------------------------------------------------
# 6. Update Application Screening Q&A
# --------------------------------------------------
echo "6. Updating screening answers payload..."
UPDATED=$(curl --fail --silent --show-error \
  --request PUT \
  --header "Content-Type: application/json" \
  --data "{\"answers_payload\": {\"sponsorship_required\": false, \"years_experience\": \"8+\", \"notice_period\": \"2_weeks\"}, \"reviewer_notes\": \"Candidate dossier verified.\"}" \
  "${API}/applications/${APP_ID}")

echo "$UPDATED" | jq .
echo "✓ Application answers updated"
echo

# --------------------------------------------------
# 7. Record Application Review Note
# --------------------------------------------------
echo "7. Recording review note in application review ledger..."
REVIEW=$(curl --fail --silent --show-error \
  --request POST \
  --header "Content-Type: application/json" \
  --data "{\"reviewer_notes\": \"Verified facts, ATS keywords, and screening answers.\", \"decision\": \"pending\"}" \
  "${API}/applications/${APP_ID}/reviews")

echo "$REVIEW" | jq .
echo "✓ Review note recorded"
echo

# --------------------------------------------------
# 8. Fetch Summary Statistics
# --------------------------------------------------
echo "8. Fetching application stats summary..."
STATS=$(curl --fail --silent --show-error "${API}/applications/stats/summary")
echo "$STATS" | jq .
echo

# --------------------------------------------------
# COMPLETE
# --------------------------------------------------
echo "========================================"
echo " Phase 7 Smoke Test PASSED"
echo "========================================"
echo "Backend health         : OK"
echo "Application Entity     : OK"
echo "Job & Resume Linking   : OK (Job #${JOB_ID}, Resume #${TAILORED_ID})"
echo "Dossier Aggregation    : OK"
echo "Screening Answers Q&A  : OK"
echo "Review Ledger Tracking : OK"
echo "Application Dashboard  : OK"
echo
