@echo off
REM Deploy Prompt2Cal backend to Google Cloud Run
REM Make sure you have gcloud CLI installed and authenticated

echo Setting project to prompt2cal...
gcloud config set project prompt2cal

echo.
echo Checking if required APIs are enabled...
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com

echo.
echo Building and deploying to Cloud Run...
gcloud builds submit --config cloudbuild.yaml

echo.
echo ✅ Deployment complete!
echo.
echo Next steps:
echo 1. Go to Cloud Run in Google Cloud Console
echo 2. Click on your service: prompt2cal-backend
echo 3. Copy the URL (e.g., https://prompt2cal-backend-xxxxx.run.app)
echo 4. Add environment variables in Cloud Run:
echo    - OPENAI_API_KEY
echo    - GOOGLE_CLIENT_ID
echo    - GOOGLE_CLIENT_SECRET
echo    - GOOGLE_REDIRECT_URI (use your Cloud Run URL)
echo 5. Update OAuth redirect URI with your Cloud Run URL

