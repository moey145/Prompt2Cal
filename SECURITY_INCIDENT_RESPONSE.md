# Security Incident Response - Exposed OAuth Tokens

## ⚠️ CRITICAL SECURITY ISSUE

User OAuth tokens containing sensitive credentials were committed to git history before being added to `.gitignore`.

## What Was Exposed

The following sensitive information is in your git history:

- **Access Tokens**: Can be used to access users' Google Calendars
- **Refresh Tokens**: Can be used to generate new access tokens indefinitely
- **Client Secret**: Allows unauthorized OAuth flows
- **Client ID**: Public identifier (less critical but still sensitive)

## Potential Dangers

### 1. **Calendar Access**

An attacker with these tokens can:

- Read all calendar events (meetings, appointments, personal info)
- Create malicious events
- Delete/modify existing events
- Access location data from events
- See attendee information

### 2. **Refresh Token Abuse**

Refresh tokens don't expire (unless revoked), so attackers can:

- Generate new access tokens indefinitely
- Maintain persistent access even after you revoke individual tokens

### 3. **Client Secret Compromise**

The exposed client secret allows:

- Unauthorized OAuth flows
- Creating new tokens for other users
- Impersonating your application

## Immediate Actions Required

### 1. **Revoke All Compromised Tokens** (URGENT - Do This First!)

For each affected user:

```bash
# Go to Google Account Security: https://myaccount.google.com/security
# Navigate to "Third-party apps with account access"
# Revoke access for your application
```

OR use the Google OAuth Revoke endpoint:

```
POST https://oauth2.googleapis.com/revoke?token=<refresh_token>
```

### 2. **Regenerate Client Secret**

1.  Go to [Google Cloud Console](https://console.cloud.google.com/)
2.  Navigate to APIs & Services > Credentials
3.  Find your OAuth 2.0 Client ID
4.  Click "Reset Secret" or create a new credential set
5.  **Update your `.env` file immediately**

### 3. **Clean Git History** (If Repository is Public)

⚠️ **WARNING**: This rewrites history. Only do this if:

- The repository is public, OR
- You coordinate with all collaborators

```bash
# Option 1: Use git-filter-repo (recommended)
pip install git-filter-repo
git filter-repo --path backend/user_tokens/ --invert-paths

# Option 2: Use BFG Repo-Cleaner
# Download from: https://rtyley.github.io/bfg-repo-cleaner/
java -jar bfg.jar --delete-folders user_tokens
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# After cleaning, force push (DANGEROUS - coordinate with team!)
git push --force --all
```

### 4. **Notify Affected Users**

If this is a production application, notify users that:

- Their tokens were exposed
- They should check their Google Calendar for suspicious activity
- They need to re-authenticate

### 5. **Security Audit**

- Check Google Cloud Console for unauthorized API usage
- Review calendar access logs
- Check for any suspicious events created

## Prevention Measures (Already Implemented)

✅ Added `backend/user_tokens/` to `.gitignore`
✅ Moved client credentials to environment variables
✅ Modified code to not store client secrets in token files

## Long-Term Security Improvements

1. **Use Environment Variables for All Secrets**

   - ✅ Already done for client credentials
   - Consider using a secrets manager (AWS Secrets Manager, Azure Key Vault, etc.) for production

2. **Token Encryption at Rest**

   - Encrypt token files before storing on disk
   - Use a key management service

3. **Token Rotation**

   - Implement automatic token refresh
   - Set shorter expiry times

4. **Access Logging**

   - Log all calendar API access
   - Monitor for suspicious patterns

5. **Pre-commit Hooks**
   - Add git hooks to prevent committing sensitive files
   - Use tools like `git-secrets` or `truffleHog`

## Status Checklist

- [ ] Revoked all exposed refresh tokens
- [ ] Regenerated Google OAuth client secret
- [ ] Updated `.env` with new credentials
- [ ] Cleaned git history (if public repo)
- [ ] Notified affected users (if applicable)
- [ ] Audited calendar access logs
- [ ] Verified `.gitignore` is working
- [ ] Tested new authentication flow

## Resources

- [Google OAuth Token Revocation](https://developers.google.com/identity/protocols/oauth2/web-server#tokenrevoke)
- [GitHub: Removing sensitive data](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository)
- [OWASP: OAuth 2.0 Security Best Practices](https://cheatsheetseries.owasp.org/cheatsheets/OAuth2_Cheat_Sheet.html)
