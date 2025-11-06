#!/usr/bin/env python3
"""Execute token revocation"""
from urllib.request import urlopen, Request

tokens = [
    '1//0gYtvz4crnLbhCgYIARAAGBASNwF-L9Ir7S7MSrt54vdhjmd2RoKzyd9FbgY-nJYzVdZgwcR6hXI6pSDNaub9Hk65q7dqmbvIAZo',
    '1//0gpxE9ZpmRYUBCgYIARAAGBASNwF-L9IrJVLN10VhrMMPduZfP0ufWnXI_wWJemqFyOMv8DUYwVpjHqahjdNHyE9OIbZpnVWWrJ4',
    '1//0g3GMijYZQtsSCgYIARAAGBASNwF-L9Ir6b_jKb5tffx6SCGNg0mAeZEVM-Ef-VAfE6poufbuOWhA2dPsXW6CNUnlXg3YkStNTGA'
]

print("=" * 60)
print("Revoking OAuth Tokens")
print("=" * 60)

for i, token in enumerate(tokens, 1):
    print(f"\nRevoking token {i}...", end=" ")
    try:
        req = Request(f'https://oauth2.googleapis.com/revoke?token={token}', method='POST')
        with urlopen(req) as response:
            if response.getcode() == 200:
                print("✅ SUCCESS")
            else:
                print(f"⚠️ Status: {response.getcode()}")
    except Exception as e:
        print(f"❌ ERROR: {e}")

print("\n" + "=" * 60)
print("Token revocation complete!")
print("=" * 60)

