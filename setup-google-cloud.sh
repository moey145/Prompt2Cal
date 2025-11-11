#!/bin/bash
# Setup script for Google Cloud deployment
# Run this after creating your Google Cloud project

PROJECT_ID=$1

if [ -z "$PROJECT_ID" ]; then
    echo "Usage: ./setup-google-cloud.sh <PROJECT_ID>"
    echo "Example: ./setup-google-cloud.sh prompt2cal-backend"
    exit 1
fi

echo "Setting up Google Cloud for project: $PROJECT_ID"

# Set the project
gcloud config set project $PROJECT_ID

# Enable required APIs
echo "Enabling required APIs..."
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable cloudresourcemanager.googleapis.com

# Set up Cloud Build service account permissions
echo "Setting up Cloud Build permissions..."
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
    --role="roles/run.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
    --role="roles/iam.serviceAccountUser"

echo "✅ Google Cloud setup complete!"
echo ""
echo "Next steps:"
echo "1. Set environment variables in Cloud Run (after first deployment)"
echo "2. Deploy: gcloud builds submit --config cloudbuild.yaml"
echo "3. Update extension with the Cloud Run URL"

