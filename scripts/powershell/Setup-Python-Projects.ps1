# Description: This script sets up the Python environment for all projects in a multi-project repository.
#
# Notes:
# - This script sets up Python environments for multiple projects in a VS Code workspace.
# - It uses the Initialize-PythonEnvironment function from the Common.ps1 script to set up the Python environment for each project.
# - It finds the .code-workspace file at the root of the repository and extracts the project folders from it.
# - It iterates over each project folder and calls the Initialize-PythonEnvironment function to configure the Python environment.

# Exit immediately if a command exits with a non-zero status
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Load the common functions
. "$PSScriptRoot/Common.ps1"

# Main script execution

# Find the .code-workspace file
$workspaceFile = Get-ChildItem -Filter "*.code-workspace" | Select-Object -First 1

if (-Not $workspaceFile) {
    Write-Host "No *.code-workspace file found at the root of the repository."
    exit 1
}

# Set up the root project first
Setup-PythonEnvironment -projectPath "." -isRoot $true

# Get the list of project folders
$projectFolders = (Get-Content $workspaceFile.FullName | ConvertFrom-Json).folders.path

# Iterate over each project folder (excluding the root project) and set up the environment
foreach ($folder in $projectFolders) {
    if ($folder -ne ".") {
        Initialize-PythonEnvironment -projectPath $folder -isRoot $false
    }
}

Write-Host "All projects have been configured successfully."
