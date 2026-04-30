# Description: Common functions for PowerShell scripts
#
# Notes:
# - Copy-TemplateIfNotExists: Copies a template file to a target path if it does not exist
# - Find-AndReplace: Finds and replaces a string in a file
# - New-Venv: Creates a new virtual environment
# - Initialize-PythonEnvironment: Initializes the Python environment for a project
# - $repoRoot: The absolute path of the root of the Git repository
# - $repoFolder: The folder name extracted from the path
# - $repoName: The uppercase version of the folder name

Write-Host "Common.ps1 execution started." -ForegroundColor Green

# Get the absolute path of the root of the Git repository
$repoRoot = git rev-parse --show-toplevel
if (-Not $repoRoot) {
    Write-Error "Failed to determine the root of the Git repository."
} else {
    Write-Output "Git repository root: $repoRoot"
}

# Extract the folder name from the path
$repoFolder = Split-Path -Leaf $repoRoot
$repoFolder = $repoFolder.ToLower()
$repoName = $repoFolder.ToUpper()

$workspaceFileName = $repoFolder + ".code-workspace"
$workspaceFile = Get-Item $workspaceFileName
if (-Not $workspaceFile) {
    Write-Error "No *.code-workspace file found in the repository root: $repoRoot"
} else {
    Write-Output "Workspace file found: $workspaceFile"
}
$global:workspaceFile = $workspaceFile  # Add this line to make it accessible globally

# Print the name of the folder
Write-Output "Root Repository: $repoFolder, Root Project Name: $repoName, Workspace File: $workspaceFile"

function Use-ProjectPip {
    # Override pip command to always use the correct one
    function global:pip {
        $pythonPath = & { python -c "import sys; print(sys.executable)" }
        $pipPath = [System.IO.Path]::GetDirectoryName($pythonPath)
        
        # Call the pip from the active Python environment
        & "$pipPath\python.exe" -m pip $args
    }
    
    Write-Host "Using project-specific pip (linked to active Python interpreter)" -ForegroundColor Green
}

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
    python3.11 -m venv $venvPath
}

function Copy-HostFile {
    $hostFile = "$repoRoot/.templates/config.%HOST-PC%.json"
    $targetPath = "$repoRoot/config.$env:COMPUTERNAME.json"

    try {
        $resolvedHostFile = (Resolve-Path -LiteralPath $hostFile -ErrorAction Stop).Path
        Write-Output "Resolved host file path: $resolvedHostFile"
    } catch {
        Write-Error "Failed to resolve host file path: $hostFile"
        return
    }

    if (-Not (Test-Path -LiteralPath $targetPath)) {
        if (Test-Path -LiteralPath $hostFile) {
            try {
                Write-Output "Copying $hostFile to $targetPath"
                Copy-Item -LiteralPath $hostFile -Destination $targetPath -ErrorAction Stop
                $hostName = $env:COMPUTERNAME
                (Get-Content -Path $targetPath) -replace "%HOST-PC%", $hostName | Set-Content -Path $targetPath
            } catch {
                Write-Error "Failed to copy or modify the host file: $_"
            }
        } else {
            Write-Error "Source host file does not exist: $hostFile"
        }
    } else {
        Write-Output "Host file already exists at $targetPath"
    }
}

function Update-Requirements-Txt {
    param (
        [string]$projectPath,
        [bool]$isRoot
    )

    # Convert relative path to absolute path relative to repo root
    if ($projectPath -eq ".") {
        $fullProjectPath = $repoRoot
    } else {
        $fullProjectPath = Join-Path -Path $repoRoot -ChildPath $projectPath
    }

    if (-Not (Test-Path -Path $fullProjectPath)) {
        Write-Error "Project path not found: $fullProjectPath"
        return
    }

    Write-Output "Recreating requirements.txt in project $projectPath..."

    $venvPath = Join-Path -Path $fullProjectPath -ChildPath ".venv"

    if (-Not (Test-Path -Path $venvPath)) {
        Write-Error "Virtual environment not found at $venvPath"
        return
    }

    # Store current location
    $originalLocation = Get-Location

    try {
        # Change to the project directory
        Set-Location -Path $fullProjectPath

        & "$venvPath/scripts/Activate.ps1"

        # Freeze the requirements excluding editable packages
        pip freeze --exclude-editable | Where-Object { 
            ($_ -notmatch "^workspace-packages==") -and 
            ($_ -notmatch "^project-packages==") 
        } > requirements.txt

        # Append the editable package references        
        if (-Not $isRoot) {
            Add-Content -Path requirements.txt -Value "-e ../__workspace_packages__"
            Add-Content -Path requirements.txt -Value "-e ./__project_packages__"
        } else {
            Add-Content -Path requirements.txt -Value "-e ./__workspace_packages__"
            Add-Content -Path requirements.txt -Value "-e ./__project_packages__"
        }

        # Deactivate the virtual environment
        deactivate
    }
    finally {
        # Always restore original location
        Set-Location -Path $originalLocation
    }
}

function Initialize-PythonEnvironment {
    param (
        [string]$projectPath,
        [bool]$isRoot
    )

    Write-Output "Initializing Python environment for project at $projectPath..."

    $projectPath = Resolve-Path -Path $projectPath

    if (-Not $isRoot) {
        Set-Location -Path $projectPath
    }

    Write-Output "Find and replace %REPO-NAME% with the actual repository name"
    Find-AndReplace "%REPO-NAME%" $repoName "$projectPath/.vscode/launch.json"

    $venvPath = "$projectPath/.venv"

    New-Venv -venvPath $venvPath

    & "$venvPath/scripts/Activate.ps1"

    Write-Output "Upgrading pip..."
    python -m pip install --upgrade pip

    $pythonpath = ""

    if ($isRoot) {
        Write-Output "Registering __workspace_packages__ in the root project..."
        pip install -e "$projectPath/__workspace_packages__"
        $pythonpath = "$projectPath/__workspace_packages__"
        Copy-HostFile
    } else {
        Write-Output "Registering __workspace_packages__ and __project_packages__ in subproject..."
        $repoPath = Resolve-Path -Path "$projectPath/../__workspace_packages__"
        $workspacePath = Resolve-Path -Path "$projectPath/__project_packages__"
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

    if (-Not $isRoot) {
        Set-Location -Path $repoRoot
    }
}