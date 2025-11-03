# Description: This script renames an existing subproject in the workspace.
#
# Usage:
# 1. Close the workspace (File -> Close Workspace)
# 2. Open the root folder
# 3. Run: .\Rename-Sub-Project.ps1 -oldProjectName <OLD_NAME> -newProjectName <NEW_NAME>
# 4. Reopen the workspace file
#
# Parameters:
# - oldProjectName: Current name of the subproject (e.g., EXPORT-TRAINING-DATA)
# - newProjectName: New name for the subproject (e.g., TRAIN-PATENT-MODELS)
#
# Notes:
# - The script updates the workspace file and renames the project directory
# - Updates all configuration files with the new project name
# - Requires closing the workspace but VS Code can remain open
param (
    [string]$oldProjectName,
    [string]$newProjectName
)

# Determine the directory of the current script
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Load the common functions, check if the script is already sourced
if ((-not (Get-Variable -Name COMMON_INCLUDED -Scope Global -ErrorAction SilentlyContinue)) -or (-not $global:COMMON_INCLUDED)) {
    . "$scriptDir/Common.ps1"
    $global:COMMON_INCLUDED = $true
}

function Update-EnvFile {
    param (
        [string]$oldProjectPath,
        [string]$newProjectPath
    )

    $envFile = Join-Path -Path $repoRoot -ChildPath "$newProjectPath/.env"
    if (Test-Path $envFile) {
        Find-AndReplace -searchString $oldProjectPath -replaceString $newProjectPath -filePath $envFile
        Write-Output "Updated paths in .env file for project: $newProjectPath"
    }
}

function Close-Workspace {
    # Get running VS Code instances
    $vsCodeProcesses = Get-Process "Code" -ErrorAction SilentlyContinue
    
    if ($vsCodeProcesses) {
        Write-Output "Requesting VS Code to close workspace..."
        # Use VS Code CLI to close the workspace
        Start-Process "code" -ArgumentList "--remove-workspace" -Wait -NoNewWindow
        Start-Sleep -Seconds 2
        return $true
    }
    return $false
}

function Rename-FolderInWorkspace {
    param (
        [string]$workspaceFile,
        [string]$oldProjectName,
        [string]$newProjectName
    )

    $oldProjectPath = $oldProjectName.ToLower()
    $newProjectPath = $newProjectName.ToLower()
    $newProjectName = $newProjectName.ToUpper()

    # Fix: Use full paths for directory checks
    $oldFullPath = Join-Path -Path $repoRoot -ChildPath $oldProjectPath
    $newFullPath = Join-Path -Path $repoRoot -ChildPath $newProjectPath

    # Validation checks
    if (-Not (Test-Path -Path $workspaceFile)) {
        Write-Output "Workspace file '$workspaceFile' not found."
        return $false
    }

    if (-Not (Test-Path -Path $oldFullPath)) {
        Write-Output "Source project folder '$oldFullPath' not found."
        return $false
    }

    if (Test-Path -Path $newFullPath) {
        Write-Output "Target project folder '$newFullPath' already exists."
        return $false
    }

    # First: Update workspace file
    $workspaceData = Get-Content -Path $workspaceFile -Raw | ConvertFrom-Json
    $existingFolder = $workspaceData.folders | Where-Object { $_.path -eq $oldProjectPath }
    if (-not $existingFolder) {
        Write-Output "Folder '$oldProjectPath' not found in workspace."
        return $false
    }

    Write-Output "Updating workspace file..."
    $existingFolder.name = $newProjectName
    $existingFolder.path = $newProjectPath
    $workspaceData | ConvertTo-Json -Depth 10 | Set-Content -Path $workspaceFile

    # Second: Try to rename the directory with retries
    Write-Output "Renaming folder from '$oldFullPath' to '$newFullPath'..."
    $maxAttempts = 3
    $attempt = 0
    $success = $false

    while ($attempt -lt $maxAttempts -and -not $success) {
        try {
            $attempt++
            Write-Output "Attempt $attempt of $maxAttempts to rename folder..."
            
            # Try to close workspace first
            if ($attempt -gt 1) {
                Write-Output "Attempting to close workspace..."
                Close-Workspace
                Start-Sleep -Seconds 2
            }
    
            Rename-Item -Path $oldFullPath -NewName (Split-Path -Leaf $newFullPath) -Force
            $success = $true
        }
        catch {
            Write-Output "Failed attempt $attempt`: $($_.Exception.Message)"
            if ($attempt -lt $maxAttempts) {
                Write-Output "Please close the workspace manually (File -> Close Workspace) and press Enter to continue..."
                Read-Host
            }
        }
    }

    if (-not $success) {
        Write-Output "Failed to rename folder after $maxAttempts attempts."
        Write-Output "Please close Visual Studio Code and try again."
        return $false
    }

    # Third: Update configuration files
    $configFiles = @(
        (Join-Path -Path $newFullPath -ChildPath ".vscode/launch.json"),
        (Join-Path -Path $newFullPath -ChildPath ".vscode/settings.json"),
        (Join-Path -Path $newFullPath -ChildPath ".vscode/tasks.json")
    )

    foreach ($file in $configFiles) {
        if (Test-Path $file) {
            Find-AndReplace -searchString $oldProjectName.ToUpper() -replaceString $newProjectName -filePath $file
        }
    }

    Write-Output "Successfully renamed subproject from '$oldProjectName' to '$newProjectName'"
    Write-Output "Please restart Visual Studio Code for changes to take effect."
    return $true
}

if (-Not $oldProjectName) {
    $oldProjectName = Read-Host "Enter the current subproject name"
}

if (-Not $newProjectName) {
    $newProjectName = Read-Host "Enter the new subproject name"
}

if (-Not $workspaceFile) {
    Write-Output "No *.code-workspace file found at the root of the repository."
    exit 1
}

$success = Rename-FolderInWorkspace -workspaceFile $workspaceFile.FullName -oldProjectName $oldProjectName -newProjectName $newProjectName

if (-not $success) {
    Write-Output "Failed to rename subproject."
    exit 1
}