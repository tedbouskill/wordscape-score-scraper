# Change to the workspace root directory
Set-Location -Path $PSScriptRoot\..\..

# Freeze the requirements excluding editable packages
pip freeze --exclude-editable > requirements.txt

# Append the editable package reference
Add-Content -Path requirements.txt -Value "-e ./__workspace_packages__"