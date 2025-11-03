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
    python3.11 -m venv "$venv_path"
}

copy_host_file() {
    local host_file=""
    local target_path=""

    if [ "$(uname)" == "Darwin" ]; then
        host_file="$repo_root/.templates/config.[HOST-MAC].json"
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
        # shellcheck disable=SC2155
        local host_name=$(hostname)
        sed -i '' "s/\[HOST-MAC\]/$host_name/g" "$target_path"
    else
        echo "Host file already exists at $target_path"
    fi
}

# Function to update requirements.txt for a project
update_requirements_txt() {
    local project_path="$1"
    local is_root="$2"

    # Convert relative path to absolute path relative to repo root
    local full_project_path=""
    if [ "$project_path" == "." ]; then
        full_project_path="$repo_root"
    else
        full_project_path="$repo_root/$project_path"
    fi

    if [ ! -d "$full_project_path" ]; then
        echo "Error: Project path not found: $full_project_path" >&2
        return 1
    fi

    echo "Recreating requirements.txt in project $project_path..."

    local venv_path="$full_project_path/.venv"

    if [ ! -d "$venv_path" ]; then
        echo "Error: Virtual environment not found at $venv_path" >&2
        return 1
    fi

    # Store current location
    local original_location=$(pwd)

    # Use a subshell to ensure we return to original location
    (
        # Change to the project directory
        cd "$full_project_path" || exit 1

        # Activate the virtual environment
        source "$venv_path/bin/activate"

        # Freeze the requirements excluding editable packages
        pip freeze --exclude-editable > requirements.txt

        # Append the editable package references
        if [ "$is_root" != "true" ]; then
            echo "-e ../__workspace_packages__" >> requirements.txt
            echo "-e ./__project_packages__" >> requirements.txt
        else
            echo "-e ./__workspace_packages__" >> requirements.txt
        fi

        # Deactivate the virtual environment
        deactivate
    )

    # Return to original location (this happens automatically after subshell)
    cd "$original_location" || return 1
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
        echo "Registering __workspace_packages__ in the root project..."
        pip install -e "$project_path/__workspace_packages__"
        pythonpath="$project_path/__workspace_packages__"
        copy_host_file
    else
        echo "Registering __workspace_packages__ and __project_packages__ in subproject..."
        repo_path=$(cd "$project_path/../__workspace_packages__" && pwd)
        workspace_path=$(cd "$project_path/__project_packages__" && pwd)
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
    else
    # To Do: Ensure the __workspace_packages__ and __project_packages__ are set to editable before creating the requirements.txt file
        echo "No requirements.txt found."
    #    pip freeze > "$requirements_path"
    #    echo "requirements.txt created at $requirements_path"
    fi

    # Deactivate the virtual environment
    echo "Deactivating virtual environment..."
    deactivate
}

