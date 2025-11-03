[CmdletBinding()]
param (
    [Parameter()]
    [string]$projectToUpdate = "."
)

Write-Host "Script execution started." -ForegroundColor Green

# Exit immediately if a command exits with a non-zero status
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Determine the directory of the current script
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$global:workspaceFile = $null

# Load the common functions, check if the script is already sourced
if ((-not (Get-Variable -Name COMMON_INCLUDED -Scope Global -ErrorAction SilentlyContinue)) -or (-not $global:COMMON_INCLUDED) -or (-not $global:workspaceFile)) {
    Write-Host "Including Common.ps1" -ForegroundColor Green
    . "$scriptDir/Common.ps1"
    $global:COMMON_INCLUDED = $true
} else {
    Write-Host "Common.ps1 already included." -ForegroundColor Yellow
}

# Main script execution
if (-Not $global:workspaceFile) {
    Write-Host "No *.code-workspace file found at the root of the repository."
    exit 1
}

if ($projectToUpdate -ne ".") {
    # Update single project
    $projectPath = $projectToUpdate.ToLower()
    $projectName = $projectToUpdate.ToUpper()
    if ($projectPath -eq ".") {
        Update-Requirements-Txt -projectPath "." -isRoot $true
        Write-Host "Root project requirements.txt has been updated successfully."
    } else {
        $fullProjectPath = Join-Path -Path $repoRoot -ChildPath $projectPath
        if (-Not (Test-Path -Path $fullProjectPath)) {
            Write-Host "Project folder '$fullProjectPath' not found."
            exit 1
        }
        Update-Requirements-Txt -projectPath $projectPath -isRoot $false
        Write-Host "Project '$projectName' requirements.txt has been updated successfully."
    }
} else {
    # Update all projects
    Update-Requirements-Txt -projectPath "." -isRoot $true

    Write-Host "Workspace file: $global:workspaceFile" -ForegroundColor Cyan

    # Get the list of project folders
    $jsonContent = Get-Content $global:workspaceFile -Raw | ConvertFrom-Json
    $projectFolders = $jsonContent.folders.path

    # Iterate over each project folder (excluding the root project) and update requirements
    foreach ($folder in $projectFolders) {
        if ($folder -ne ".") {
            Update-Requirements-Txt -projectPath $folder -isRoot $false
        }
    }

    Write-Host "All requirements.txt files have been updated successfully."
}