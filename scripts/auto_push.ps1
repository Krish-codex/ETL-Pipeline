# ==========================================
# LOCAL WINDOWS AUTOMATION SCRIPT (ETL & PUSH)
# ==========================================
# This script executes the ETL pipeline locally, stages updated database
# and reports, and pushes them back to your GitHub repository.
#
# How to run:
#   powershell -File scripts/auto_push.ps1
#
# Scheduling with Windows Task Scheduler:
#   1. Open Task Scheduler.
#   2. Create a Basic Task.
#   3. Trigger: Daily or Hourly.
#   4. Action: Start a Program.
#   5. Program/script: powershell.exe
#   6. Add arguments: -ExecutionPolicy Bypass -File "i:\Projects\ETL Piprline\scripts\auto_push.ps1"

# Force Unicode output
$OutputEncoding = [System.Text.Encoding]::UTF8

# Set workspace directory
$etlPath = "i:\Projects\ETL Piprline"
cd $etlPath

Write-Output "=========================================="
Write-Output "Starting Local Scheduled ETL Ingestion..."
Write-Output "=========================================="

# Run ETL pipeline
python main.py

if ($LASTEXITCODE -ne 0) {
    Write-Error "ETL Pipeline step failed!"
    exit 1
}

Write-Output "Staging database and analytical reports..."
git add data/ outputs/

# Check for modified or new files
$changes = git status --porcelain
if ($changes) {
    Write-Output "Changes detected. Preparing automatic commit..."
    $currentDate = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    git commit -m "Automated local ETL run - $currentDate"
    
    Write-Output "Pushing changes to remote repository (origin main)..."
    git push origin main
    Write-Output "Automatic push completed successfully! ✓"
} else {
    Write-Output "No changes in weather databases or reports detected. Skipping push."
}
