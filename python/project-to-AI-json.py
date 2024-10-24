import os
import shutil
import json
import fnmatch
from datetime import datetime
import re
import chardet
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

# ---------------------------- Configuration Section ---------------------------- #

# Define your configuration parameters here
CONFIG = {
    "source_folders": {
        # "grc-saas-events-broker": "D:\supports\Dhanush\code\temp\2024-10-11\grc-saas-events-broker"
          "react-app": "D:\Applications\pratice\ReactJs\my-app\src"
        
    },
    "destination_folder": "D:/temp/destFolder",
    "omit_files": [
        "package-lock*", "README*", ".gitignore", ".*", "Docker*", "gradle*",
        "settings*", "*.sh", "*.xml", "*.config", "*.options", "*.md"
    ],
    "omit_folders": [
        ".*", ".idea", "target", "node_modules", ".git*", ".cra", ".vscode",
        "helm", "gradle", "test", "build", "bin"
    ],
    "max_files_per_json": 100,
    "max_json_size_mb": 10,
    "logging_file": "file_processor.log",
    "error_log_file": "error_log.txt"
}

# ---------------------------- End of Configuration ---------------------------- #

# Configure logging
logging.basicConfig(
    filename=CONFIG["logging_file"],
    filemode='a',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def generate_tree_structure(rootdir, prefix=""):
    """
    Generate a tree-like structure string for the directory.
    """
    tree_structure = ""
    try:
        contents = os.listdir(rootdir)
    except PermissionError as e:
        logging.error(f"PermissionError accessing {rootdir}: {e}")
        return tree_structure
    except Exception as e:
        logging.error(f"Error accessing {rootdir}: {e}")
        return tree_structure

    contents.sort()
    pointers = ['├── '] * (len(contents) - 1) + ['└── ']

    for pointer, content in zip(pointers, contents):
        path = os.path.join(rootdir, content)
        if os.path.isdir(path):
            tree_structure += f"{prefix}{pointer}{content}/\n"
            extension = "│   " if pointer == '├── ' else "    "
            tree_structure += generate_tree_structure(path, prefix + extension)
        else:
            tree_structure += f"{prefix}{pointer}{content}\n"
    return tree_structure

def should_omit(item, patterns):
    """
    Check if the file or directory matches any of the omit patterns.
    """
    for pattern in patterns:
        if fnmatch.fnmatch(item, pattern):
            return True
    return False

def clear_destination_folder(destination_folder):
    """
    Clear all contents of the destination folder.
    """
    if os.path.exists(destination_folder):
        try:
            shutil.rmtree(destination_folder)
            logging.info(f"Cleared destination folder: {destination_folder}")
        except Exception as e:
            logging.error(f"Failed to clear destination folder {destination_folder}: {e}")
            raise e
    try:
        os.makedirs(destination_folder, exist_ok=True)
        logging.info(f"Created destination folder: {destination_folder}")
    except Exception as e:
        logging.error(f"Failed to create destination folder {destination_folder}: {e}")
        raise e

def ensure_directory_exists(file_path):
    """
    Ensure that the directory for the given file path exists.
    """
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        try:
            os.makedirs(directory, exist_ok=True)
            logging.info(f"Created directory: {directory}")
        except Exception as e:
            logging.error(f"Failed to create directory {directory}: {e}")
            raise e

def is_binary_file(file_path):
    """
    Check if a file is a binary file based on its extension.
    """
    binary_extensions = [
        '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico', '.exe',
        '.dll', '.zip', '.tar', '.gz', '.pdf', '.bin', '.dat'
    ]
    _, ext = os.path.splitext(file_path)
    return ext.lower() in binary_extensions

def read_file_content(file_path):
    """
    Read file content with encoding detection.
    """
    try:
        with open(file_path, 'rb') as f:
            raw_data = f.read()
        result = chardet.detect(raw_data)
        encoding = result['encoding'] if result['encoding'] else 'utf-8'
        return raw_data.decode(encoding)
    except Exception as e:
        logging.error(f"Failed to read {file_path}: {e}")
        return ""

def clean_code(content):
    """
    Clean the code by removing excessive whitespace but preserving comments and docstrings.
    """
    # Remove excessive whitespace
    content = re.sub(r'\n\s*\n', '\n', content)
    return content.strip()

def generate_file_summary(content, language):
    """
    Generate a brief summary of the file content based on the programming language.
    """
    if language == 'python':
        # Extract module docstring
        match = re.match(r'"""(.*?)"""', content, re.DOTALL)
        if not match:
            match = re.match(r"'''(.*?)'''", content, re.DOTALL)
        if match:
            return match.group(1).strip()
    elif language in ['java', 'c#', 'c++', 'javascript', 'typescript']:
        # Extract class or file-level comments
        match = re.search(r'//\s*(.*)', content)
        if match:
            return match.group(1).strip()
    # Add more languages as needed
    return "No summary available."

def get_language(file_extension):
    """
    Determine the programming language based on the file extension.
    """
    language_map = {
        '.py': 'python',
        '.java': 'java',
        '.cs': 'c#',
        '.cpp': 'c++',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.rb': 'ruby',
        '.go': 'go',
        '.php': 'php',
        '.swift': 'swift',
        '.kt': 'kotlin',
        '.rs': 'rust',
        # Add more mappings as needed
    }
    return language_map.get(file_extension.lower(), 'unknown')

def process_file(source_file_path, destination_file_path, language, source_folder):
    """
    Process a single file: copy and generate log data.
    """
    try:
        if is_binary_file(source_file_path):
            shutil.copy2(source_file_path, destination_file_path)
            logging.info(f"Copied binary file: {source_file_path} to {destination_file_path}")
            return {
                "filename": os.path.basename(source_file_path),
                "relative_path": os.path.relpath(os.path.dirname(source_file_path), source_folder),
                "summary": "Binary file",
                "content": ""
            }
        else:
            shutil.copy2(source_file_path, destination_file_path)
            logging.info(f"Copied text file: {source_file_path} to {destination_file_path}")
            content = read_file_content(source_file_path)
            if not content:
                return {
                    "filename": os.path.basename(source_file_path),
                    "relative_path": os.path.relpath(os.path.dirname(source_file_path), source_folder),
                    "summary": "Failed to read content",
                    "content": ""
                }
            file_summary = generate_file_summary(content, language)
            cleaned_content = clean_code(content)
            return {
                "filename": os.path.basename(source_file_path),
                "relative_path": os.path.relpath(os.path.dirname(source_file_path), source_folder),
                "summary": file_summary,
                "content": cleaned_content
            }
    except Exception as e:
        logging.error(f"Error processing {source_file_path}: {e}")
        return {"error": f"Error processing {source_file_path}: {e}"}

def split_log_data(log_data, max_files_per_json=100):
    """
    Split log data into multiple JSON files with a maximum number of files each.
    """
    split_logs = []
    current_split = {"app_name": log_data["app_name"], "files": []}
    for file in log_data["files"]:
        if len(current_split["files"]) >= max_files_per_json:
            split_logs.append(current_split)
            current_split = {"app_name": log_data["app_name"], "files": []}
        current_split["files"].append(file)
    if current_split["files"]:
        split_logs.append(current_split)
    return split_logs

def check_json_size(file_path, max_size_mb=10):
    """
    Check if the JSON file exceeds the maximum allowed size.
    """
    try:
        size = os.path.getsize(file_path) / (1024 * 1024)  # Size in MB
        return size > max_size_mb
    except Exception as e:
        logging.error(f"Failed to get size for {file_path}: {e}")
        return False

def copy_all_files_and_log(source_folders, destination_folder, omit_files=None, omit_folders=None, max_files_per_json=100, max_json_size_mb=10):
    """
    Copies all files from the source folders to the respective app folders in the destination folder.
    Also logs the details of the copied files and generates a project structure file.

    Parameters:
    - source_folders (dict): A dictionary where keys are app names and values are source paths.
    - destination_folder (str): The path where files should be copied.
    - omit_files (list, optional): A list of file patterns to omit during copying.
    - omit_folders (list, optional): A list of folder patterns to omit during copying.
    - max_files_per_json (int): Maximum number of files per JSON log file.
    - max_json_size_mb (int): Maximum size of each JSON log file in megabytes.
    """

    # Normalize destination folder path
    destination_folder = os.path.normpath(destination_folder)
    clear_destination_folder(destination_folder)

    if omit_files is None:
        omit_files = []
    if omit_folders is None:
        omit_folders = []

    # Common files to omit
    omit_files += ['desktop.ini', 'Thumbs.db']

    error_log = []

    for app_name, source_folder in source_folders.items():
        # Normalize source folder path
        source_folder = os.path.normpath(source_folder)
        try:
            if not os.path.exists(source_folder):
                raise FileNotFoundError(f"Source folder {source_folder} does not exist.")

            app_destination_folder = os.path.join(destination_folder, app_name)
            ensure_directory_exists(app_destination_folder)

            log_data = {"app_name": app_name, "files": []}
            log_data_without_paths = {"app_name": app_name, "files": []}

            with ThreadPoolExecutor(max_workers=10) as executor:
                future_to_file = {}
                for root, dirs, files in os.walk(source_folder):
                    # Normalize root path
                    root = os.path.normpath(root)
                    dirs[:] = [d for d in dirs if not should_omit(d, omit_folders)]

                    for file in files:
                        if should_omit(file, omit_files):
                            continue

                        source_file_path = os.path.join(root, file)
                        # Normalize source file path
                        source_file_path = os.path.normpath(source_file_path)
                        relative_path = os.path.relpath(root, source_folder)
                        app_dest_folder = os.path.join(destination_folder, app_name, relative_path)
                        app_dest_folder = os.path.normpath(app_dest_folder)
                        destination_file_path = os.path.join(app_dest_folder, file)
                        destination_file_path = os.path.normpath(destination_file_path)
                        ensure_directory_exists(destination_file_path)

                        _, ext = os.path.splitext(file)
                        language = get_language(ext)

                        future = executor.submit(
                            process_file,
                            source_file_path,
                            destination_file_path,
                            language,
                            source_folder
                        )
                        future_to_file[future] = source_file_path

                for future in as_completed(future_to_file):
                    result = future.result()
                    if result:
                        if 'error' in result:
                            error_log.append(result['error'])
                        else:
                            log_data["files"].append(result)
                            log_data_without_paths["files"].append({
                                "filename": result["filename"],
                                "summary": result["summary"],
                                "content": result["content"]
                            })

            # Split log data into smaller chunks if necessary
            split_logs = split_log_data(log_data, max_files_per_json)
            split_logs_without_paths = split_log_data(log_data_without_paths, max_files_per_json)

            for idx, split_log in enumerate(split_logs):
                timestamp = datetime.now().strftime('%Y%m%d')
                log_file = f"copy_log_{timestamp}-{app_name}_part{idx+1}.json"
                log_file_path = os.path.join(destination_folder, log_file)
                try:
                    with open(log_file_path, 'w', encoding='utf-8') as log_f:
                        json.dump(split_log, log_f, indent=4)
                    logging.info(f"Generated JSON log file: {log_file_path}")
                except Exception as e:
                    logging.error(f"Failed to write JSON log file {log_file_path}: {e}")
                    error_log.append(f"Failed to write JSON log file {log_file_path}: {e}")
                    continue

                if check_json_size(log_file_path, max_json_size_mb):
                    logging.warning(f"JSON file {log_file_path} exceeds the size limit of {max_json_size_mb} MB.")

            for idx, split_log in enumerate(split_logs_without_paths):
                timestamp = datetime.now().strftime('%Y%m%d')
                log_file = f"copy_log_no_paths_{timestamp}-{app_name}_part{idx+1}.json"
                log_file_path = os.path.join(destination_folder, log_file)
                try:
                    with open(log_file_path, 'w', encoding='utf-8') as log_f:
                        json.dump(split_log, log_f, indent=4)
                    logging.info(f"Generated JSON log file without paths: {log_file_path}")
                except Exception as e:
                    logging.error(f"Failed to write JSON log file {log_file_path}: {e}")
                    error_log.append(f"Failed to write JSON log file {log_file_path}: {e}")
                    continue

                if check_json_size(log_file_path, max_json_size_mb):
                    logging.warning(f"JSON file {log_file_path} exceeds the size limit of {max_json_size_mb} MB.")

            # Generate and save project structure
            project_structure = generate_tree_structure(source_folder)
            project_structure_file_path = os.path.join(destination_folder, f"project_structure_{app_name}.txt")
            try:
                with open(project_structure_file_path, 'w', encoding='utf-8') as proj_struct_file:
                    proj_struct_file.write(f"{app_name} Project Structure:\n\n")
                    proj_struct_file.write(project_structure)
                logging.info(f"Saved project structure to: {project_structure_file_path}")
            except Exception as e:
                logging.error(f"Failed to write project structure file {project_structure_file_path}: {e}")
                error_log.append(f"Failed to write project structure file {project_structure_file_path}: {e}")

        except Exception as e:
            error_message = f"Error during processing of {app_name}: {e}. No files or logs created."
            error_log.append(error_message)
            logging.error(error_message)

    if error_log:
        error_log_path = os.path.join(destination_folder, CONFIG["error_log_file"])
        try:
            with open(error_log_path, 'w', encoding='utf-8') as error_log_file:
                error_log_file.write("\n".join(error_log))
            logging.info(f"Errors were encountered during execution. Check '{error_log_path}' for details.")
            print(f"Errors were encountered during execution. Check '{error_log_path}' for details.")
        except Exception as e:
            logging.error(f"Failed to write error log file {error_log_path}: {e}")
            print(f"Errors were encountered during execution, but failed to write error log file '{error_log_path}'. Check '{CONFIG['logging_file']}' for details.")
    else:
        print("Processing completed without any errors.")
        logging.info("Processing completed without any errors.")

def main():
    """
    Main function to execute the file processing.
    """
    try:
        # Normalize source folder paths
        source_folders = {app: os.path.normpath(path) for app, path in CONFIG["source_folders"].items()}
        destination_folder = os.path.normpath(CONFIG["destination_folder"])
        omit_files = CONFIG["omit_files"]
        omit_folders = CONFIG["omit_folders"]
        max_files_per_json = CONFIG["max_files_per_json"]
        max_json_size_mb = CONFIG["max_json_size_mb"]

        copy_all_files_and_log(
            source_folders=source_folders,
            destination_folder=destination_folder,
            omit_files=omit_files,
            omit_folders=omit_folders,
            max_files_per_json=max_files_per_json,
            max_json_size_mb=max_json_size_mb
        )
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
