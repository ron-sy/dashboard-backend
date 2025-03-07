from firebase_admin import initialize_app, credentials, firestore
import os
import sys

try:
    cred = credentials.Certificate('firebase-sa-key.json')
    app = initialize_app(cred)
    db = firestore.client()

    print('Listing all users...')
    users = db.collection('users').stream()
    for user in users:
        data = user.to_dict()
        print(f"Document ID: {user.id}")
        print(f"Email: {data.get('email')}")
        print('---')

except Exception as e:
    print(f'Error: {str(e)}')
    sys.exit(1)