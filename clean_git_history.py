#!/usr/bin/env python3
"""
Clean git history to remove sensitive user_tokens files.
This script will attempt multiple methods to clean git history.
"""

import subprocess
import sys
from pathlib import Path

def run_command(cmd, description):
    """Run a git command and return success status."""
    print(f"\n{'='*60}")
    print(f"📋 {description}")
    print(f"{'='*60}")
    print(f"Command: {' '.join(cmd)}")
    print()
    
    try:
        result = subprocess.run(
            cmd,
            cwd=Path(__file__).parent,
            capture_output=True,
            text=True
        )
        
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return False

def check_git_repo():
    """Check if we're in a git repository."""
    return run_command(['git', 'rev-parse', '--git-dir'], "Checking git repository")

def check_clean_working_directory():
    """Check if working directory is clean."""
    result = subprocess.run(
        ['git', 'status', '--porcelain'],
        cwd=Path(__file__).parent,
        capture_output=True,
        text=True
    )
    
    if result.stdout.strip():
        print("⚠️  WARNING: You have uncommitted changes!")
        print("   Consider committing or stashing them first.")
        print("\n   Changes:")
        print(result.stdout)
        return False
    return True

def method1_git_filter_branch():
    """Method 1: Use git filter-branch (older method)."""
    print("\n" + "="*60)
    print("Method 1: Using git filter-branch")
    print("="*60)
    
    # Remove user_tokens directory from all commits
    cmd = [
        'git', 'filter-branch', '--force', '--index-filter',
        'git rm -rf --cached --ignore-unmatch backend/user_tokens/',
        '--prune-empty', '--tag-name-filter', 'cat', '--', '--all'
    ]
    
    return run_command(cmd, "Removing user_tokens from git history (filter-branch)")

def method2_bfg_install_check():
    """Check if BFG Repo-Cleaner is available."""
    try:
        result = subprocess.run(
            ['java', '-jar', 'bfg.jar', '--version'],
            capture_output=True,
            text=True
        )
        return True
    except:
        return False

def method2_bfg():
    """Method 2: Use BFG Repo-Cleaner (requires Java and BFG jar)."""
    print("\n" + "="*60)
    print("Method 2: Using BFG Repo-Cleaner")
    print("="*60)
    
    if not method2_bfg_install_check():
        print("⚠️  BFG Repo-Cleaner not found.")
        print("   Download from: https://rtyley.github.io/bfg-repo-cleaner/")
        print("   Place bfg.jar in the project root")
        return False
    
    # Remove user_tokens directory
    cmd = ['java', '-jar', 'bfg.jar', '--delete-folders', 'user_tokens']
    if not run_command(cmd, "Removing user_tokens with BFG"):
        return False
    
    # Clean up
    run_command(['git', 'reflog', 'expire', '--expire=now', '--all'], 
                "Expiring reflog")
    run_command(['git', 'gc', '--prune=now', '--aggressive'], 
                "Running garbage collection")
    
    return True

def method3_reset_repo():
    """Method 3: Reset repository (nuclear option - loses all history)."""
    print("\n" + "="*60)
    print("⚠️  METHOD 3: RESET REPOSITORY (DESTRUCTIVE)")
    print("="*60)
    print("\nThis will:")
    print("   ❌ Remove ALL git history")
    print("   ❌ Create a fresh initial commit")
    print("   ⚠️  You'll need to force push to remote")
    print("\nThis is the nuclear option - only use if other methods fail!")
    
    response = input("\nDo you want to proceed? (type 'YES' to confirm): ")
    
    if response != 'YES':
        print("❌ Cancelled")
        return False
    
    print("\n🔄 Resetting repository...")
    
    # Get current files (excluding .git)
    files_to_keep = []
    for item in Path(__file__).parent.rglob('*'):
        if item.is_file() and '.git' not in str(item):
            files_to_keep.append(item.relative_to(Path(__file__).parent))
    
    # Remove .git directory
    import shutil
    git_dir = Path(__file__).parent / '.git'
    if git_dir.exists():
        shutil.rmtree(git_dir)
        print("✅ Removed .git directory")
    
    # Initialize new repo
    run_command(['git', 'init'], "Initializing new git repository")
    run_command(['git', 'add', '.'], "Adding all files")
    run_command(['git', 'commit', '-m', 'Initial commit - history cleaned for security'], 
                "Creating initial commit")
    
    print("\n✅ Repository reset complete!")
    print("⚠️  You'll need to:")
    print("   1. Update your remote: git remote set-url origin <new-url> OR")
    print("   2. Force push: git push --force --all (DANGEROUS - coordinate with team!)")
    
    return True

def verify_cleanup():
    """Verify that user_tokens are removed from history."""
    print("\n" + "="*60)
    print("🔍 Verifying cleanup")
    print("="*60)
    
    # Check if files are still tracked
    result = subprocess.run(
        ['git', 'ls-files', 'backend/user_tokens/'],
        cwd=Path(__file__).parent,
        capture_output=True,
        text=True
    )
    
    if result.stdout.strip():
        print("❌ user_tokens files are still tracked!")
        print(result.stdout)
        return False
    else:
        print("✅ user_tokens files are not tracked")
    
    # Check git history
    result = subprocess.run(
        ['git', 'log', '--all', '--oneline', '--', 'backend/user_tokens/'],
        cwd=Path(__file__).parent,
        capture_output=True,
        text=True
    )
    
    if result.stdout.strip():
        print("⚠️  user_tokens still found in git history:")
        print(result.stdout[:200] + "..." if len(result.stdout) > 200 else result.stdout)
        return False
    else:
        print("✅ user_tokens not found in git history")
    
    return True

def main():
    print("=" * 60)
    print("🧹 Git History Cleanup Script")
    print("=" * 60)
    
    if not check_git_repo():
        print("❌ Not a git repository!")
        return
    
    if not check_clean_working_directory():
        response = input("\nContinue anyway? (y/N): ")
        if response.lower() != 'y':
            return
    
    print("\n📋 Available cleanup methods:")
    print("   1. git filter-branch (standard, may be slow)")
    print("   2. BFG Repo-Cleaner (fast, requires Java)")
    print("   3. Reset repository (nuclear - removes all history)")
    print("   4. Exit")
    
    choice = input("\nSelect method (1-4): ").strip()
    
    success = False
    
    if choice == '1':
        success = method1_git_filter_branch()
        if success:
            run_command(['git', 'reflog', 'expire', '--expire=now', '--all'], 
                       "Cleaning up")
            run_command(['git', 'gc', '--prune=now', '--aggressive'], 
                       "Garbage collection")
    
    elif choice == '2':
        success = method2_bfg()
    
    elif choice == '3':
        success = method3_reset_repo()
    
    elif choice == '4':
        print("Exiting...")
        return
    
    else:
        print("❌ Invalid choice")
        return
    
    if success:
        print("\n✅ Cleanup completed!")
        verify_cleanup()
        
        print("\n⚠️  IMPORTANT NEXT STEPS:")
        print("   1. Review the changes: git log --all")
        print("   2. If pushing to remote, you'll need to force push:")
        print("      git push --force --all")
        print("      ⚠️  WARNING: This rewrites remote history!")
        print("      ⚠️  Coordinate with your team first!")
    else:
        print("\n❌ Cleanup failed or was cancelled")
        print("   You may want to try method 3 (reset repository)")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Cancelled by user")
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()

