#!/bin/bash
set -e

# Get the URL of the deployed service
SERVICE_NAME="dashboard-backend"
REGION="us-central1"
PROJECT_ID=$(gcloud config get-value project)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Testing deployment for ${SERVICE_NAME} in project ${PROJECT_ID}${NC}"

# Get the service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --platform managed --region $REGION --format 'value(status.url)')
echo -e "Service URL: ${SERVICE_URL}"

# Test the health endpoint
echo -e "${YELLOW}Testing health endpoint...${NC}"
HEALTH_RESPONSE=$(curl -s ${SERVICE_URL}/health)
echo "Health response: ${HEALTH_RESPONSE}"

if [[ "${HEALTH_RESPONSE}" == *"ok"* ]]; then
    echo -e "${GREEN}Health check passed!${NC}"
else
    echo -e "${RED}Health check failed!${NC}"
    exit 1
fi

# Test API endpoint
echo -e "${YELLOW}Testing API endpoint...${NC}"
API_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" ${SERVICE_URL}/api)

if [[ "${API_RESPONSE}" -ge 200 && "${API_RESPONSE}" -lt 500 ]]; then
    echo -e "${GREEN}API test passed with status code: ${API_RESPONSE}${NC}"
else
    echo -e "${RED}API test failed with status code: ${API_RESPONSE}${NC}"
    exit 1
fi

echo -e "${GREEN}All tests passed! The service is running correctly.${NC}" 