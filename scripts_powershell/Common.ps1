# Description: Common functions for PowerShell scripts
#
# Notes:
# - Copy-TemplateIfNotExists: Copies a template file to a target path if it does not exist
# - Find-AndReplace: Finds and replaces a string in a file
# - New-Venv: Creates a new virtual environment
# - Initialize-PythonEnvironment: Initializes the Python environment for a project
# - $repo_root: The absolute path of the root of the Git repository
# - $repo_name: The folder name extracted from the path
# - $repo_name_upper: The uppercase version of the folder name

# Get the absolute path of the root of the Git repository
$repo_root = git rev-parse --show-toplevel

# Extract the folder name from the path
$repo_name = Split-Path -Leaf $repo_root
$repo_name_upper = $repo_name.ToUpper()

# Print the name of the folder
Write-Output "The root folder of the repository is: $repo_name, the project name is: $repo_name_upper"

function Copy-TemplateIfNotExists {
    param (
        [string]$templatePath,
        [string]$targetPath
    )

    if (-Not (Test-Path -Path $targetPath)) {
        Copy-Item -Path $templatePath -Destination $targetPath
    } else {
        Write-Output "File '$targetPath' already exists."
    }
}

function Find-AndReplace {
    param (
        [string]$searchString,
        [string]$replaceString,
        [string]$filePath
    )

    (Get-Content -Path $filePath) -replace $searchString, $replaceString | Set-Content -Path $filePath
}

function New-Venv {
    param (
        [string]$venvPath
    )

    if (Test-Path -Path $venvPath) {
        Write-Output "Virtual environment already exists at $venvPath"
        return
    }

    Write-Output "Creating a new virtual environment at $venvPath"
    python3 -m venv $venvPath
}

function Copy-HostFile {
    $hostFile = ""
    $targetPath = "$repo_root/host_config.json"

    if ($IsMacOS) {
        $hostFile = "$repo_root/templates/config.[HOST-MAC].json"
    } elseif ($IsWindows) {
        $hostFile = "$repo_root/templates/config.[HOST-PC].json"
    } else {
        Write-Output "Unsupported OS"
        return
    }

    if (-Not (Test-Path -Path $targetPath)) {
        Copy-Item -Path $hostFile -Destination $targetPath
        $hostName = $env:COMPUTERNAME
        (Get-Content -Path $targetPath) -replace "\[HOST\]", $hostName | Set-Content -Path $targetPath
    } else {
        Write-Output "Host file already exists at $targetPath"
    }
}

function Initialize-PythonEnvironment {
    param (
        [string]$projectPath,
        [bool]$isRoot
    )

    Write-Output "Initializing Python environment for project at $projectPath..."

    $projectPath = Resolve-Path -Path $projectPath

    Write-Output "Find and replace [REPO-NAME] with the actual repository name"
    Find-AndReplace "\[REPO-NAME\]" $repo_name_upper "$projectPath/.vscode/launch.json"

    $venvPath = "$projectPath/.venv"

    New-Venv -venvPath $venvPath

    & "$venvPath/Scripts/Activate.ps1"

    Write-Output "Upgrading pip..."
    python -m pip install --upgrade pip

    $pythonpath = ""

    if ($isRoot) {
        Write-Output "Registering repo_packages in the root project..."
        pip install -e "$projectPath/repo_packages"
        $pythonpath = "$projectPath/repo_packages"
        Copy-HostFile
    } else {
        Write-Output "Registering repo_packages and workspace_packages in subproject..."
        $repoPath = Resolve-Path -Path "$projectPath/../repo_packages"
        $workspacePath = Resolve-Path -Path "$projectPath/workspace_packages"
        pip install -e $repoPath
        pip install -e $workspacePath
        $pythonpath = "$repoPath;$workspacePath"
    }

    Write-Output "Creating .env file with fully qualified PYTHONPATH..."
    Set-Content -Path "$projectPath/.env" -Value "PYTHONPATH=$pythonpath"

    $requirementsPath = "$projectPath/requirements.txt"
    if (Test-Path -Path $requirementsPath) {
        Write-Output "Installing dependencies from $requirementsPath..."
        pip install -r $requirementsPath
    }

    Write-Output "Deactivating virtual environment..."
    deactivate
}