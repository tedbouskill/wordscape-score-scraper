# Description: This script adds a subproject to the workspace and sets up the necessary folders and files.
#
# Notes:
# - This script adds a subproject to the workspace and sets up the necessary folders and files.
# - The script prompts for the subproject name (relative path) and then adds it to the workspace.
# - It creates the subproject folder, .vscode folder, and standard configuration files.
# - It also creates the __project_packages__ folder and copies the setup.py and setup.cfg files.
# - The script uses the Common.ps1 script for shared functions and variables.

param (
    [string]$subProjectName
)

# Determine the directory of the current script
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Load the common functions, check if the script is already sourced
if ((-not (Get-Variable -Name COMMON_INCLUDED -Scope Global -ErrorAction SilentlyContinue)) -or (-not $global:COMMON_INCLUDED)) {
    . "$scriptDir/Common.ps1"
    $global:COMMON_INCLUDED = $true
}

function Add-FolderToWorkspace {
    param (
        [string]$workspaceFile,
        [string]$subProjectName,
        [string]$subProjectPath
    )

    if (-Not (Test-Path -Path $workspaceFile)) {
        Write-Output "Workspace file '$workspaceFile' not found."
        return
    }

    $workspaceData = Get-Content -Path $workspaceFile -Raw | ConvertFrom-Json

    if ($workspaceData.folders | Where-Object { $_.path -eq $subProjectPath }) {
        Write-Output "Folder '$subProjectPath' is already in the workspace."
    } else {
        $workspaceData.folders += [PSCustomObject]@{ name = $subProjectName; path = $subProjectPath }
        $workspaceData | ConvertTo-Json -Depth 10 | Set-Content -Path $workspaceFile
    }

    if (-Not (Test-Path -Path "$repoRoot/$subProjectPath")) {
        New-Item -ItemType Directory -Path "$repoRoot/$subProjectPath" | Out-Null
    }

    if (-Not (Test-Path -Path "$repoRoot/$subProjectPath/.vscode")) {
        New-Item -ItemType Directory -Path "$repoRoot/$subProjectPath/.vscode" | Out-Null
    }

    Write-Output "Subproject '$subProjectName' with path '$subProjectPath' added to the workspace."
}

if (-Not $subProjectName) {
    $subProjectName = Read-Host "Enter the Sub-Project name (relative path)"
}

if (-Not $workspaceFile) {
    Write-Output "No *.code-workspace file found at the root of the repository."
    exit 1
}

$subProjectName = $subProjectName.ToUpper()
$subProjectPath = $subProjectName.ToLower()

Add-FolderToWorkspace -workspaceFile $workspaceFile.FullName -subProjectName $subProjectName -subProjectPath $subProjectPath

if (-Not (Test-Path -Path "$repoRoot/$subProjectPath")) {
    New-Item -ItemType Directory -Path "$repoRoot/$subProjectPath" | Out-Null
}

if (-Not (Test-Path -Path "$repoRoot/$subProjectPath/.vscode")) {
    New-Item -ItemType Directory -Path "$repoRoot/$subProjectPath/.vscode" | Out-Null
}

function Update-VSCodeConfig {
    param (
        [string]$repoRoot,
        [string]$subProjectPath,
        [string]$repoName,
        [string]$subProjectName
    )

    $vscodePath = "$repoRoot/$subProjectPath/.vscode"
    $templates = @{
        'launch.json'   = @{path = "$repoRoot/.templates/launch.json"; target = "$vscodePath/launch.json"}
        'settings.json' = @{path = "$repoRoot/.templates/settings.json"; target = "$vscodePath/settings.json"}
        'tasks.json'    = @{path = "$repoRoot/.templates/tasks.json"; target = "$vscodePath/tasks.json"}
    }

    foreach ($template in $templates.GetEnumerator()) {
        Copy-TemplateIfNotExists -templatePath $template.Value.path -targetPath $template.Value.target
        Find-AndReplace -searchString "%REPO-NAME%" -replaceString $repoName -filePath $template.Value.target
        Find-AndReplace -searchString "%PROJECT-NAME%" -replaceString $subProjectName -filePath $template.Value.target
    }
}

Update-VSCodeConfig -repoRoot $repoRoot -subProjectPath $subProjectPath -repoName $repoName -subProjectName $subProjectName

if (-Not (Test-Path -Path "$repoRoot/$subProjectPath/__project_packages__")) {
    New-Item -ItemType Directory -Path "$repoRoot/$subProjectPath/__project_packages__" | Out-Null
}

Copy-TemplateIfNotExists -templatePath "$repoRoot/.templates/setup.py" -targetPath "$repoRoot/$subProjectPath/__project_packages__/setup.py"
Copy-TemplateIfNotExists -templatePath "$repoRoot/.templates/setup.cfg" -targetPath "$repoRoot/$subProjectPath/__project_packages__/setup.cfg"

Initialize-PythonEnvironment -projectPath "$repoRoot/$subProjectPath" -isRoot $false
