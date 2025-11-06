#!/usr/bin/env python3
"""
Revoke all OAuth tokens programmatically.
This script will revoke all refresh tokens found in user_tokens directory.
"""

import os
import json
from pathlib import Path
from typing import List, Dict
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

def revoke_token(refresh_token: str) -> bool:
    """
    Revoke a single OAuth refresh token.
    
    Args:
        refresh_token: The refresh token to revoke
        
    Returns:
        True if successful, False otherwise
    """
    try:
        url = f"https://oauth2.googleapis.com/revoke?token={refresh_token}"
        req = Request(url, method='POST')
        
        with urlopen(req) as response:
            # Google returns 200 on success
            if response.getcode() == 200:
                return True
            else:
                print(f"      ⚠️  Unexpected status code: {response.getcode()}")
                return False
    except HTTPError as e:
        if e.code == 200:
            return True
        print(f"      ⚠️  HTTP Error {e.code}")
        return False
    except URLError as e:
        print(f"      ❌ Network Error: {e.reason}")
        return False
    except Exception as e:
        print(f"      ❌ Error: {e}")
        return False

def load_user_tokens() -> List[Dict]:
    """
    Load all user token files.
    
    Returns:
        List of token data dictionaries
    """
    user_tokens_dir = Path(__file__).parent / 'backend' / 'user_tokens'
    
    if not user_tokens_dir.exists():
        print("❌ user_tokens directory not found!")
        return []
    
    tokens = []
    for token_file in user_tokens_dir.glob('*.json'):
        try:
            with open(token_file, 'r') as f:
                data = json.load(f)
                data['_filename'] = token_file.name
                data['_user_id'] = token_file.stem.replace('user_', '')
                tokens.append(data)
        except Exception as e:
            print(f"⚠️  Error reading {token_file.name}: {e}")
    
    return tokens

def revoke_all_tokens():
    """
    Revoke all refresh tokens found in user_tokens directory.
    """
    print("=" * 60)
    print("🔒 OAuth Token Revocation Script")
    print("=" * 60)
    
    tokens = load_user_tokens()
    
    if not tokens:
        print("✅ No token files found. Nothing to revoke.")
        return
    
    print(f"\n📋 Found {len(tokens)} user token file(s)\n")
    
    revoked_count = 0
    failed_count = 0
    
    for token_data in tokens:
        filename = token_data.get('_filename', 'unknown')
        user_id = token_data.get('_user_id', 'unknown')
        refresh_token = token_data.get('refresh_token')
        
        print(f"📄 Processing: {filename}")
        print(f"   User ID: {user_id}")
        
        if not refresh_token:
            print("   ⚠️  No refresh token found in this file")
            failed_count += 1
            continue
        
        print(f"   Token: {refresh_token[:20]}...{refresh_token[-10:]}")
        print("   Revoking...", end=" ")
        
        if revoke_token(refresh_token):
            print("✅ SUCCESS")
            revoked_count += 1
        else:
            print("❌ FAILED")
            failed_count += 1
        
        print()
    
    print("=" * 60)
    print(f"📊 Summary:")
    print(f"   ✅ Successfully revoked: {revoked_count}")
    print(f"   ❌ Failed: {failed_count}")
    print(f"   📁 Total processed: {len(tokens)}")
    print("=" * 60)
    
    if revoked_count > 0:
        print("\n⚠️  IMPORTANT: After revoking tokens:")
        print("   1. Users will need to re-authenticate")
        print("   2. Consider deleting the token files (they're now invalid)")
        print("   3. Regenerate your OAuth client secret in Google Cloud Console")
    
    return revoked_count, failed_count

if __name__ == '__main__':
    try:
        revoke_all_tokens()
    except KeyboardInterrupt:
        print("\n\n⚠️  Cancelled by user")
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()

