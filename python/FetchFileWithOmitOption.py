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

def should_omit(file, patterns):
    """Check if the file matches any of the omit patterns."""
    for pattern in patterns:
        if fnmatch.fnmatch(file, pattern):
            return True
    return False

def copy_all_files_flat_and_log(source_folder, destination_folder, omit_files=None, omit_folders=None):
    """
    Copies all files from the source folder to the destination folder in a flat structure.
    Also logs the details of the copied files and generates a project structure file.

    Parameters:
    - source_folder (str): The path of the source directory.
    - destination_folder (str): The path where files should be copied.
    - omit_files (list, optional): A list of file patterns to omit during copying.
      - Examples of patterns:
        - `'Testing.java'`: Omits only the file named 'Testing.java'.
        - `'Testing*'`: Omits all files starting with 'Testing', e.g., 'Testing.java', 'TestingSample.txt'.
        - `'*.java'`: Omits all files ending with '.java', e.g., 'Example.java', 'AnotherTest.java'.
        - `'*'`: Omits all files (though this would omit everything, so use with caution).
    - omit_folders (list, optional): A list of folder names to omit during copying.
      - Example:
        - `['test', 'docs']`: Omits folders named 'test' and 'docs' and their contents.
    """

    # Generate the log file names with the current date in YYYYMMDD format
    log_file = f"copy_log_{datetime.now().strftime('%Y%m%d')}.json"
    reduced_log_file = f"reduced_copy_log_{datetime.now().strftime('%Y%m%d')}.json"
    project_structure_file = "project_structure.txt"
    
    # Normalize the paths for compatibility
    source_folder = os.path.abspath(source_folder)
    all_files_folder = os.path.join(destination_folder, 'all-files')
    log_file_path = os.path.join(destination_folder, log_file)
    reduced_log_file_path = os.path.join(destination_folder, reduced_log_file)
    project_structure_file_path = os.path.join(destination_folder, project_structure_file)

    # Ensure the destination folder and all-files folder exist, creating them if necessary
    if os.path.exists(all_files_folder):
        shutil.rmtree(all_files_folder)  # Delete existing folder and its contents
    os.makedirs(all_files_folder, exist_ok=True)

    # Initialize omit arrays if not provided
    if omit_files is None:
        omit_files = []
    if omit_folders is None:
        omit_folders = []

    # Initialize log data structures
    log_data = {"files": []}
    reduced_log_data = {"files": []}

    # Walk through the source directory
    for root, dirs, files in os.walk(source_folder):
        # Skip folders that are in the omit list
        dirs[:] = [d for d in dirs if os.path.relpath(os.path.join(root, d), source_folder) not in omit_folders]

        for file in files:
            # Check if the file should be omitted based on the patterns
            if should_omit(file, omit_files):
                continue

            # Construct the full file path in the source directory
            source_file_path = os.path.join(root, file)
            
            # Construct the destination file path (flat structure)
            destination_file_path = os.path.join(all_files_folder, file)
            
            try:
                # Copy the file to the destination folder
                shutil.copy2(source_file_path, destination_file_path)
                print(f"Copied: {source_file_path} to {destination_file_path}")
                
                # Read the content of the file
                with open(source_file_path, 'r', encoding='utf-8') as src_file:
                    content = src_file.read()
                
                # Append the file info to the detailed log data
                log_data["files"].append({
                    "filename": file,
                    "source_path": source_file_path,
                    "destination_path": destination_file_path,
                    "content": content
                })

                # Append the file info to the reduced log data (without content)
                reduced_log_data["files"].append({
                    "filename": file,
                    "source_path": source_file_path,
                    "destination_path": destination_file_path,
                })

            except Exception as e:
                # Handle any errors during the copy process
                print(f"Failed to copy {source_file_path} to {destination_file_path}: {e}")
                log_data["files"].append({
                    "filename": file,
                    "source_path": source_file_path,
                    "destination_path": destination_file_path,
                    "error": str(e)
                })
                reduced_log_data["files"].append({
                    "filename": file,
                    "source_path": source_file_path,
                    "destination_path": destination_file_path,
                    "error": str(e)
                })

    # Write the detailed log data to the log file in JSON format
    with open(log_file_path, 'w', encoding='utf-8') as log:
        json.dump(log_data, log, indent=4)

    # Write the reduced log data to the reduced-size log file in JSON format
    with open(reduced_log_file_path, 'w', encoding='utf-8') as reduced_log:
        json.dump(reduced_log_data, reduced_log, indent=4)

    # Generate and write the project structure to the project structure file in tree format
    project_structure = generate_tree_structure(source_folder)
    with open(project_structure_file_path, 'w', encoding='utf-8') as proj_struct_file:
        proj_struct_file.write("Project Structure:\n\n")
        proj_struct_file.write(project_structure)

    print(f"Project structure saved to: {project_structure_file_path}")

# Example usage:
copy_all_files_flat_and_log(
    r'D:\supports\assignment\sukumar-advaith\repo\Jiraboard_demo_test\Jiraboard_demo_test\src',
    r'D:\temp\destFolder',  # Log files and project structure file will be created in this folder, and files will be stored in 'all-files' subfolder
    omit_files=['Testing*', '*.java'],  # Patterns to omit: all files starting with 'Testing' and all Java files
    omit_folders=['test', 'docs']  # Folders to omit
)
