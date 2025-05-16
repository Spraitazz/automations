#!/bin/bash
set -e

# Ensure on working branch
git switch working

# Create a temporary branch (optional safety)
#git branch -f temp main
git switch -c main

# Force main to match working
#git checkout main
git reset --hard working

# Swap in the GitHub-specific .gitignore
cp githubignore .gitignore
git add .gitignore

git rm --cached -r . # tells Git to stop tracking all files.
git add . # re-adds only files not ignored by .gitignore

git commit --amend --no-edit #

# Push to GitHub
git push github main #####--force

# Switch back
#git checkout working
git switch working

# Remove main branch
git branch -d main
