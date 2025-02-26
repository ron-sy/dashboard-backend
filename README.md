# Dashboard Backend

A Flask-based backend API for the dashboard application with Firebase Authentication integration.

## Features

- User authentication with Firebase
- Admin API for user management
- Company management
- Onboarding progress tracking
- Firestore database integration

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

5. Create a `.env` file with the following variables:
   ```
   PORT=5001
   FLASK_ENV=production
   FRONTEND_URL=http://localhost:3000
   FIREBASE_PROJECT_ID=your_firebase_project_id
   FIREBASE_USE_EMULATOR=false
   ```

6. Start the server:
   ```
   python src/app.py
   ```

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

## Technologies Used

- Python
- Flask
- Firebase Admin SDK
- Firestore 