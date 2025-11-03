import os
import re
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from typing import List, Tuple

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

def process_file(file_path: Path, repo_root: Path) -> List[str]:
    """
    Process a single file to extract TODO comments.

    Args:
        file_path (Path): Path to the file
        repo_root (Path): Path to the repository root

    Returns:
        List[str]: List of formatted TODO comments
    """
    todo_comments = []
    single_line_pattern = re.compile(r"#\s*TODO\s*:\s*(.*)", re.IGNORECASE)
    multi_line_pattern = re.compile(r"#\s*<TODO>(.*?)</TODO>", re.IGNORECASE | re.DOTALL)
    
    try:
        # Calculate relative paths
        relative_path = file_path.relative_to(repo_root)
        display_path = relative_path
        
        # Read file content
        content = file_path.read_text(encoding='utf-8')
        lines = content.splitlines()
        
        # Process each line for single-line TODOs
        for line_number, line in enumerate(lines, start=1):
            if match := single_line_pattern.search(line):
                todo_text = match.group(1).strip()  # Get the text after 'TODO:'
                todo_comments.append(
                    f"- [{display_path}](../{relative_path}#L{line_number}): {todo_text}"
                )
        
        # Process multi-line TODOs
        for match in multi_line_pattern.finditer(content):
            # Find the line number of the start of the TODO block
            start_line = content[:match.start()].count('\n') + 1
            todo_text = match.group(1).strip()
            # Remove any leading '# ' from each line
            cleaned_lines = [line.lstrip('# ').strip() for line in todo_text.split('\n')]
            # Format multi-line TODOs with proper indentation
            formatted_todo = "\n  ".join(cleaned_lines)
            todo_comments.append(
                f"- [{display_path}](../{relative_path}#L{start_line}):\n  {formatted_todo}"
            )
            
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
    
    return todo_comments

def extract_todo_comments(repo_root: str) -> List[str]:
    """
    Extract TODO comments from Python, Shell, and PowerShell files throughout the repository.

    Args:
        repo_root (str): The root directory of the repository.

    Returns:
        list: A list of formatted TODO comments with relative links.
    """
    repo_path = Path(repo_root)
    
    # Get all relevant files using pathlib, excluding .venv directories
    source_files = []
    for ext in ['.py', '.sh', '.ps1']:
        files = [
            f for f in repo_path.rglob(f"*{ext}")
            if ".venv" not in f.parts  # Exclude files in .venv directories
        ]
        print(f"Found {len(files)} {ext} files")
        source_files.extend(files)
    
    print(f"Total files to process: {len(source_files)}")
    
    # Process files in parallel
    todo_comments = []
    with ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(process_file, file_path, repo_path)
            for file_path in source_files
        ]
        
        for future in futures:
            result = future.result()
            if result:
                print(f"Found TODOs in: {result[0].split(']')[0][2:]}")
            todo_comments.extend(result)
    
    print(f"Total TODOs found: {len(todo_comments)}")
    return todo_comments

def update_todo_md(repo_root: str, todos: List[str], todo_file: str = "to-do.md", section_header: str = "## TODOs from Source Files"):
    """
    Updates the to-do.md file with the new TODO comments.

    Args:
        repo_root (str): The root directory of the repository.
        todos (list): List of TODO comments to include.
        todo_file (str): Path to the to-do.md file relative to the docs folder.
        section_header (str): Header for the TODO section in the Markdown file.
    """
    todo_file_path = Path(repo_root) / "docs" / todo_file
    print(f"Updating {todo_file_path}")
    
    # Create file if it doesn't exist
    if not todo_file_path.exists():
        print(f"Creating new {todo_file}")
        todo_file_path.write_text(f"# Project TODOs\n\n{section_header}\n\n", encoding='utf-8')
        return

    # Read existing content
    content = todo_file_path.read_text(encoding='utf-8').splitlines()
    print(f"Read {len(content)} lines from {todo_file}")
    
    # Find the section (case-insensitive)
    section_index = -1
    for i, line in enumerate(content):
        if line.strip().lower() == section_header.lower():
            section_index = i
            break
    
    if section_index == -1:
        print(f"Section '{section_header}' not found, appending to end")
        # If section not found, append to end
        content.extend(["", section_header, ""])
        content.extend(todos)
    else:
        print(f"Found section at line {section_index}")
        # Find the next section or end of file
        next_section_index = len(content)
        for i in range(section_index + 1, len(content)):
            if content[i].startswith("#"):
                next_section_index = i
                break
        
        # Replace the section content
        new_content = content[:section_index + 1]
        new_content.append("")  # Add blank line after header
        new_content.extend(todos)
        new_content.append("")  # Add blank line after TODOs
        new_content.extend(content[next_section_index:])
        content = new_content

    # Write back the updated content
    todo_file_path.write_text("\n".join(content) + "\n", encoding='utf-8')
    print(f"Updated {todo_file} with {len(todos)} TODOs")

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
