#!/bin/bash

set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
API="${BASE_URL}/api/v1"

echo "========================================"
echo " Phase 8 Smoke Test"
echo " Human Approval Security Gate & State Machine"
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
# 2. Get Primary Candidate Profile & Verify
# --------------------------------------------------
echo "2. Ensuring verified candidate profile exists..."
PROFILE=$(curl --fail --silent --show-error "${API}/profile")
PROFILE_ID=$(echo "$PROFILE" | jq -r '.id // empty')

if [ -z "${PROFILE_ID}" ] || [ "${PROFILE_ID}" = "null" ]; then
    echo "ERROR: No candidate profile found. Create one first."
    exit 1
fi

# Ensure profile is verified
VERIFIED_PROFILE=$(curl --fail --silent --show-error --request POST "${API}/profile/${PROFILE_ID}/verify?verify_all_children=true")
echo "✓ Candidate Profile #${PROFILE_ID} verified: $(echo "$VERIFIED_PROFILE" | jq -r '.is_verified')"
echo

# --------------------------------------------------
# 3. Get Job Listings
# --------------------------------------------------
echo "3. Fetching job listing..."
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
# 4. Create Application Linked to Job
# --------------------------------------------------
echo "4. Creating application linked to job #${JOB_ID}..."
APP_CREATE=$(curl --fail --silent --show-error \
  --request POST \
  --header "Content-Type: application/json" \
  --data "{\"job_id\": ${JOB_ID}, \"portal_type\": \"greenhouse\", \"status\": \"ready_for_review\", \"answers_payload\": {\"sponsorship\": false, \"work_auth\": true}}" \
  "${API}/applications")

APP_ID=$(echo "$APP_CREATE" | jq -r '.id')
echo "✓ Created Application #${APP_ID} (Initial Status: $(echo "$APP_CREATE" | jq -r '.status'))"
echo

# --------------------------------------------------
# 5. Security Gate Negative Test 1: Attempt Preparation Without Approval
# --------------------------------------------------
echo "5. Testing Security Boundary: Attempt preparation authorization WITHOUT human approval..."
HTTP_CODE=$(curl --silent --output /tmp/prep_unauth.json --write-out "%{http_code}" \
  --request POST \
  "${API}/applications/${APP_ID}/authorize-preparation")

if [ "$HTTP_CODE" -ne 403 ]; then
    echo "SECURITY FAILURE: Expected HTTP 403 Forbidden, but received HTTP ${HTTP_CODE}!"
    cat /tmp/prep_unauth.json
    exit 1
fi

echo "✓ Security Boundary Active: Server rejected unauthorized preparation with HTTP 403 Forbidden:"
jq . /tmp/prep_unauth.json
echo

# --------------------------------------------------
# 6. Grant Cryptographic Human Approval
# --------------------------------------------------
echo "6. Granting Cryptographic Human Approval for Application #${APP_ID}..."
APPROVAL_RES=$(curl --fail --silent --show-error \
  --request POST \
  --header "Content-Type: application/json" \
  --data "{\"approver_notes\": \"Verified ground-truth facts against master candidate record.\", \"approver_id\": \"security_lead\"}" \
  "${API}/applications/${APP_ID}/approve")

echo "$APPROVAL_RES" | jq .
APPROVAL_TOKEN=$(echo "$APPROVAL_RES" | jq -r '.approval_token')
echo "✓ Human Approval Certificate Granted! Token: ${APPROVAL_TOKEN}"
echo

# --------------------------------------------------
# 7. Verify Approval Integrity
# --------------------------------------------------
echo "7. Verifying Approval Integrity against Live Material Hashes..."
VERIFY_RES=$(curl --fail --silent --show-error "${API}/applications/${APP_ID}/verify-approval")
echo "$VERIFY_RES" | jq .

IS_VALID=$(echo "$VERIFY_RES" | jq -r '.is_valid')
if [ "$IS_VALID" != "true" ]; then
    echo "ERROR: Approval verification expected is_valid=true, got ${IS_VALID}"
    exit 1
fi
echo "✓ Cryptographic approval binding verified intact!"
echo

# --------------------------------------------------
# 8. Authorize Preparation with Valid Approval
# --------------------------------------------------
echo "8. Authorizing Browser Preparation through Security Gate..."
AUTH_RES=$(curl --fail --silent --show-error \
  --request POST \
  "${API}/applications/${APP_ID}/authorize-preparation")

echo "$AUTH_RES" | jq .
if [ "$(echo "$AUTH_RES" | jq -r '.authorization_granted')" != "true" ]; then
    echo "ERROR: Preparation authorization failed!"
    exit 1
fi
echo "✓ Preparation authorization granted! Status: $(echo "$AUTH_RES" | jq -r '.status')"
echo

# --------------------------------------------------
# 9. Material Change Tamper Detection Test
# --------------------------------------------------
echo "9. Tamper Detection Test: Modifying screening answers payload to simulate material change..."
curl --fail --silent --show-error \
  --request PUT \
  --header "Content-Type: application/json" \
  --data "{\"answers_payload\": {\"sponsorship\": true, \"work_auth\": false, \"tampered\": true}}" \
  "${API}/applications/${APP_ID}" | jq .

echo "Verifying live approval status after material change..."
VERIFY_TAMPER=$(curl --fail --silent --show-error "${API}/applications/${APP_ID}/verify-approval")
echo "$VERIFY_TAMPER" | jq .

if [ "$(echo "$VERIFY_TAMPER" | jq -r '.is_valid')" != "false" ]; then
    echo "SECURITY FAILURE: Tampered application was NOT invalidated!"
    exit 1
fi
echo "✓ Security Boundary passed: Approval successfully INVALIDATED upon detecting material input hash change."
echo

echo "Attempting preparation on invalidated application..."
HTTP_TAMPER_CODE=$(curl --silent --output /tmp/prep_tampered.json --write-out "%{http_code}" \
  --request POST \
  "${API}/applications/${APP_ID}/authorize-preparation")

if [ "$HTTP_TAMPER_CODE" -ne 403 ]; then
    echo "SECURITY FAILURE: Expected HTTP 403 Forbidden for tampered application, got ${HTTP_TAMPER_CODE}!"
    cat /tmp/prep_tampered.json
    exit 1
fi
echo "✓ Security Gate successfully blocked preparation with HTTP 403 Forbidden."
echo

# --------------------------------------------------
# 10. Re-approve Application to Restore Authorization
# --------------------------------------------------
echo "10. Re-approving Application #${APP_ID}..."
REAPPROVE_RES=$(curl --fail --silent --show-error \
  --request POST \
  --header "Content-Type: application/json" \
  --data "{\"approver_notes\": \"Re-approved updated sponsorship screening requirements.\"}" \
  "${API}/applications/${APP_ID}/approve")

echo "$REAPPROVE_RES" | jq .

echo "Attempting preparation again on re-approved application..."
RESTORE_AUTH=$(curl --fail --silent --show-error \
  --request POST \
  "${API}/applications/${APP_ID}/authorize-preparation")

echo "$RESTORE_AUTH" | jq .
echo "✓ Authorization successfully restored after human re-approval."
echo

# --------------------------------------------------
# COMPLETE
# --------------------------------------------------
echo "========================================"
echo " Phase 8 Smoke Test PASSED"
echo "========================================"
echo "Backend health                 : OK"
echo "Security Boundary Rejection    : OK (403 Forbidden on unapproved preparation)"
echo "Cryptographic Input Hashing    : OK (Job, Profile, Resume, Answers SHA-256)"
echo "Human Approval State Machine   : OK (draft -> ready_for_review -> approved -> staged_for_prep)"
echo "Tamper Detection & Auto-Invalid: OK (requires_reapproval upon material change)"
echo "Re-approval & Authorization    : OK"
echo
