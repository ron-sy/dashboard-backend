# Deploying to Google Cloud Run

This guide outlines the steps to deploy the dashboard-backend application to Google Cloud Platform using Cloud Run.

## Prerequisites

1. A Google Cloud Platform account
2. Firebase project with Firestore enabled
3. Mandrill API key for email sending
4. Google Cloud SDK installed locally

## Deployment Architecture

The deployment has the following components:

1. **Cloud Run service** - Hosts the containerized Flask application
2. **VPC Network** - For secure communication with external services
3. **Secret Manager** - Securely stores API keys and credentials
4. **VPC Connector** - Allows Cloud Run to access resources in the VPC network

## Automated Deployment

We've provided a script that automates the deployment process:

```bash
chmod +x deploy-to-gcp.sh
./deploy-to-gcp.sh
```

The script will:
1. Create a new GCP project
2. Enable required APIs
3. Create a VPC network and subnet
4. Create a VPC connector
5. Store your secrets in Secret Manager
6. Build and push the Docker image
7. Deploy the application to Cloud Run

## Manual Deployment Steps

If you prefer to deploy manually, follow these steps:

### 1. Create a New GCP Project

```bash
gcloud projects create PROJECT_ID --name="Dashboard Backend"
gcloud config set project PROJECT_ID
```

### 2. Enable Required APIs

```bash
gcloud services enable cloudbuild.googleapis.com \
    secretmanager.googleapis.com \
    run.googleapis.com \
    vpcaccess.googleapis.com \
    compute.googleapis.com
```

### 3. Set Up VPC Network

```bash
gcloud compute networks create dashboard-vpc --subnet-mode=custom
gcloud compute networks subnets create dashboard-subnet \
    --network=dashboard-vpc \
    --region=us-central1 \
    --range=10.8.0.0/28
```

### 4. Create VPC Connector

```bash
gcloud compute networks vpc-access connectors create dashboard-connector \
    --region=us-central1 \
    --network=dashboard-vpc \
    --range=10.8.0.0/28
```

### 5. Store Secrets in Secret Manager

```bash
# For Mandrill API key
echo "mandrill_api_key: YOUR_MANDRILL_KEY" | gcloud secrets create mandrill-api-key \
    --data-file=- \
    --replication-policy=automatic

# For Firebase credentials
cat path/to/firebase-credentials.json | gcloud secrets create firebase-credentials \
    --data-file=- \
    --replication-policy=automatic
```

### 6. Build and Push Docker Image

```bash
gcloud builds submit --tag gcr.io/PROJECT_ID/dashboard-backend
```

### 7. Deploy to Cloud Run

```bash
gcloud run deploy dashboard-backend \
    --image gcr.io/PROJECT_ID/dashboard-backend \
    --platform managed \
    --region us-central1 \
    --vpc-connector dashboard-connector \
    --set-secrets="/secrets/mandrill-api-key=mandrill-api-key:latest,/secrets/firebase-credentials=firebase-credentials:latest" \
    --set-env-vars="FIREBASE_SERVICE_ACCOUNT=/secrets/firebase-credentials,MANDRILL_API_KEY_PATH=/secrets/mandrill-api-key,FRONTEND_URL=https://your-frontend-url.com,FLASK_ENV=production" \
    --allow-unauthenticated
```

## Verification

After deployment, verify that the service is running:

```bash
curl $(gcloud run services describe dashboard-backend --platform managed --region us-central1 --format 'value(status.url)')/health
```

You should receive a response like: `{"status": "ok"}`

## Troubleshooting

1. **Secret Access Issues**: Ensure that the service account has access to Secret Manager
2. **VPC Connector Problems**: Check that the connector is in the same region as the Cloud Run service
3. **Firebase Authentication**: Verify that the Firebase credentials are correctly formatted and have proper permissions

## Security Considerations

1. The deployment uses Secret Manager to securely store sensitive information
2. The VPC connector ensures that communication with external services is secure
3. The application runs as a non-root user within the container

## Updating the Deployment

To update the deployment after code changes:

```bash
gcloud builds submit --tag gcr.io/PROJECT_ID/dashboard-backend
gcloud run deploy dashboard-backend --image gcr.io/PROJECT_ID/dashboard-backend
``` 