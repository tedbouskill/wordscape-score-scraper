# Description: This script adds a subproject to the workspace and sets up the necessary folders and files.
#
# Notes:
# - This script adds a subproject to the workspace and sets up the necessary folders and files.
# - The script prompts for the subproject name (relative path) and then adds it to the workspace.
# - It creates the subproject folder, .vscode folder, and standard configuration files.
# - It also creates the workspace_packages folder and copies the setup.py and setup.cfg files.
# - The script uses the Common.ps1 script for shared functions and variables.

param (
    [string]$subfolderName
)

# Determine the directory of the current script
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Check if the script is already sourced
if (-Not $global:SCRIPT_INCLUDED) {
    . "$scriptDir/Common.ps1"
    $global:SCRIPT_INCLUDED = $true
}

function Add-FolderToWorkspace {
    param (
        [string]$workspaceFile,
        [string]$subprojectName
    )

    $subprojectNameUpper = $subprojectName.ToUpper()
    $subprojectPath = $subprojectName.ToLower()

    if (-Not (Test-Path -Path $workspaceFile)) {
        Write-Output "Workspace file '$workspaceFile' not found."
        return
    }

    $workspaceData = Get-Content -Path $workspaceFile -Raw | ConvertFrom-Json

    if ($workspaceData.folders | Where-Object { $_.path -eq $subprojectPath }) {
        Write-Output "Folder '$subprojectPath' is already in the workspace."
    } else {
        $workspaceData.folders += [PSCustomObject]@{ name = $subprojectNameUpper; path = $subprojectPath }
        $workspaceData | ConvertTo-Json -Depth 10 | Set-Content -Path $workspaceFile
    }

    if (-Not (Test-Path -Path $subprojectPath)) {
        New-Item -ItemType Directory -Path $subprojectPath | Out-Null
    }

    if (-Not (Test-Path -Path "$subprojectPath/.vscode")) {
        New-Item -ItemType Directory -Path "$subprojectPath/.vscode" | Out-Null
    }

    Write-Output "Subproject '$subprojectNameUpper' with path '$subprojectPath' added to the workspace."
}

if (-Not $subfolderName) {
    $subfolderName = Read-Host "Enter the subproject name (relative path)"
}

$workspaceFile = Get-ChildItem -Path . -Filter "*.code-workspace" -Depth 0 | Select-Object -First 1

if (-Not $workspaceFile) {
    Write-Output "No *.code-workspace file found at the root of the repository."
    exit 1
}

Add-FolderToWorkspace -workspaceFile $workspaceFile.FullName -subprojectName $subfolderName

if (-Not (Test-Path -Path "$repo_root/$subfolderName")) {
    New-Item -ItemType Directory -Path "$repo_root/$subfolderName" | Out-Null
}

if (-Not (Test-Path -Path "$repo_root/$subfolderName/.vscode")) {
    New-Item -ItemType Directory -Path "$repo_root/$subfolderName/.vscode" | Out-Null
}

Copy-TemplateIfNotExists -templatePath "$repo_root/templates/launch.json" -targetPath "$repo_root/$subfolderName/.vscode/launch.json"
Find-AndReplace -searchString "\[REPO-NAME\]" -replaceString $repo_name_upper -filePath "$repo_root/$subfolderName/.vscode/launch.json"

Copy-TemplateIfNotExists -templatePath "$repo_root/templates/settings.json" -targetPath "$repo_root/$subfolderName/.vscode/settings.json"
Find-AndReplace -searchString "\[REPO-NAME\]" -replaceString $repo_name_upper -filePath "$repo_root/$subfolderName/.vscode/settings.json"

Copy-TemplateIfNotExists -templatePath "$repo_root/templates/tasks.json" -targetPath "$repo_root/$subfolderName/.vscode/tasks.json"

if (-Not (Test-Path -Path "$repo_root/$subfolderName/workspace_packages")) {
    New-Item -ItemType Directory -Path "$repo_root/$subfolderName/workspace_packages" | Out-Null
}

Copy-TemplateIfNotExists -templatePath "$repo_root/templates/setup.py" -targetPath "$repo_root/$subfolderName/workspace_packages/setup.py"
Copy-TemplateIfNotExists -templatePath "$repo_root/templates/setup.cfg" -targetPath "$repo_root/$subfolderName/workspace_packages/setup.cfg"

Initialize-PythonEnvironment -projectPath "$repo_root/$subfolderName" -isRoot $false
