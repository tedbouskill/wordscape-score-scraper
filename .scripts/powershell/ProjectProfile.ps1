# Log the environment variable for debugging
Write-Host "VSCODE_TASK is set to: $env:VSCODE_TASK" -ForegroundColor Yellow

# Skip execution if running as part of a VS Code task
if ($env:VSCODE_TASK -eq "true") {
    Write-Host "Skipping project environment initialization in VS Code task." -ForegroundColor Red
    return
}

Write-Host "Initializing project environment..." -ForegroundColor Yellow

if (-not (Test-Path Variable:global:OriginalPrompt)) {
    $global:OriginalPrompt = $function:prompt
}

# Always set a venv prompt defaulting to ".venv" if not detected
function global:InitializeVenvPrompt {
    # Default venv name
    #$venvName = ".venv"
    
    # Create a new prompt function that will dynamically check for VIRTUAL_ENV
    function global:prompt {
        # Save the last exit code
        $origLastExitCode = $LASTEXITCODE
        
        # Check for env var when prompt runs (it may be set by then)
        $displayName = ".venv"
        if ($env:VIRTUAL_ENV) {
            $venvPath = $env:VIRTUAL_ENV
            $tempName = Split-Path -Leaf $venvPath
            
            # If it ends with Scripts (Windows) or bin (Unix), get the parent directory name
            if ($tempName -eq "Scripts" -or $tempName -eq "bin") {
                $tempName = Split-Path -Leaf (Split-Path -Parent $venvPath)
            }
            
            if ($tempName) {
                $displayName = $tempName
            }
        }
        
        # Show the venv name in green
        Write-Host "($displayName) " -NoNewline -ForegroundColor Green
        
        # Call original prompt function
        & $global:OriginalPrompt
        
        # Restore the exit code
        $global:LASTEXITCODE = $origLastExitCode
        
        # Return a space (ensures proper line breaks)
        return " "
    }
}

# Initialize the venv prompt
# NOTE: 2025-06-4 This was originally to fix a bug in VS Code which seems to be fixed!
#InitializeVenvPrompt

function global:Show-PythonEnvironment {
    $pythonExe = & { python -c "import sys; print(sys.executable)" 2>$null }
    
    if (-not $pythonExe) {
        Write-Host "No Python interpreter found in path." -ForegroundColor Red
        return
    }
    
    $pythonDir = [System.IO.Path]::GetDirectoryName($pythonExe)
    $pythonVersion = & { python -c "import sys; print('.'.join(map(str, sys.version_info[:3])))" 2>$null }
    
    # Get pip info - use python -m pip to ensure we get the pip associated with the current interpreter
    $pipVersionCmd = python -m pip --version 2>$null
    $pipVersion = if ($pipVersionCmd) { 
        $pipVersionCmd -replace 'pip ([0-9.]+).*', '$1'
    } else {
        "Not installed"
    }
    
    # Check if we're in a virtual environment
    $venvInfo = & { 
        python -c "import sys, os; venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix); print(sys.prefix if venv else '')" 2>$null 
    }
    
    # Get project folder
    $projectFolder = $env:WORKSPACE_ROOT
    if (-not $projectFolder) {
        $projectFolder = (Get-Location).Path
    }
    
    # Format the output in a nice table
    $width = 80
    $headerColor = "Cyan"
    $valueColor = "White"
    
    Write-Host ("-" * $width) -ForegroundColor $headerColor
    Write-Host " PYTHON ENVIRONMENT INFORMATION" -ForegroundColor $headerColor
    Write-Host ("-" * $width) -ForegroundColor $headerColor
    Write-Host "Project Folder:    " -NoNewline -ForegroundColor $headerColor
    Write-Host $projectFolder -ForegroundColor $valueColor
    Write-Host "Python Version:    " -NoNewline -ForegroundColor $headerColor
    Write-Host $pythonVersion -ForegroundColor $valueColor
    Write-Host "Python Executable: " -NoNewline -ForegroundColor $headerColor
    Write-Host $pythonExe -ForegroundColor $valueColor
    Write-Host "Python Directory:  " -NoNewline -ForegroundColor $headerColor
    Write-Host $pythonDir -ForegroundColor $valueColor
    Write-Host "Pip Version:       " -NoNewline -ForegroundColor $headerColor
    Write-Host $pipVersion -ForegroundColor $valueColor
    
    if ($venvInfo) {
        Write-Host "Virtual Env:       " -NoNewline -ForegroundColor $headerColor
        Write-Host $venvInfo -ForegroundColor "Green"
    } else {
        Write-Host "Virtual Env:       " -NoNewline -ForegroundColor $headerColor
        Write-Host "Not active (using system Python)" -ForegroundColor "Yellow"
    }
    Write-Host ("-" * $width) -ForegroundColor $headerColor
}

# Save the original PATH
$originalPath = $env:PATH

# Function to ensure correct pip is used
function global:pip {
    $pythonPath = & { python -c "import sys; print(sys.executable)" }
    $pipPath = [System.IO.Path]::GetDirectoryName($pythonPath)
    
    # Call the pip from the active Python environment
    & "$pipPath\python.exe" -m pip $args
}

# Function to reset environment when deactivating
function global:Restore-Environment {
    $env:PATH = $originalPath
    Remove-Item function:pip -ErrorAction SilentlyContinue
    Remove-Item function:Restore-Environment -ErrorAction SilentlyContinue
}

Write-Host "Added 'Show-PythonEnvironment' command to display Python environment info" -ForegroundColor Green
Write-Host "Project environment initialized. Use 'pip' to ensure the correct version is used." -ForegroundColor Green
Write-Host "Use 'Restore-Environment' to revert changes if needed." -ForegroundColor Yellow