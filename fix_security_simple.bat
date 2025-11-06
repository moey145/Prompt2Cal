@echo off
echo ============================================================
echo Security Fix - Step 1: Revoking Tokens
echo ============================================================
echo.

curl -X POST "https://oauth2.googleapis.com/revoke?token=1//0gYtvz4crnLbhCgYIARAAGBASNwF-L9Ir7S7MSrt54vdhjmd2RoKzyd9FbgY-nJYzVdZgwcR6hXI6pSDNaub9Hk65q7dqmbvIAZo" >nul 2>&1
echo Token 1 revoked

curl -X POST "https://oauth2.googleapis.com/revoke?token=1//0gpxE9ZpmRYUBCgYIARAAGBASNwF-L9IrJVLN10VhrMMPduZfP0ufWnXI_wWJemqFyOMv8DUYwVpjHqahjdNHyE9OIbZpnVWWrJ4" >nul 2>&1
echo Token 2 revoked (may already be revoked)

curl -X POST "https://oauth2.googleapis.com/revoke?token=1//0g3GMijYZQtsSCgYIARAAGBASNwF-L9Ir6b_jKb5tffx6SCGNg0mAeZEVM-Ef-VAfE6poufbuOWhA2dPsXW6CNUnlXg3YkStNTGA" >nul 2>&1
echo Token 3 revoked (may already be revoked)

echo.
echo ============================================================
echo Step 2: Cleaning Git History
echo ============================================================
echo.

echo Using git filter-branch to remove user_tokens from history...
git filter-branch --force --index-filter "git rm -rf --cached --ignore-unmatch backend/user_tokens/" --prune-empty --tag-name-filter cat -- --all

echo.
echo Cleaning up git references...
git reflog expire --expire=now --all
git gc --prune=now --aggressive

echo.
echo ============================================================
echo Done!
echo ============================================================
echo.
echo Next steps:
echo 1. Regenerate OAuth client secret in Google Cloud Console
echo 2. Update .env file with new secret
echo 3. If pushing to remote: git push --force --all
echo.
pause

