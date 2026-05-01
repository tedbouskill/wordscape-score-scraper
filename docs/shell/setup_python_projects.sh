#!/bin/bash

# Notes:
# - This script sets up Python environments for multiple projects in a VS Code workspace.
# - It uses the initialize_python_environment function from the common.sh script to set up the Python environment for each project.
# - It finds the .code-workspace file at the root of the repository and extracts the project folders from it.
# - It iterates over each project folder and calls the initialize_python_environment function to configure the Python environment.

set -e  # Exit immediately if a command exits with a non-zero status

# Determine the directory of the current script
script_dir="$(dirname "${BASH_SOURCE[0]}")"

#repo_root=""
#repo_name=""

# Check if the script is already sourced
if [ -z "${SCRIPT_INCLUDED+x}" ]; then
    # shellcheck disable=SC1091
    source "$script_dir/.scripts_shell/common.sh"
    SCRIPT_INCLUDED=1
fi

# Main script execution

# Find the .code-workspace file
workspace_file=$(find . -maxdepth 1 -name "*.code-workspace" | head -n 1)

if [ -z "$workspace_file" ]; then
    echo "No *.code-workspace file found at the root of the repository."
    exit 1
fi

# Set up the root project first
initialize_python_environment "." "true"

# Get the list of project folders
project_folders=$(jq -r '.folders[].path' "$workspace_file")

# Iterate over each project folder (excluding the root project) and set up the environment
for folder in $project_folders; do
    if [ "$folder" != "." ]; then
        initialize_python_environment "$folder" "false"
    fi
done

echo "All projects have been configured successfully."
