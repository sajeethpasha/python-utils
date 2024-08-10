import os
import shutil

def copy_all_files_flat(source_folder, destination_folder):
    # Normalize the paths for compatibility
    source_folder = os.path.abspath(source_folder)
    destination_folder = os.path.abspath(destination_folder)

    # Create the destination directory if it doesn't exist
    os.makedirs(destination_folder, exist_ok=True)

    # Dictionary to keep track of filenames and their counts to handle duplicates
    filename_counts = {}

    # Walk through the source directory
    for root, dirs, files in os.walk(source_folder):
        for file in files:
            # Get the file extension and name without extension
            name, ext = os.path.splitext(file)
            
            # Initialize the new filename
            new_filename = file

            # Check if the filename already exists
            if file in filename_counts:
                # Increment the count
                filename_counts[file] += 1
                # Create a new filename with the count appended
                new_filename = f"{name}_{filename_counts[file]}{ext}"
            else:
                # First occurrence of the filename
                filename_counts[file] = 1
                # Check if the file already exists in the destination
                if os.path.exists(os.path.join(destination_folder, file)):
                    # If exists, start counting from 1
                    new_filename = f"{name}_1{ext}"
            
            # Construct the full file path in the source directory
            source_file_path = os.path.join(root, file)
            
            # Construct the full destination file path
            destination_file_path = os.path.join(destination_folder, new_filename)
            
            try:
                # Copy the file to the destination
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
