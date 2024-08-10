import os
import shutil

def copy_all_files_flat(source_folder, destination_folder):
    # Normalize the paths for compatibility
    source_folder = os.path.abspath(source_folder)
    destination_folder = os.path.abspath(destination_folder)

    # Ensure the destination folder exists
    os.makedirs(destination_folder, exist_ok=True)

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
            except Exception as e:
                # Handle any errors during the copy process
                print(f"Failed to copy {source_file_path} to {destination_file_path}: {e}")

# Example usage:
copy_all_files_flat(
    r'D:\supports\assignment\sukumar-advaith\repo\Jiraboard_demo_test\Jiraboard_demo_test\src',
    r'D:\temp\destFolder'
)
