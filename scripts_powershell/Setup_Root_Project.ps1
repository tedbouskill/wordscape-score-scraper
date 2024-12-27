# Description: This script sets up the Python environment for the root project and its sub-projects in a VS Code workspace.
#
# Notes:
# - This script sets up Python environments for multiple projects in a VS Code workspace.
# - It uses the Initialize-PythonEnvironment function from the Common.ps1 script to set up the Python environment for each project.
# - It finds the .code-workspace file at the root of the repository and extracts the project folders from it.
# - It iterates over each project folder and calls the Initialize-PythonEnvironment function to configure the Python environment.

# Exit immediately if a command exits with a non-zero status
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

param (
    [string]$repoRoot,
    [string]$repoName,
    [string]$repoNameUpper
)

# Determine the directory of the current script
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Check if the script is already sourced
if (-Not $global:SCRIPT_INCLUDED) {
    . "$scriptDir/Common.ps1"
    $global:SCRIPT_INCLUDED = $true
}

function Create-RootProjectWorkspace {
    param (
        [string]$repoRoot,
        [string]$repoName,
        [string]$repoNameUpper
    )

    Write-Output "Creating root project workspace..."
    Copy-TemplateIfNotExists -templatePath "$repoRoot/templates/[REPO-NAME].code-workspace" -targetPath "$repoRoot/$repoName.code-workspace"

    Write-Output "Find and replace [REPO-NAME] with the actual repository name"
    Find-AndReplace -searchString "\[REPO-NAME\]" -replaceString $repoNameUpper -filePath "$repoRoot/$repoName.code-workspace"

    Write-Output "Copy the launch.json file to the .vscode folder"
    Copy-TemplateIfNotExists -templatePath "$repoRoot/templates/launch.json" -targetPath "$repoRoot/.vscode/launch.json"

    Write-Output "Find and replace [REPO-NAME] with the actual repository name"
    Find-AndReplace -searchString "\[REPO-NAME\]" -replaceString $repoNameUpper -filePath "$repoRoot/.vscode/launch.json"
}

Create-RootProjectWorkspace -repoRoot $repoRoot -repoName $repoName -repoNameUpper $repoNameUpper

Initialize-PythonEnvironment -projectPath $repoRoot -isRoot $true

Initialize-PythonEnvironment -projectPath "$repoRoot/google-bigquery" -isRoot $false

Initialize-PythonEnvironment -projectPath "$repoRoot/google-cloud-storage" -isRoot $false
