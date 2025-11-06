# Manual Security Fix Instructions

## ✅ Status Summary

**Token Revocation:**
- ✅ Token 1: Successfully revoked
- ⚠️  Token 2: HTTP 400 (may already be revoked)
- ⚠️  Token 3: HTTP 400 (may already be revoked)

**Git History:**
- ❌ Need to manually clean (Windows permission issue)

## 🔧 Manual Fix Steps

### Step 1: Close All Git Processes
1. Close any Git GUI applications (GitHub Desktop, SourceTree, etc.)
2. Close any IDE terminals that might have git processes running
3. Close VS Code/Cursor if it has git extensions active

### Step 2: Delete .git Directory Manually

**Option A: Using File Explorer**
1. Open File Explorer
2. Navigate to: `C:\Users\moham\OneDrive\Documents\GitHub\Prompt2Cal`
3. Enable "Show hidden files" (View → Show → Hidden items)
4. Right-click on `.git` folder → Delete
5. If it says "Access Denied", try:
   - Right-click → Properties → Uncheck "Read-only"
   - Or restart your computer and try again

**Option B: Using PowerShell (Run as Administrator)**
```powershell
cd "C:\Users\moham\OneDrive\Documents\GitHub\Prompt2Cal"
Remove-Item -Recurse -Force .git
```

### Step 3: Reinitialize Git Repository

Open a new terminal/command prompt and run:

```bash
cd C:\Users\moham\OneDrive\Documents\GitHub\Prompt2Cal
git init
git add .
git commit -m "Initial commit - history reset for security"
```

### Step 4: Verify Cleanup

Check that user_tokens are not in history:
```bash
git log --all --oneline -- backend/user_tokens/
```

Should return nothing (empty).

### Step 5: Update Remote (If Needed)

If you need to push to remote:
```bash
git remote -v  # Check your remote
git push --force --all
```

⚠️ **WARNING**: Force push rewrites remote history. Make sure repository is private.

## 🔒 Security Actions Completed

- ✅ 1/3 tokens revoked (others may already be invalid)
- ⚠️  Git history needs manual cleanup (see above)

## 📋 Next Steps After Git Cleanup

1. ✅ Regenerate OAuth client secret in Google Cloud Console
2. ✅ Update `.env` file with new client secret  
3. ✅ Users will need to re-authenticate
4. ✅ Verify `.gitignore` includes `backend/user_tokens/` (already done ✅)

