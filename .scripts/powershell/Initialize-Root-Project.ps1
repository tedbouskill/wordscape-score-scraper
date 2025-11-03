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

# Determine the directory of the current script
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Load the common functions which sets the $repoRoot, $repoFolder, and $repoName variables
# Load the common functions, check if the script is already sourced
if ((-not (Get-Variable -Name COMMON_INCLUDED -Scope Global -ErrorAction SilentlyContinue)) -or (-not $global:COMMON_INCLUDED)) {
    . "$scriptDir/Common.ps1"
    $global:COMMON_INCLUDED = $true
}

#Write-Output "Repo Root: $repoRoot, Repository: $repoFolder, Root Project Name: $repoName"
function Initialize-RootProjectWorkspace {
    param (
        [string]$repoRoot,
        [string]$repoFolder,
        [string]$repoName
    )

    # Fix: Use Join-Path for consistent path handling
    $workspacePath = Join-Path -Path $repoRoot -ChildPath "$repoFolder.code-workspace"
    $vscodePath = Join-Path -Path $repoRoot -ChildPath ".vscode"
    $launchPath = Join-Path -Path $vscodePath -ChildPath "launch.json"

    Write-Output "Creating root project workspace..."
    Copy-TemplateIfNotExists -templatePath (Join-Path -Path $repoRoot -ChildPath "templates/%REPO-NAME%.code-workspace") -targetPath $workspacePath

    Write-Output "Find and replace %REPO-NAME% with the actual repository name"
    Find-AndReplace -searchString "%REPO-NAME%" -replaceString $repoName -filePath $workspacePath

    if (-not (Test-Path $vscodePath)) {
        New-Item -ItemType Directory -Path $vscodePath | Out-Null
    }

    Write-Output "Copy the launch.json file to the .vscode folder"
    Copy-TemplateIfNotExists -templatePath (Join-Path -Path $repoRoot -ChildPath "templates/launch.json") -targetPath $launchPath

    Write-Output "Find and replace %REPO-NAME% with the actual repository name"
    Find-AndReplace -searchString "%REPO-NAME%" -replaceString $repoName -filePath $launchPath
}

Write-Output "Initializing root project workspace... in root project folder: $repoRoot"

Initialize-RootProjectWorkspace -repoRoot $repoRoot -repoName $repoFolder -repoNameUpper $repoName

Initialize-PythonEnvironment -projectPath $repoRoot -isRoot $true

#Initialize-PythonEnvironment -projectPath "$repoRoot/subproject" -isRoot $false
