#!/bin/bash

BASE_URL="http://localhost:8000"
REFUND_NOTARY_URL="https://refund.decide.fyi"
PROJECT_ID=80180134
MR_IID=4

# --- Test Refund Notary (decide.fyi) ---
echo "=== Testing Refund Notary (decide.fyi) ==="
ELIGIBILITY_RESP=$(curl -s -w "\n%{http_code}" -X POST "$REFUND_NOTARY_URL/api/v1/refund/eligibility" \
  -H "Content-Type: application/json" \
  -d '{}')
HTTP_CODE=$(echo "$ELIGIBILITY_RESP" | tail -n1)
BODY=$(echo "$ELIGIBILITY_RESP" | sed '$d')
if [[ "$HTTP_CODE" =~ ^2 ]]; then
  echo "  Eligibility: HTTP $HTTP_CODE — $BODY"
else
  echo "  Eligibility: HTTP $HTTP_CODE — $BODY"
fi
echo ""

# --- Webhook concurrency (uses config with decide.fyi MCP) ---
PAYLOAD="{
  \"object_kind\": \"merge_request\",
  \"project\": {
    \"id\": $PROJECT_ID,
    \"name\": \"test-pros\",
    \"web_url\": \"https://gitlab.com/anshd2001/test-pros\"
  },
  \"object_attributes\": {
    \"iid\": $MR_IID,
    \"title\": \"Remove License section from README.md\",
    \"action\": \"update\",
    \"state\": \"opened\",
    \"source_branch\": \"feat\",
    \"target_branch\": \"main\"
  },
  \"user\": {
    \"name\": \"Anshdeep Singh\",
    \"username\": \"anshd2001\"
  }
}"

echo "=== Webhook concurrency (review uses decide.fyi MCP from 80180134.deep.yml) ==="
echo "=== Sending Update 1 (will be cancelled) ==="
curl -s -X POST "$BASE_URL/webhook/gitlab" \
     -H "Content-Type: application/json" \
     -H "X-Gitlab-Event: Merge Request Hook" \
     -d "$PAYLOAD" &

sleep 1

echo "=== Sending Update 2 (should cancel Update 1) ==="
curl -s -X POST "$BASE_URL/webhook/gitlab" \
     -H "Content-Type: application/json" \
     -H "X-Gitlab-Event: Merge Request Hook" \
     -d "$PAYLOAD" &

wait
echo -e "\n=== Done. Refund Notary above; check server logs for cancellation and MCP (decide.fyi) usage. ==="
