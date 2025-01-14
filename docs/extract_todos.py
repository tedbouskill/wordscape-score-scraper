import os
import re
from pathlib import Path

def find_repository_root(current_path=None):
    """
    Finds the root of the git repository by looking for the .git folder.
    If not found, defaults to the parent of the 'docs' folder.

    Args:
        current_path (str): Starting directory. Defaults to the current working directory.

    Returns:
        str: The path to the repository root.
    """
    current_path = current_path or os.getcwd()
    current_path = Path(current_path).resolve()

    for parent in [current_path] + list(current_path.parents):
        if (parent / ".git").is_dir():
            return str(parent)
    return str(current_path.parent)  # Default to parent of 'docs'

def extract_todo_comments(repo_root, src_folder="src", relative_to="docs"):
    """
    Extract TODO comments from Python files in the src folder and generate relative links.

    Args:
        repo_root (str): The root directory of the repository.
        src_folder (str): Subdirectory to search for Python files.
        relative_to (str): Subdirectory for relative path calculation.

    Returns:
        list: A list of formatted TODO comments with relative links.
    """
    todo_comments = []
    src_path = os.path.join(repo_root, src_folder)
    todo_pattern = re.compile(r"#.*TODO.*", re.IGNORECASE)

    for root, _, files in os.walk(src_path):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                # Calculate relative path for links
                relative_path = os.path.relpath(file_path, os.path.join(repo_root, relative_to))
                display_path = os.path.relpath(file_path, src_path)  # Path relative to src/
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line_number, line in enumerate(f, start=1):
                        if match := todo_pattern.search(line):
                            # Add the relative link with display path
                            todo_comments.append(
                                f"- [{display_path}](../{relative_path}#L{line_number}): {match.group().strip()}"
                            )

    return todo_comments

def update_todo_md(repo_root, todos, todo_file="to-do.md", section_header="## TODOs from Python Files"):
    """
    Updates the to-do.md file with the new TODO comments.

    Args:
        repo_root (str): The root directory of the repository.
        todos (list): List of TODO comments to include.
        todo_file (str): Path to the to-do.md file relative to the docs folder.
        section_header (str): Header for the TODO section in the Markdown file.
    """
    todo_file_path = os.path.join(repo_root, "docs", todo_file)
    updated_content = []
    in_section = False

    # Create file if it doesn't exist
    if not os.path.exists(todo_file_path):
        with open(todo_file_path, 'w', encoding='utf-8') as f:
            f.write(f"# Project TODOs\n\n{section_header}\n\n")

    with open(todo_file_path, 'r', encoding='utf-8') as f:
        for line in f:
            # Detect the start of the section
            if line.strip() == section_header:
                in_section = True
                updated_content.append(line)
                updated_content.append("\n".join(todos) + "\n")
                # Skip existing section content
                while in_section:
                    next_line = f.readline()
                    if not next_line or next_line.startswith("#"):
                        in_section = False
                        if next_line:
                            updated_content.append(next_line)
            else:
                updated_content.append(line)

    # Write back the updated content
    with open(todo_file_path, 'w', encoding='utf-8') as f:
        f.writelines(updated_content)

def main():
    """
    Main function to extract TODOs and update the to-do.md file.
    """
    # Find the repository root
    repo_root = find_repository_root()
    print(f"Repository root found: {repo_root}")

    # Extract TODO comments
    todos = extract_todo_comments(repo_root)

    if todos:
        # Update the to-do.md file
        update_todo_md(repo_root, todos)
        print("to-do.md has been updated with the latest TODOs!")
    else:
        print("No TODO comments found.")

if __name__ == "__main__":
    main()
