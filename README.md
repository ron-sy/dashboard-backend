# Dashboard Backend

A Flask-based backend API for the dashboard application with Firebase Authentication integration.

## Features

- User authentication with Firebase
- Admin API for user management
- Company management
- Onboarding progress tracking
- Firestore database integration
- Email notifications via Mandrill

## Setup

1. Clone the repository
2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Set up Firebase:
   - Create a Firebase project
   - Set up Firebase Authentication
   - Set up Firestore Database
   - Download your Firebase Admin SDK service account key
   - Set up Application Default Credentials:
     ```
     gcloud auth application-default login
     gcloud auth application-default set-quota-project YOUR_PROJECT_ID
     ```

5. Create a `.env` file based on `.env.example`:
   ```
   cp .env.example .env
   ```
   
   Then edit the `.env` file with your actual credentials:
   ```
   PORT=5001
   FLASK_ENV=development
   FRONTEND_URL=http://localhost:3000
   FIREBASE_SERVICE_ACCOUNT=firebase-sa-key.json
   GOOGLE_APPLICATION_CREDENTIALS=firebase-sa-key.json
   MANDRILL_API_KEY=your-mandrill-api-key  # Keep this secure!
   MANDRILL_FROM_EMAIL=your-sender-email
   MANDRILL_FROM_NAME=Your Name or Company
   ```

   **IMPORTANT: Never commit your .env file to version control!**

6. Start the server:
   ```
   python -m src.app
   ```

## Security Best Practices

### Handling Sensitive Credentials

- **Local Development**: Use `.env` file (already in `.gitignore`)
- **Production Deployment**: Use Google Cloud Secret Manager
- **CI/CD Pipeline**: 
  - The GitHub Actions workflow is configured to use secrets from Google Cloud Secret Manager
  - The workflow automatically removes any environment variables and sets them using the `--set-secrets` flag

### Authentication Security
- All Firebase tokens are validated on every request
- Application uses service-to-service authentication for Google Cloud services

## API Endpoints

### Authentication
- Authentication is handled via Firebase Authentication
- All API requests require a valid Firebase ID token in the Authorization header

### Admin Endpoints
- `GET /api/admin/users` - Get all users
- `POST /api/admin/users` - Create a new user
- `PUT /api/admin/users/:id` - Update a user
- `GET /api/admin/companies/:id/users` - Get all users for a company

### Company Endpoints
- `GET /api/companies` - Get all companies
- `GET /api/companies/:id` - Get a specific company
- `POST /api/companies` - Create a new company
- `GET /api/companies/:id/onboarding` - Get onboarding steps for a company
- `PUT /api/companies/:id/onboarding/:step_id` - Update an onboarding step

## Deployment

### Google Cloud Run

The application is deployed to Google Cloud Run using GitHub Actions. The workflow:
1. Builds a Docker container
2. Pushes the container to Google Container Registry
3. Deploys the container to Cloud Run with proper secrets management

To deploy manually:
```
# Authenticate with Google Cloud
gcloud auth login

# Make sure you're in the project directory
cd dashboard-backend

# Deploy to Cloud Run 
gcloud run deploy dashboard-api \
  --source . \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --update-env-vars="FRONTEND_URL=https://app.syntheticteams.com" \
  --set-secrets="MANDRILL_API_KEY=mandrill-api-key:latest,/secrets/firebase-credentials=firebase-credentials:latest"
```

## Technologies Used

- Python
- Flask
- Firebase Admin SDK
- Firestore
- Mandrill (email service) 