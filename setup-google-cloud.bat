@echo off
REM Setup script for Google Cloud deployment (Windows)
REM Run this after creating your Google Cloud project

set PROJECT_ID=%1

if "%PROJECT_ID%"=="" (
    echo Usage: setup-google-cloud.bat ^<PROJECT_ID^>
    echo Example: setup-google-cloud.bat prompt2cal-backend
    exit /b 1
)

echo Setting up Google Cloud for project: %PROJECT_ID%

REM Set the project
gcloud config set project %PROJECT_ID%

REM Enable required APIs
echo Enabling required APIs...
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable cloudresourcemanager.googleapis.com

echo.
echo ✅ Google Cloud setup complete!
echo.
echo Next steps:
echo 1. Set environment variables in Cloud Run (after first deployment)
echo 2. Deploy: gcloud builds submit --config cloudbuild.yaml
echo 3. Update extension with the Cloud Run URL

