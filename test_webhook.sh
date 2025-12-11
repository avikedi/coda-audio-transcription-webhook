#!/bin/bash

# Test script for webhook endpoints
# Usage: ./test_webhook.sh [base_url]

BASE_URL="${1:-http://localhost:8000}"

echo "=========================================="
echo "Testing Transcription Webhook Service"
echo "=========================================="
echo "Base URL: $BASE_URL"
echo ""

# Test 1: Health check
echo "Test 1: Health Check"
echo "--------------------"
curl -s "${BASE_URL}/api/health/" | python3 -m json.tool
echo -e "\n"

# Test 2: Webhook endpoint (with test data)
echo "Test 2: Webhook Endpoint"
echo "------------------------"
echo "Sending POST request with test data..."
curl -X POST "${BASE_URL}/api/webhook/transcribe/" \
  -H "Content-Type: application/json" \
  -d '{
    "row_id": "i-OQq0AURiBG",
    "audio_url": "https://drive.google.com/file/d/1Y3UeqL10Bu-ICbW_6ABv1N7z62xfNJMG/view?usp=sharing"
  }' | python3 -m json.tool

echo -e "\n"
echo "=========================================="
echo "Test Complete!"
echo "=========================================="
echo ""
echo "If webhook test returned a task_id, check status with:"
echo "curl ${BASE_URL}/api/status/TASK_ID/"
echo ""
