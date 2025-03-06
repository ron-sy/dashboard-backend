#!/bin/bash
set -e

# Configuration
PROJECT_NAME="dashboard-backend-$(date +%Y%m%d)"
REGION="us-central1"
SERVICE_NAME="dashboard-backend"
VPC_CONNECTOR_NAME="dashboard-connector"
VPC_NETWORK_NAME="dashboard-vpc"
VPC_SUBNET_NAME="dashboard-subnet"
SUBNET_RANGE="10.8.0.0/28"
CONNECTOR_RANGE="10.8.0.0/28"
SERVICE_ACCOUNT_NAME="dashboard-backend-sa"
SERVICE_ACCOUNT_DISPLAY_NAME="Dashboard Backend Service Account"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting GCP deployment for ${SERVICE_NAME}${NC}"

# Authenticate with GCP
echo -e "${YELLOW}Authenticating with GCP...${NC}"
gcloud auth login ron@syntheticteams.com

# Create a new project
echo -e "${YELLOW}Creating new GCP project: ${PROJECT_NAME}...${NC}"
gcloud projects create $PROJECT_NAME --name="Dashboard Backend"
gcloud config set project $PROJECT_NAME

# Enable required APIs
echo -e "${YELLOW}Enabling required APIs...${NC}"
gcloud services enable cloudbuild.googleapis.com \
    secretmanager.googleapis.com \
    run.googleapis.com \
    vpcaccess.googleapis.com \
    compute.googleapis.com \
    firebase.googleapis.com \
    iam.googleapis.com

# Create service account
echo -e "${YELLOW}Creating service account: ${SERVICE_ACCOUNT_NAME}${NC}"
SERVICE_ACCOUNT_EMAIL="${SERVICE_ACCOUNT_NAME}@${PROJECT_NAME}.iam.gserviceaccount.com"
gcloud iam service-accounts create $SERVICE_ACCOUNT_NAME \
    --display-name="$SERVICE_ACCOUNT_DISPLAY_NAME"

# Grant necessary permissions
echo -e "${YELLOW}Granting necessary permissions to the service account${NC}"

# Secret Manager access
gcloud projects add-iam-policy-binding $PROJECT_NAME \
    --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
    --role="roles/secretmanager.secretAccessor"

# Cloud Run service agent
gcloud projects add-iam-policy-binding $PROJECT_NAME \
    --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
    --role="roles/run.serviceAgent"

# Firebase Admin role (if using Firebase)
gcloud projects add-iam-policy-binding $PROJECT_NAME \
    --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
    --role="roles/firebase.admin"

# VPC access
gcloud projects add-iam-policy-binding $PROJECT_NAME \
    --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
    --role="roles/compute.networkUser"

# Create VPC network and subnet
echo -e "${YELLOW}Creating VPC network and subnet...${NC}"
gcloud compute networks create $VPC_NETWORK_NAME --subnet-mode=custom
gcloud compute networks subnets create $VPC_SUBNET_NAME \
    --network=$VPC_NETWORK_NAME \
    --region=$REGION \
    --range=$SUBNET_RANGE

# Create VPC connector
echo -e "${YELLOW}Creating VPC connector...${NC}"
gcloud compute networks vpc-access connectors create $VPC_CONNECTOR_NAME \
    --region=$REGION \
    --network=$VPC_NETWORK_NAME \
    --range=$CONNECTOR_RANGE

# Create secrets in Secret Manager
echo -e "${YELLOW}Creating secrets in Secret Manager...${NC}"

# Prompt for Mandrill API key
echo -e "${YELLOW}Enter your Mandrill API key:${NC}"
read -s MANDRILL_API_KEY
echo "mandrill_api_key: $MANDRILL_API_KEY" | gcloud secrets create mandrill-api-key \
    --data-file=- \
    --replication-policy=automatic

# Create Firebase service account
echo -e "${YELLOW}Creating Firebase service account file...${NC}"
echo -e "${YELLOW}Please paste the content of your Firebase service account JSON (end with Ctrl+D):${NC}"
cat > firebase-credentials.json

# Upload Firebase credentials to Secret Manager
cat firebase-credentials.json | gcloud secrets create firebase-credentials \
    --data-file=- \
    --replication-policy=automatic

# Remove local copy of credentials
rm firebase-credentials.json

# Build and push the Docker image to Google Container Registry
echo -e "${YELLOW}Building and pushing Docker image...${NC}"
gcloud builds submit --tag gcr.io/$PROJECT_NAME/$SERVICE_NAME

# Deploy to Cloud Run with VPC connector and secrets
echo -e "${YELLOW}Deploying to Cloud Run...${NC}"
gcloud run deploy $SERVICE_NAME \
    --image gcr.io/$PROJECT_NAME/$SERVICE_NAME \
    --platform managed \
    --region $REGION \
    --vpc-connector $VPC_CONNECTOR_NAME \
    --set-secrets="/secrets/mandrill-api-key=mandrill-api-key:latest,/secrets/firebase-credentials=firebase-credentials:latest" \
    --set-env-vars="FIREBASE_SERVICE_ACCOUNT=/secrets/firebase-credentials,MANDRILL_API_KEY_PATH=/secrets/mandrill-api-key,FRONTEND_URL=https://your-frontend-url-here.com,FLASK_ENV=production" \
    --service-account=$SERVICE_ACCOUNT_EMAIL \
    --allow-unauthenticated

# Get the deployed service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --platform managed --region $REGION --format 'value(status.url)')

echo -e "${GREEN}Deployment completed successfully!${NC}"
echo -e "${GREEN}Service URL: ${SERVICE_URL}${NC}"
echo -e "${YELLOW}Be sure to update your frontend application with this service URL.${NC}" 