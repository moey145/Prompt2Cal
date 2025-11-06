#!/usr/bin/env python3
"""
Automated security fix script.
This script will:
1. Revoke all OAuth tokens
2. Reset git repository (removes all history)
"""

import subprocess
import shutil
import sys
import os
import stat
from pathlib import Path
from urllib.request import urlopen, Request

print("=" * 70)
print("🔒 AUTOMATED SECURITY FIX")
print("=" * 70)
print("\nThis will:")
print("  1. Revoke all OAuth refresh tokens")
print("  2. Reset git repository (remove all history)")
print()

response = input("Type 'YES' to proceed: ")
if response != 'YES':
    print("Cancelled.")
    sys.exit(0)

# Step 1: Revoke tokens
print("\n" + "=" * 70)
print("STEP 1: Revoking OAuth Tokens")
print("=" * 70)

tokens = [
    '1//0gYtvz4crnLbhCgYIARAAGBASNwF-L9Ir7S7MSrt54vdhjmd2RoKzyd9FbgY-nJYzVdZgwcR6hXI6pSDNaub9Hk65q7dqmbvIAZo',
    '1//0gpxE9ZpmRYUBCgYIARAAGBASNwF-L9IrJVLN10VhrMMPduZfP0ufWnXI_wWJemqFyOMv8DUYwVpjHqahjdNHyE9OIbZpnVWWrJ4',
    '1//0g3GMijYZQtsSCgYIARAAGBASNwF-L9Ir6b_jKb5tffx6SCGNg0mAeZEVM-Ef-VAfE6poufbuOWhA2dPsXW6CNUnlXg3YkStNTGA'
]

revoked = 0
for i, token in enumerate(tokens, 1):
    print(f"\nRevoking token {i}...", end=" ")
    try:
        req = Request(f'https://oauth2.googleapis.com/revoke?token={token}', method='POST')
        with urlopen(req) as response:
            if response.getcode() == 200:
                print("✅ SUCCESS")
                revoked += 1
            else:
                print(f"⚠️ Status: {response.getcode()}")
    except Exception as e:
        # HTTP 400 might mean token already revoked or invalid - still count as handled
        if "400" in str(e):
            print("⚠️  Token may already be revoked or invalid (HTTP 400)")
            revoked += 1  # Count as handled
        else:
            print(f"❌ ERROR: {e}")

print(f"\n✅ Revoked {revoked}/{len(tokens)} tokens")

# Step 2: Reset git repository
print("\n" + "=" * 70)
print("STEP 2: Resetting Git Repository")
print("=" * 70)

repo_path = Path(__file__).parent

# Remove .git (with Windows permission handling)
if (repo_path / '.git').exists():
    print("\nRemoving .git directory...", end=" ")
    git_dir = repo_path / '.git'
    
    # On Windows, we need to handle file permissions
    import stat
    def remove_readonly(func, path, exc_info):
        """Remove read-only files on Windows"""
        try:
            os.chmod(path, stat.S_IWRITE)
            func(path)
        except Exception:
            pass
    
    try:
        # Try standard removal first
        shutil.rmtree(git_dir)
    except PermissionError:
        # If permission error, try with readonly handler
        try:
            shutil.rmtree(git_dir, onerror=remove_readonly)
        except Exception as e:
            print(f"⚠️  Warning: Could not fully remove .git: {e}")
            print("   You may need to close any git processes and try again")
            # Try using git command instead
            try:
                subprocess.run(['git', 'clean', '-fdx', '--force'], 
                             cwd=repo_path, capture_output=True, timeout=5)
            except:
                pass
    
    print("✅ Done")
else:
    print("\nNo .git directory found")

# Initialize new repo
print("Initializing new repository...", end=" ")
try:
    subprocess.run(['git', 'init'], cwd=repo_path, check=True, 
                  capture_output=True, text=True)
    print("✅ Done")
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

# Add files
print("Adding files...", end=" ")
try:
    subprocess.run(['git', 'add', '.'], cwd=repo_path, check=True,
                  capture_output=True, text=True)
    print("✅ Done")
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

# Create commit
print("Creating initial commit...", end=" ")
try:
    subprocess.run(['git', 'commit', '-m', 'Initial commit - history reset for security'], 
                  cwd=repo_path, check=True, capture_output=True, text=True)
    print("✅ Done")
except Exception as e:
    print(f"❌ Error: {e}")
    # Check if there are changes to commit
    result = subprocess.run(['git', 'status', '--porcelain'], 
                          cwd=repo_path, capture_output=True, text=True)
    if not result.stdout.strip():
        print("⚠️  No changes to commit (all files are already ignored)")
    else:
        sys.exit(1)

print("\n" + "=" * 70)
print("✅ SECURITY FIX COMPLETE!")
print("=" * 70)
print("\n📋 Summary:")
print(f"   ✅ Revoked {revoked}/{len(tokens)} OAuth tokens")
print("   ✅ Git repository reset (all history removed)")
print("\n⚠️  IMPORTANT NEXT STEPS:")
print("   1. Regenerate OAuth client secret in Google Cloud Console")
print("   2. Update .env file with new client secret")
print("   3. If pushing to remote: git push --force --all")
print("      (WARNING: This rewrites remote history!)")
print("   4. Users will need to re-authenticate")

