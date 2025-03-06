#!/bin/bash
set -e

# Configuration
PROJECT_ID=$(gcloud config get-value project)
SERVICE_ACCOUNT_NAME="dashboard-backend-sa"
SERVICE_ACCOUNT_DISPLAY_NAME="Dashboard Backend Service Account"
SERVICE_ACCOUNT_EMAIL="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Setting up service account for Cloud Run${NC}"

# Create service account
echo -e "${YELLOW}Creating service account: ${SERVICE_ACCOUNT_NAME}${NC}"
gcloud iam service-accounts create $SERVICE_ACCOUNT_NAME \
    --display-name="$SERVICE_ACCOUNT_DISPLAY_NAME"

# Grant necessary permissions
echo -e "${YELLOW}Granting necessary permissions to the service account${NC}"

# Secret Manager access
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
    --role="roles/secretmanager.secretAccessor"

# Cloud Run service agent
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
    --role="roles/run.serviceAgent"

# Firebase Admin role (if using Firebase)
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
    --role="roles/firebase.admin"

# VPC access
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
    --role="roles/compute.networkUser"

# Cloud Run admin (for initial deployment)
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
    --role="roles/run.admin"

echo -e "${GREEN}Service account setup complete: ${SERVICE_ACCOUNT_EMAIL}${NC}"
echo -e "${YELLOW}Update your deployment command to use this service account with:${NC}"
echo -e "--service-account=${SERVICE_ACCOUNT_EMAIL}" 