import os
import shutil
import json
import fnmatch
from datetime import datetime
import re

def generate_tree_structure(rootdir, prefix=""):
    """Generate a tree-like structure string for the directory."""
    tree_structure = ""
    contents = os.listdir(rootdir)
    contents.sort()
    pointers = ['├── '] * (len(contents) - 1) + ['└── ']
    
    for pointer, content in zip(pointers, contents):
        path = os.path.join(rootdir, content)
        if os.path.isdir(path):
            tree_structure += f"{prefix}{pointer}{content}/\n"
            tree_structure += generate_tree_structure(path, prefix + "│   ")
        else:
            tree_structure += f"{prefix}{pointer}{content}\n"
    return tree_structure

def should_omit(item, patterns):
    """Check if the file or directory matches any of the omit patterns."""
    for pattern in patterns:
        if fnmatch.fnmatch(item, pattern):
            return True
    return False

def clear_destination_folder(destination_folder):
    """Clear all contents of the destination folder."""
    if os.path.exists(destination_folder):
        shutil.rmtree(destination_folder)
    os.makedirs(destination_folder, exist_ok=True)

def ensure_directory_exists(file_path):
    """Ensure that the directory for the given file path exists."""
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)

def is_binary_file(file_path):
    """Check if a file is a binary file based on its extension."""
    binary_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico', '.exe', '.dll', '.zip', '.tar', '.gz', '.pdf']
    _, ext = os.path.splitext(file_path)
    return ext.lower() in binary_extensions

def remove_comments_and_spaces(content):
    """Remove non-essential comments and excessive whitespace from the content."""
    # Preserve essential comments and docstrings
    def replacer(match):
        s = match.group(0)
        if s.startswith('"') or s.startswith("'"):
            # This is a string or docstring, keep it
            return s
        else:
            # This is a comment, remove it
            return ''

    pattern = r"""
        # Single-line comments
        (#[^\n]*)
        |
        # Multi-line comments / docstrings
        (['"]{3}.*?['"]{3})
        |
        # Strings
        (['"].*?['"])
    """
    content = re.sub(pattern, replacer, content, flags=re.VERBOSE | re.DOTALL)
    # Remove excessive whitespace
    content = re.sub(r'\n\s*\n', '\n', content)
    return content.strip()

def generate_file_summary(content):
    """Generate a brief summary of the file content."""
    # Extract the first docstring or comment block as the summary
    summary_match = re.search(r'"""(.*?)"""', content, re.DOTALL)
    if not summary_match:
        summary_match = re.search(r"'''(.*?)'''", content, re.DOTALL)
    if summary_match:
        summary = summary_match.group(1).strip()
        return summary
    else:
        # Try to find a top-level comment
        summary_match = re.search(r'#\s*(.*)', content)
        if summary_match:
            summary = summary_match.group(1).strip()
            return summary
        else:
            return "No summary available."

def copy_all_files_flat_and_log(source_folders, destination_folder, omit_files=None, omit_folders=None):
    """
    Copies all files from the source folders to the respective app folders in the destination folder in a flat structure.
    Also logs the details of the copied files and generates a project structure file.

    Parameters:
    - source_folders (dict): A dictionary where keys are app names and values are source paths.
    - destination_folder (str): The path where files should be copied.
    - omit_files (list, optional): A list of file patterns to omit during copying.
    - omit_folders (list, optional): A list of folder patterns to omit during copying.
    """

    clear_destination_folder(destination_folder)

    destination_folder = os.path.abspath(destination_folder)

    if omit_files is None:
        omit_files = []
    if omit_folders is None:
        omit_folders = []

    omit_files += ['desktop.ini', 'Thumbs.db']

    error_log = []

    for app_name, source_folder in source_folders.items():
        try:
            if not os.path.exists(source_folder):
                raise FileNotFoundError(f"Source folder {source_folder} does not exist.")
            
            app_destination_folder = os.path.join(destination_folder, app_name)

            log_data = {"app_name": app_name, "files": []}
            log_data_without_paths = {"app_name": app_name, "files": []}

            for root, dirs, files in os.walk(source_folder):
                dirs[:] = [d for d in dirs if not should_omit(d, omit_folders)]

                for file in files:
                    if should_omit(file, omit_files):
                        continue

                    source_file_path = os.path.join(root, file)
                    
                    if not os.path.exists(source_file_path):
                        error_log.append(f"Warning: The file {source_file_path} does not exist and will be skipped.")
                        continue
                    
                    destination_file_path = os.path.join(app_destination_folder, file)
                    
                    ensure_directory_exists(destination_file_path)
                    
                    try:
                        if is_binary_file(source_file_path):
                            shutil.copy2(source_file_path, destination_file_path)
                        else:
                            shutil.copy2(source_file_path, destination_file_path)

                            with open(source_file_path, 'r', encoding='utf-8') as src_file:
                                content = src_file.read()
                            
                            file_summary = generate_file_summary(content)
                            cleaned_content = remove_comments_and_spaces(content)

                            # Calculate the relative source path
                            relative_source_path = os.path.relpath(source_file_path, source_folder)

                            log_data["files"].append({
                                "filename": file,
                                "source_path": relative_source_path,  # Use relative path
                                "summary": file_summary,
                                "content": cleaned_content
                            })

                            log_data_without_paths["files"].append({
                                "filename": file,
                                "summary": file_summary,
                                "content": cleaned_content
                            })
                    except Exception as e:
                        error_log.append(f"Error copying file {source_file_path} to {destination_file_path}: {e}")
                        continue

            log_file = f"copy_log_{datetime.now().strftime('%Y%m%d')}-{app_name}.json"
            log_file_without_paths = f"copy_log_no_paths_{datetime.now().strftime('%Y%m%d')}-{app_name}.json"

            log_file_path = os.path.join(destination_folder, log_file)
            log_file_without_paths_path = os.path.join(destination_folder, log_file_without_paths)

            with open(log_file_path, 'w', encoding='utf-8') as log:
                json.dump(log_data, log, indent=4)

            with open(log_file_without_paths_path, 'w', encoding='utf-8') as log_no_paths:
                json.dump(log_data_without_paths, log_no_paths, indent=4)

            project_structure = generate_tree_structure(source_folder)

            project_structure_file_path = os.path.join(destination_folder, f"project_structure_{app_name}.txt")
            with open(project_structure_file_path, 'w', encoding='utf-8') as proj_struct_file:
                proj_struct_file.write(f"{app_name} Project Structure:\n\n")
                proj_struct_file.write(project_structure)

            print(f"{app_name} project structure saved to: {project_structure_file_path}")

        except Exception as e:
            error_log.append(f"Error during finalization of {app_name}: {e}. No files or logs created.")

    if error_log:
        error_log_path = os.path.join(destination_folder, "error_log.txt")
        with open(error_log_path, 'w', encoding='utf-8') as error_log_file:
            error_log_file.write("\n".join(error_log))
        print(f"Errors were encountered during execution. Check '{error_log_path}' for details.")

# Example usage:
copy_all_files_flat_and_log(
    {
        'grc-saas-events-broker': r'D:\supports\Dhanush\code\temp\2024-09-06\grc-saas-events-broker',
    },
    r'D:\temp\destFolder',
    omit_files=[
        'package-lock*', 'README*', '.gitignore', '.*', 'Docker*', 'gradle*', 'settings*',
        '*.sh', '*.xml', '*.config', '*.options', '*.md',
    ],
    omit_folders=[
        '.*', '.idea', 'target', 'node_modules', '.git*', '.cra', '.vscode',
        'helm', 'gradle', 'test', 'build', 'bin'
    ]
)
