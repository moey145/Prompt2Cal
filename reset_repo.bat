@echo off
echo ============================================================
echo WARNING: This will reset your git repository!
echo All git history will be lost.
echo ============================================================
echo.
set /p confirm="Type RESET to confirm: "
if not "%confirm%"=="RESET" (
    echo Cancelled.
    exit /b
)

echo.
echo Removing .git directory...
if exist .git rmdir /s /q .git

echo Initializing new repository...
git init

echo Adding files...
git add .

echo Creating initial commit...
git commit -m "Initial commit - history reset for security"

echo.
echo ============================================================
echo Repository reset complete!
echo ============================================================
echo.
echo Next steps:
echo 1. Check your remote: git remote -v
echo 2. Force push to remote: git push --force --all
echo    WARNING: This rewrites remote history!
echo.
pause

