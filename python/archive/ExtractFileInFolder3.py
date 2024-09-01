import os
import shutil

def copy_all_files_flat_and_log(source_folder, destination_folder, log_file):
    # Normalize the paths for compatibility
    source_folder = os.path.abspath(source_folder)
    destination_folder = os.path.abspath(destination_folder)
    log_file_path = os.path.join(destination_folder, log_file)

    # Ensure the destination folder exists
    os.makedirs(destination_folder, exist_ok=True)

    # Open the log file to append all file contents
    with open(log_file_path, 'w') as log:
        # Walk through the source directory
        for root, dirs, files in os.walk(source_folder):
            for file in files:
                # Construct the full file path in the source directory
                source_file_path = os.path.join(root, file)
                
                # Construct the destination file path (flat structure)
                destination_file_path = os.path.join(destination_folder, file)
                
                try:
                    # Copy the file to the destination folder
                    shutil.copy2(source_file_path, destination_file_path)
                    print(f"Copied: {source_file_path} to {destination_file_path}")
                    
                    # Read the content of the file and write it to the log file
                    with open(source_file_path, 'r') as src_file:
                        content = src_file.read()
                        log.write(f"File: {file}\n")
                        log.write(content)
                        log.write("\n" + "-"*40 + "\n")  # Separator between files

                except Exception as e:
                    # Handle any errors during the copy process
                    print(f"Failed to copy {source_file_path} to {destination_file_path}: {e}")
                    log.write(f"Failed to copy {source_file_path}: {e}\n")



# Example usage:
copy_all_files_flat_and_log(
    r'D:\supports\assignment\sukumar-advaith\repo\Jiraboard_demo_test\Jiraboard_demo_test\src',
    r'D:\temp\destFolder',
    'jiraboard_demo_test-completecode.txt'
)
