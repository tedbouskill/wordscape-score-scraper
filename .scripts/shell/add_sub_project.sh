#!/bin/bash

# Notes:
# - This script adds a subproject to the workspace and sets up the necessary folders and files.
# - The script prompts for the subproject name (relative path) and then adds it to the workspace.
# - It creates the subproject folder, .vscode folder, and standard configuration files.
# - It also creates the __project_packages__ folder and copies the setup.py and setup.cfg files.
# - The script uses the common.sh script for shared functions and variables.

set -e  # Exit immediately if a command exits with a non-zero status

# Determine the directory of the current script
script_dir="$(dirname "${BASH_SOURCE[0]}")"

repo_root=""
repo_name=""
repo_name_upper=""

# Check if the script is already sourced
if [ -z "${SCRIPT_INCLUDED+x}" ]; then
    # shellcheck disable=SC1091
    source "$script_dir/common.sh"
    SCRIPT_INCLUDED=1
fi

# Function to add a folder to the workspace
add_folder_to_workspace() {
    local workspace_file="$1"
    local subproject_name="$2"

    local subproject_name_upper
    subproject_name_upper=$(echo "$subproject_name" | tr '[:lower:]' '[:upper:]')

    local subproject_path
    subproject_path=$(echo "$subproject_name" | tr '[:upper:]' '[:lower:]')

    if [ ! -f "$workspace_file" ]; then
        echo "Workspace file '$workspace_file' not found."
    fi

    # Read the workspace file
    workspace_data=$(cat "$workspace_file")

    # Check if the folder already exists
    if echo "$workspace_data" | grep -q "\"path\": \"$subproject_path\""; then
        echo "Folder '$subproject_path' is already in the workspace."
    else
        # Add the new folder entry
        updated_workspace_data=$(echo "$workspace_data" | jq --arg name "$subproject_name_upper" --arg path "$subproject_path" '.folders += [{"name": $name, "path": $path}]')
    fi

    # Save the updated workspace file
    echo "$updated_workspace_data" > "$workspace_file"

    # Create the subfolder if it doesn't exist
    if [ ! -d "$subproject_path" ]; then
        mkdir "$subproject_path"
    fi

    # Create standard subproject folders and files

    # Create .vscode folder
    if [ ! -d "$subproject_path/.vscode" ]; then
        mkdir "$subproject_path/.vscode"
    fi

    # Copy

    echo "Subproject '$subproject_name_upper' with path '$subproject_path' added to the workspace."
}

# Prompt for workspace file and subfolder name
# shellcheck disable=SC2162
read -p "Enter the subproject name (relative path): " subfolder_name

# Find the .code-workspace file
workspace_file=$(find . -maxdepth 1 -name "*.code-workspace" | head -n 1)

if [ -z "$workspace_file" ]; then
    echo "No *.code-workspace file found at the root of the repository."
    exit 1
fi

add_folder_to_workspace "$workspace_file" "$subfolder_name"

# Create the subproject folder if it doesn't exist
if [ ! -d "$repo_root/$subfolder_name" ]; then
    mkdir "$repo_root/$subfolder_name"
fi

# Create the subproject .vscode folder if it doesn't exist
if [ ! -d "$repo_root/$subfolder_name/.vscode" ]; then
    mkdir "$repo_root/$subfolder_name/.vscode"
fi

# Copy the launch.json file to the .vscode folder
copy_template_if_not_exists "$repo_root/.templates/launch.json" "$repo_root/$subfolder_name/.vscode/launch.json"
# Find and replace [REPO-NAME] with the actual repository name
find_and_replace "\[REPO-NAME\]" "$repo_name_upper" "$repo_root/$subfolder_name/.vscode/launch.json"

# Copy the settings.json file to the .vscode folder
copy_template_if_not_exists "$repo_root/.templates/settings.json" "$repo_root/$subfolder_name/.vscode/settings.json"
# Find and replace [REPO-NAME] with the actual repository name
find_and_replace "\[REPO-NAME\]" "$repo_name_upper" "$repo_root/$subfolder_name/.vscode/settings.json"

# Copy the tasks.json file to the .vscode folder
copy_template_if_not_exists "$repo_root/.templates/tasks.json" "$repo_root/$subfolder_name/.vscode/tasks.json"

# Create the subproject __project_packages__ folder if it doesn't exist
if [ ! -d "$repo_root/$subfolder_name/__project_packages__" ]; then
    mkdir "$repo_root/$subfolder_name/__project_packages__"
fi

# Copy the setup.py file to the __project_packages__ folder
copy_template_if_not_exists "$repo_root/.templates/setup.py" "$repo_root/$subfolder_name/__project_packages__/setup.py"

# Copy the setup.cfg file to the __project_packages__ folder
copy_template_if_not_exists "$repo_root/.templates/setup.cfg" "$repo_root/$subfolder_name/__project_packages__/setup.cfg"

initialize_python_environment "$repo_root/$subfolder_name" "false"