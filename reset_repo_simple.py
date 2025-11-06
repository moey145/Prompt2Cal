#!/usr/bin/env python3
"""
Simple repository reset script.
This will completely reset the git repository, removing all history.
Use this if other cleanup methods fail.
"""

import subprocess
import shutil
import sys
from pathlib import Path

def main():
    print("=" * 60)
    print("⚠️  REPOSITORY RESET SCRIPT")
    print("=" * 60)
    print("\nThis script will:")
    print("   ❌ Delete ALL git history")
    print("   ✅ Create a fresh repository")
    print("   ✅ Keep all your current files")
    print("   ⚠️  You'll need to force push to remote")
    
    response = input("\n⚠️  Are you sure? Type 'RESET' to confirm: ")
    
    if response != 'RESET':
        print("❌ Cancelled")
        return
    
    print("\n🔄 Starting reset...")
    
    repo_path = Path(__file__).parent
    
    # Step 1: Remove .git directory
    git_dir = repo_path / '.git'
    if git_dir.exists():
        print("📁 Removing .git directory...")
        try:
            shutil.rmtree(git_dir)
            print("✅ .git directory removed")
        except Exception as e:
            print(f"❌ Error removing .git: {e}")
            return
    else:
        print("ℹ️  No .git directory found")
    
    # Step 2: Initialize new repository
    print("\n🔄 Initializing new git repository...")
    try:
        subprocess.run(['git', 'init'], cwd=repo_path, check=True)
        print("✅ Repository initialized")
    except Exception as e:
        print(f"❌ Error initializing repo: {e}")
        return
    
    # Step 3: Add all files (respecting .gitignore)
    print("\n📁 Adding files...")
    try:
        subprocess.run(['git', 'add', '.'], cwd=repo_path, check=True)
        print("✅ Files added")
    except Exception as e:
        print(f"❌ Error adding files: {e}")
        return
    
    # Step 4: Create initial commit
    print("\n💾 Creating initial commit...")
    try:
        subprocess.run(
            ['git', 'commit', '-m', 'Initial commit - history reset for security'],
            cwd=repo_path,
            check=True
        )
        print("✅ Initial commit created")
    except Exception as e:
        print(f"❌ Error creating commit: {e}")
        return
    
    print("\n" + "=" * 60)
    print("✅ REPOSITORY RESET COMPLETE!")
    print("=" * 60)
    
    print("\n📋 Next steps:")
    print("   1. Check your remote: git remote -v")
    print("   2. If you need to update remote:")
    print("      git remote set-url origin <your-repo-url>")
    print("   3. Force push to remote (⚠️  DANGEROUS - coordinate with team!):")
    print("      git push --force --all")
    print("      git push --force --tags")
    print("\n⚠️  WARNING: Force pushing rewrites remote history!")
    print("   Make sure all team members are aware!")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

