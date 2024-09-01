import os
import shutil
import json
import fnmatch  # Importing fnmatch for pattern matching
from datetime import datetime

def generate_tree_structure(rootdir, prefix=""):
    """Generate a tree-like structure string for the directory."""
    tree_structure = ""
    contents = os.listdir(rootdir)
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
        shutil.rmtree(destination_folder)  # Delete everything in the destination folder
    os.makedirs(destination_folder, exist_ok=True)  # Recreate the empty destination folder

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

def copy_all_files_flat_and_log(source_folders, destination_folder, omit_files=None, omit_folders=None):
    """
    Copies all files from the source folders to the respective app folders in the destination folder in a flat structure.
    Also logs the details of the copied files and generates a project structure file.

    Parameters:
    - source_folders (dict): A dictionary where keys are app names and values are source paths.
    - destination_folder (str): The path where files should be copied.
    - omit_files (list, optional): A list of file patterns to omit during copying.
      - Example patterns:
        - `'*.java'`: Omits all Java files.
        - `'README*'`: Omits all files starting with 'README'.
    - omit_folders (list, optional): A list of folder patterns to omit during copying.
      - Example patterns:
        - `'node_modules'`: Omits all folders named 'node_modules'.
        - `'.git*'`: Omits all folders starting with '.git'.
    """

    # Clear the destination folder before starting
    clear_destination_folder(destination_folder)

    # Normalize the destination path
    destination_folder = os.path.abspath(destination_folder)

    # Initialize omit arrays if not provided
    if omit_files is None:
        omit_files = []
    if omit_folders is None:
        omit_folders = []

    # Add patterns to omit system files like desktop.ini
    omit_files += ['desktop.ini', 'Thumbs.db']

    # Iterate through the source folders dictionary
    for app_name, source_folder in source_folders.items():
        try:
            # Attempt to process the source folder
            # If this block succeeds, it will proceed to create the destination folder and log files
            
            # Check access to the source folder and basic validity
            if not os.path.exists(source_folder):
                raise FileNotFoundError(f"Source folder {source_folder} does not exist.")
            
            # Create the app-specific destination folder
            app_destination_folder = os.path.join(destination_folder, app_name)

            # Initialize log data structures
            log_data = {"files": []}
            log_data_without_paths = {"files": []}

            # Walk through the source directory
            for root, dirs, files in os.walk(source_folder):
                # Skip folders that are in the omit list
                dirs[:] = [d for d in dirs if not should_omit(d, omit_folders)]

                for file in files:
                    # Check if the file should be omitted based on the patterns
                    if should_omit(file, omit_files):
                        continue

                    # Construct the full file path in the source directory
                    source_file_path = os.path.join(root, file)
                    
                    # Check if the file exists before trying to copy it
                    if not os.path.exists(source_file_path):
                        print(f"Warning: The file {source_file_path} does not exist and will be skipped.")
                        continue
                    
                    # Construct the destination file path (flat structure)
                    destination_file_path = os.path.join(app_destination_folder, file)
                    
                    # Ensure the destination directory exists
                    ensure_directory_exists(destination_file_path)
                    
                    try:
                        # Copy binary files directly without opening
                        if is_binary_file(source_file_path):
                            shutil.copy2(source_file_path, destination_file_path)
                        else:
                            # Copy the file to the destination folder
                            shutil.copy2(source_file_path, destination_file_path)
                            print(f"Copied: {source_file_path} to {destination_file_path}")

                            # Read the content of the file if it's not binary
                            with open(source_file_path, 'r', encoding='utf-8') as src_file:
                                content = src_file.read()

                            # Append the file info to the detailed log data
                            log_data["files"].append({
                                "filename": file,
                                "source_path": source_file_path,
                                "destination_path": destination_file_path,
                                "content": content
                            })

                            # Append the file info to the log data without paths
                            log_data_without_paths["files"].append({
                                "filename": file,
                                "content": content
                            })
                    except Exception as e:
                        print(f"Error copying file {source_file_path} to {destination_file_path}: {e}")
                        continue  # Skip this file but continue processing others

            # Generate the log file names with the current date and app name
            log_file = f"copy_log_{datetime.now().strftime('%Y%m%d')}-{app_name}.json"
            log_file_without_paths = f"copy_log_no_paths_{datetime.now().strftime('%Y%m%d')}-{app_name}.json"

            # Define paths for the log files
            log_file_path = os.path.join(destination_folder, log_file)
            log_file_without_paths_path = os.path.join(destination_folder, log_file_without_paths)

            # Write the detailed log data to the log file in JSON format
            with open(log_file_path, 'w', encoding='utf-8') as log:
                json.dump(log_data, log, indent=4)

            # Write the log data without paths to a separate JSON file
            with open(log_file_without_paths_path, 'w', encoding='utf-8') as log_no_paths:
                json.dump(log_data_without_paths, log_no_paths, indent=4)

            # Generate and store the project structure for the current app
            project_structure = generate_tree_structure(source_folder)

            # Write the project structure to the project structure file in tree format
            project_structure_file_path = os.path.join(destination_folder, f"project_structure_{app_name}.txt")
            with open(project_structure_file_path, 'w', encoding='utf-8') as proj_struct_file:
                proj_struct_file.write(f"{app_name} Project Structure:\n\n")
                proj_struct_file.write(project_structure)

            print(f"{app_name} project structure saved to: {project_structure_file_path}")

        except Exception as e:
            # Handle any errors encountered during the creation of the folder and logs
            print(f"Error during finalization of {app_name}: {e}. No files or logs created.")

# Example usage:
copy_all_files_flat_and_log(
    {
        r'grc-saas-events-broker': r'D:\supports\Dhanush\code\temp\2024-08-30\grc-saas-evnts-broker',
    },
    r'D:\temp\destFolder',
    omit_files=['package-lock*', 'README*','.gitignore','.*','Docker*', 'gradle*','settings*','*.sh','*.xml','*.config','*.options','*.md',],  # Patterns to omit files
    omit_folders=['.*','.idea','target','node_modules','.git*','.cra','.vscode','helm','gradle','test','build','bin']  # Patterns to omit folders
)
