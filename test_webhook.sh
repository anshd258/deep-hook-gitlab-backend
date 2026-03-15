#!/bin/bash

BASE_URL="http://localhost:8000"
PROJECT_ID=80180134
MR_IID=1

echo "=== Test 1: MR Open Event ==="
curl -s -X POST "$BASE_URL/webhook/gitlab" \
     -H "Content-Type: application/json" \
     -H "X-Gitlab-Event: Merge Request Hook" \
     -d "{
  \"object_kind\": \"merge_request\",
  \"project\": {
    \"id\": $PROJECT_ID,
    \"name\": \"test-pros\",
    \"web_url\": \"https://gitlab.com/anshd2001/test-pros\"
  },
  \"object_attributes\": {
    \"iid\": $MR_IID,
    \"title\": \"Remove License section from README.md\",
    \"action\": \"open\",
    \"state\": \"opened\",
    \"source_branch\": \"feat\",
    \"target_branch\": \"main\"
  },
  \"user\": {
    \"name\": \"Anshdeep Singh\",
    \"username\": \"anshd2001\"
  }
}"
echo -e "\n"

sleep 2

echo "=== Test 2: MR Update Event ==="
curl -s -X POST "$BASE_URL/webhook/gitlab" \
     -H "Content-Type: application/json" \
     -H "X-Gitlab-Event: Merge Request Hook" \
     -d "{
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
    \"target_branch\": \"main\",
    \"oldrev\": \"abc123\"
  },
  \"user\": {
    \"name\": \"Anshdeep Singh\",
    \"username\": \"anshd2001\"
  }
}"
echo -e "\n"

echo "=== Done ==="
