@echo off
echo ============================================================
echo Revoking OAuth Tokens
echo ============================================================
echo.

curl -X POST "https://oauth2.googleapis.com/revoke?token=1//0gYtvz4crnLbhCgYIARAAGBASNwF-L9Ir7S7MSrt54vdhjmd2RoKzyd9FbgY-nJYzVdZgwcR6hXI6pSDNaub9Hk65q7dqmbvIAZo"
echo Token 1 revoked (user_ngrj32xjn.json)
echo.

curl -X POST "https://oauth2.googleapis.com/revoke?token=1//0gpxE9ZpmRYUBCgYIARAAGBASNwF-L9IrJVLN10VhrMMPduZfP0ufWnXI_wWJemqFyOMv8DUYwVpjHqahjdNHyE9OIbZpnVWWrJ4"
echo Token 2 revoked (user_wik180szl.json)
echo.

curl -X POST "https://oauth2.googleapis.com/revoke?token=1//0g3GMijYZQtsSCgYIARAAGBASNwF-L9Ir6b_jKb5tffx6SCGNg0mAeZEVM-Ef-VAfE6poufbuOWhA2dPsXW6CNUnlXg3YkStNTGA"
echo Token 3 revoked (user_zhy07a88j.json)
echo.

echo ============================================================
echo Done! All tokens have been revoked.
echo ============================================================
pause

