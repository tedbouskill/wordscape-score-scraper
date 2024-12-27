#!/bin/bash

# Notes:
# - This script contains common functions and variables used by other scripts.
# - It defines the repo_root and repo_name variables.
# - It contains functions to copy a template file if it doesn't exist, find and replace a string in a file, and set up a Python environment.
# - The script is sourced by other scripts to reuse these functions and variables.

# Get the absolute path of the root of the Git repository
repo_root=$(git rev-parse --show-toplevel)

# Extract the folder name from the path
repo_name=$(basename "$repo_root")
repo_name_upper=$(echo "$repo_name" | tr '[:lower:]' '[:upper:]')

# Print the name of the folder
echo "The root folder of the repository is: $repo_name, the project name is: $repo_name_upper"

copy_template_if_not_exists() {
    local template_path=$1
    local target_path=$2

    if [ ! -f "$target_path" ]; then
        cp "$template_path" "$target_path"
    else
        echo "File '$target_path' already exists."
    fi
}

# Function to find and replace a string in a file
find_and_replace() {
    local search_string=$1
    local replace_string=$2
    local file_path=$3

    sed -i '' "s/$search_string/$replace_string/g" "$file_path"
}

# Function to create a virtual environment
new_venv() {
    local venv_path=$1

    # Check if the virtual environment already exists
    if [ -d "$venv_path" ]; then
        echo "Virtual environment already exists at $venv_path"
        return
    fi

    # Create a new virtual environment
    echo "Creating a new virtual environment at $venv_path"
    python3 -m venv "$venv_path"
}

copy_host_file() {
    local host_file=""
    local target_path=""

    if [ "$(uname)" == "Darwin" ]; then
        host_file="$repo_root/templates/config.[HOST-MAC].json"
        target_path="$repo_root/config.$(hostname).json"
    elif [ "$(uname)" == "Linux" ]; then
        echo "Unsupported OS: Linux"
        return 1
    else
        echo "Unsupported OS"
        return 1
    fi

    if [ ! -f "$target_path" ]; then
        cp "$host_file" "$target_path"
        local host_name=$(hostname)
        sed -i '' "s/\[HOST-MAC\]/$host_name/g" "$target_path"
    else
        echo "Host file already exists at $target_path"
    fi
}

# Function to set up the Python environment for each project
initialize_python_environment() {
    local project_path="$1"
    local is_root="$2"

    echo "Configuring Python environment for project at $project_path..."

    # Convert project_path to an absolute path
    project_path=$(cd "$project_path" && pwd)

    echo "Find and replace [REPO-NAME] with the actual repository name"
    find_and_replace "\[REPO-NAME\]" "$repo_name_upper" "$project_path/.vscode/launch.json"

    # Check if a virtual environment already exists in .venv
    local venv_path="$project_path/.venv"

    new_venv "$venv_path"

    # Activate the virtual environment
    # shellcheck disable=SC1091
    source "$venv_path/bin/activate"

    # Upgrade pip using python -m pip
    echo "Upgrading pip..."
    python -m pip install --upgrade pip

    # Initialize PYTHONPATH
    local pythonpath=""

    # Register editable packages
    if [ "$is_root" == "true" ]; then
        echo "Registering repo_packages in the root project..."
        pip install -e "$project_path/repo_packages"
        pythonpath="$project_path/repo_packages"
        copy_host_file
    else
        echo "Registering repo_packages and workspace_packages in subproject..."
        repo_path=$(cd "$project_path/../repo_packages" && pwd)
        workspace_path=$(cd "$project_path/workspace_packages" && pwd)
        pip install -e "$repo_path"
        pip install -e "$workspace_path"
        pythonpath="$repo_path:$workspace_path"
    fi

    # Create or overwrite the .env file with the absolute PYTHONPATH
    echo "Creating .env file with fully qualified PYTHONPATH..."
    echo "PYTHONPATH=$pythonpath" > "$project_path/.env"

    # Check if requirements.txt exists
    local requirements_path="$project_path/requirements.txt"
    if [ -f "$requirements_path" ]; then
        echo "Installing dependencies from $requirements_path..."
        pip install -r "$requirements_path"
    #else
    # To Do: Ensure the repo_packages and workspace_packages are set to editable before creating the requirements.txt file
    #    echo "No requirements.txt found. Creating one..."
    #    pip freeze > "$requirements_path"
    #    echo "requirements.txt created at $requirements_path"
    fi

    # Deactivate the virtual environment
    echo "Deactivating virtual environment..."
    deactivate
}

