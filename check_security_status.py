#!/usr/bin/env python3
"""
Security Status Checker for Exposed OAuth Tokens
This script helps identify and manage the security incident.
"""

import os
import json
import subprocess
from pathlib import Path

def check_repo_visibility():
    """Check if the repository is public or private."""
    try:
        result = subprocess.run(
            ['git', 'remote', '-v'],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent
        )
        
        if 'github.com' in result.stdout:
            print("⚠️  Repository appears to be on GitHub")
            print("   Check repository visibility at: https://github.com/YOUR_USERNAME/Prompt2Cal/settings")
            print("   If PUBLIC: Tokens are exposed to anyone on the internet!")
            print("   If PRIVATE: Only collaborators can see them (still risky)")
        else:
            print("ℹ️  Repository remote not detected or not on GitHub")
            
    except Exception as e:
        print(f"❌ Could not check repository visibility: {e}")

def list_exposed_tokens():
    """List all user tokens that were exposed."""
    user_tokens_dir = Path(__file__).parent / 'backend' / 'user_tokens'
    
    if not user_tokens_dir.exists():
        print("✅ No user_tokens directory found (good!)")
        return
    
    print(f"\n⚠️  Found {len(list(user_tokens_dir.glob('*.json')))} user token files:")
    print("   These may have been committed to git history!")
    
    for token_file in user_tokens_dir.glob('*.json'):
        user_id = token_file.stem.replace('user_', '')
        try:
            with open(token_file, 'r') as f:
                data = json.load(f)
                has_client_secret = 'client_secret' in data
                has_refresh_token = 'refresh_token' in data
                
                print(f"\n   📄 {token_file.name}")
                print(f"      User ID: {user_id}")
                print(f"      Contains Client Secret: {'❌ YES (CRITICAL!)' if has_client_secret else '✅ No'}")
                print(f"      Contains Refresh Token: {'❌ YES (CRITICAL!)' if has_refresh_token else '✅ No'}")
                
                if has_client_secret:
                    print(f"      Client ID: {data.get('client_id', 'N/A')[:30]}...")
                    
        except Exception as e:
            print(f"   ❌ Error reading {token_file.name}: {e}")

def check_git_history():
    """Check if tokens are in git history."""
    print("\n🔍 Checking git history for exposed tokens...")
    
    try:
        # Check if user_tokens directory is tracked
        result = subprocess.run(
            ['git', 'ls-files', 'backend/user_tokens/'],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent
        )
        
        if result.stdout.strip():
            print("❌ CRITICAL: user_tokens files are currently tracked in git!")
            print("   Files:", result.stdout.strip().split('\n'))
        else:
            print("✅ user_tokens directory is not tracked (good)")
        
        # Check git history
        result = subprocess.run(
            ['git', 'log', '--all', '--oneline', '--', 'backend/user_tokens/'],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent
        )
        
        if result.stdout.strip():
            print(f"\n⚠️  Found {len(result.stdout.strip().split(chr(10)))} commits containing user_tokens")
            print("   These commits are in your git history!")
            print("\n   Recent commits:")
            for line in result.stdout.strip().split('\n')[:5]:
                print(f"      {line}")
        else:
            print("✅ No commits found with user_tokens (good)")
            
    except Exception as e:
        print(f"❌ Error checking git history: {e}")

def check_gitignore():
    """Verify .gitignore is properly configured."""
    print("\n🔍 Checking .gitignore configuration...")
    
    gitignore_path = Path(__file__).parent / '.gitignore'
    
    if not gitignore_path.exists():
        print("❌ No .gitignore file found!")
        return False
    
    with open(gitignore_path, 'r') as f:
        content = f.read()
    
    checks = {
        'backend/user_tokens/': 'backend/user_tokens/' in content,
        'backend/token.json': 'backend/token.json' in content,
        'backend/credentials.json': 'backend/credentials.json' in content,
        '.env': '.env' in content
    }
    
    all_good = True
    for pattern, found in checks.items():
        status = "✅" if found else "❌"
        print(f"   {status} {pattern}")
        if not found:
            all_good = False
    
    return all_good

def generate_revocation_guide():
    """Generate a guide for revoking tokens."""
    user_tokens_dir = Path(__file__).parent / 'backend' / 'user_tokens'
    
    if not user_tokens_dir.exists():
        return
    
    print("\n📋 Token Revocation Guide:")
    print("   For each user token, you need to revoke the refresh token.")
    print("   You can do this via:")
    print("   1. Google Account Settings: https://myaccount.google.com/security")
    print("      → Third-party apps with account access")
    print("   2. Programmatically using the revoke endpoint")
    print("\n   Refresh tokens to revoke:")
    
    for token_file in user_tokens_dir.glob('*.json'):
        try:
            with open(token_file, 'r') as f:
                data = json.load(f)
                refresh_token = data.get('refresh_token', 'N/A')
                if refresh_token != 'N/A':
                    print(f"\n   {token_file.name}:")
                    print(f"      curl -X POST 'https://oauth2.googleapis.com/revoke?token={refresh_token}'")
        except:
            pass

def main():
    print("=" * 60)
    print("🔒 SECURITY INCIDENT STATUS CHECK")
    print("=" * 60)
    
    check_repo_visibility()
    list_exposed_tokens()
    check_git_history()
    gitignore_ok = check_gitignore()
    
    if not gitignore_ok:
        print("\n⚠️  WARNING: .gitignore is not properly configured!")
    
    generate_revocation_guide()
    
    print("\n" + "=" * 60)
    print("📖 See SECURITY_INCIDENT_RESPONSE.md for detailed remediation steps")
    print("=" * 60)

if __name__ == '__main__':
    main()

