<#
Untrack the `assets/` directory in a local git repository while keeping the files on disk.

Usage (PowerShell):
    cd path\to\repo
    .\scripts\untrack_assets.ps1

This script runs the following commands:
 - git rm --cached -r assets
 - git add .gitignore
 - git commit -m "Stop tracking assets/ (now in .gitignore)"

#>

if (-not (Test-Path -Path .git\HEAD)) {
    Write-Error "This folder does not look like a git repository. Run these commands from your repo root."
    exit 1
}

Write-Host "Removing assets/ from git index (files will remain on disk)..."
git rm --cached -r assets

Write-Host "Adding .gitignore and committing..."
git add .gitignore
git commit -m "Stop tracking assets/ (add to .gitignore)"

Write-Host "Done. assets/ is no longer tracked."
