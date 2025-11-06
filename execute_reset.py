#!/usr/bin/env python3
"""Execute git repository reset"""
import subprocess
import shutil
from pathlib import Path

print("=" * 60)
print("Resetting Git Repository")
print("=" * 60)
print("\nThis will:")
print("  - Remove all git history")
print("  - Create a fresh repository")
print("  - Keep all current files")

response = input("\nType 'RESET' to confirm: ")
if response != 'RESET':
    print("Cancelled.")
    exit(1)

repo_path = Path(__file__).parent

# Remove .git
if (repo_path / '.git').exists():
    print("\nRemoving .git directory...")
    shutil.rmtree(repo_path / '.git')
    print("✅ Done")

# Initialize new repo
print("\nInitializing new repository...")
subprocess.run(['git', 'init'], cwd=repo_path, check=True)
print("✅ Done")

# Add files
print("\nAdding files...")
subprocess.run(['git', 'add', '.'], cwd=repo_path, check=True)
print("✅ Done")

# Create commit
print("\nCreating initial commit...")
subprocess.run(['git', 'commit', '-m', 'Initial commit - history reset for security'], 
              cwd=repo_path, check=True)
print("✅ Done")

print("\n" + "=" * 60)
print("Repository reset complete!")
print("=" * 60)
print("\nNext steps:")
print("  1. Check remote: git remote -v")
print("  2. Force push: git push --force --all")
print("     (WARNING: This rewrites remote history!)")

