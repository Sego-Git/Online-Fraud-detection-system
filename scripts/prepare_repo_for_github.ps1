<#
Helper PowerShell script to set up Git LFS tracking and untrack large files from the index.
Review before running. This script does not rewrite history or force-push.
#>

param(
    [switch]$Run
)

Write-Host "This script will:"
Write-Host " - Ensure git-lfs is installed and initialized"
Write-Host " - Add common LFS tracking patterns"
Write-Host " - Remove data, models, and instance from the git index (keeps files locally)"
Write-Host "Review the script before running. Pass -Run to execute."

if (-not $Run) {
    exit 0
}

# Ensure git is available
git --version

# Initialize git-lfs (if installed)
git lfs install

# Track heavy file patterns (modify as needed)
git lfs track "models/**"
git lfs track "data/**"
git lfs track "*.h5"
git lfs track "*.pkl"

git add .gitattributes

Write-Host "Removing large dirs from the index (files remain on disk)."
git rm --cached -r data models instance webapp/instance || Write-Host "Some paths may not exist — that's OK."

Write-Host "Staging and committing the removal."
git add -A
git commit -m "Prepare repo: move data/models to LFS and untrack local large files" || Write-Host "Nothing to commit."

Write-Host "Done. Review changes and push to remote. If you need to rewrite history, follow GIT_CLEANUP.md instructions."
