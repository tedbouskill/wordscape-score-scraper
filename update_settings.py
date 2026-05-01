import os
import json
from pathlib import Path

def find_repo_root():
    """
    Finds the repository root.
    """
    current_path = Path.cwd()
    while current_path != current_path.parent:
        if (current_path / '.git').exists():
            return current_path
        current_path = current_path.parent
    return None

def find_workspace_file():
    """
    Finds the first `.code-workspace` file in the repository root.
    """
    repo_root = find_repo_root()
    if not repo_root:
        print("Repository root not found.")
        return None

    for file in os.listdir(repo_root):
        if file.endswith(".code-workspace"):
            return repo_root / file
    return None

def get_workspace_folders(workspace_file):
    """
    Extracts the project paths from the `folders` section of the workspace file.
    """
    with open(workspace_file, "r") as file:
        workspace = json.load(file)

    if "folders" not in workspace:
        print("No 'folders' section found in the workspace file.")
        return []

    return [folder["path"] for folder in workspace["folders"]]

def update_json_file(file_path, new_data):
    """
    Updates a JSON file only if the content needs to be changed.
    """
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    with open(file_path, "r") as file:
        current_data = json.load(file)

    if current_data == new_data:
        print(f"No changes needed for: {file_path}")
        return

    with open(file_path, "w") as file:
        json.dump(new_data, file, indent=4)
        print(f"Updated file: {file_path}")

def update_workspace_file(workspace_file):
    """
    Updates the `.code-workspace` file with the appropriate interpreter path.
    """
    with open(workspace_file, "r") as file:
        workspace = json.load(file)

    if "settings" not in workspace:
        workspace["settings"] = {}

    if os.name == "nt":  # Windows
        interpreter_path = ".venv\\Scripts\\python.exe"
    else:
        interpreter_path = ".venv/bin/python"

    new_settings = workspace["settings"].copy()
    new_settings["python.defaultInterpreterPath"] = interpreter_path

    if workspace["settings"] != new_settings:
        workspace["settings"] = new_settings
        with open(workspace_file, "w") as file:
            json.dump(workspace, file, indent=4)
            print(f"Updated workspace file: {workspace_file}")
    else:
        print(f"No changes needed for workspace file: {workspace_file}")

def update_project_settings(project_paths):
    """
    Updates `.vscode/settings.json` files for each project path in the workspace.
    """
    for project_path in project_paths:
        settings_path = Path(project_path) / ".vscode/settings.json"
        if not settings_path.exists():
            print(f"Settings file not found for project: {settings_path}")
            continue

        if os.name == "nt":  # Windows
            interpreter_path = ".venv\\Scripts\\python.exe"
        else:
            interpreter_path = ".venv/bin/python"

        with open(settings_path, "r") as file:
            settings = json.load(file)

        new_settings = settings.copy()
        new_settings["python.defaultInterpreterPath"] = interpreter_path

        if settings != new_settings:
            with open(settings_path, "w") as file:
                json.dump(new_settings, file, indent=4)
                print(f"Updated settings for project: {settings_path}")
        else:
            print(f"No changes needed for project settings: {settings_path}")

def update_root_settings():
    """
    Updates the root `.vscode/settings.json` file if it exists.
    """
    settings_path = Path(".vscode/settings.json")
    if not settings_path.exists():
        print(f"Root settings file not found: {settings_path}")
        return

    if os.name == "nt":  # Windows
        interpreter_path = ".venv\\Scripts\\python.exe"
    else:
        interpreter_path = ".venv/bin/python"

    with open(settings_path, "r") as file:
        settings = json.load(file)

    new_settings = settings.copy()
    new_settings["python.defaultInterpreterPath"] = interpreter_path

    if settings != new_settings:
        with open(settings_path, "w") as file:
            json.dump(new_settings, file, indent=4)
            print(f"Updated root settings: {settings_path}")
    else:
        print(f"No changes needed for root settings: {settings_path}")

def main():
    """
    Main function to update all configuration files.
    """
    # Find the workspace file
    workspace_file = find_workspace_file()
    if workspace_file:
        print(f"Workspace file found: {workspace_file}")
        # Update workspace settings
        update_workspace_file(workspace_file)

        # Get project paths from the workspace file
        project_paths = get_workspace_folders(workspace_file)

        # Update project settings
        update_project_settings(project_paths)
    else:
        print("No workspace file found.")

    # Update root settings
    update_root_settings()

if __name__ == "__main__":
    main()
