import os
import re
import datetime
import glob

# ------------------- Configuration Variables -------------------

# Static input variables
FULL_CLASS_NAME = 'com.example.demo.testing.parentpackage.ParentOne'  # Fully qualified class name
PROJECT_ROOT = r'D:\Applications\Test\spring\demo'                    # Root directory of the Java project
OUTPUT_DIR = r'D:\out\java'                                           # Directory to store the output file
SOURCE_DIR = os.path.join(PROJECT_ROOT, 'src', 'main', 'java')        # Source directory in Maven project

# ------------------- Helper Functions -------------------

def get_current_timestamp():
    """Returns the current timestamp in the format YYYYMMDDHHMMSS."""
    return datetime.datetime.now().strftime('%Y%m%d%H%M%S')

def remove_previous_outputs(class_name, output_dir):
    """Removes previous output files matching the class name with any timestamp."""
    pattern = os.path.join(output_dir, f"{class_name}-*.java")
    files = glob.glob(pattern)
    for file in files:
        try:
            os.remove(file)
            print(f"Removed existing output file: {file}")
        except OSError as e:
            print(f"Error removing file {file}: {e}")

def ensure_output_directory(output_dir):
    """Ensures that the output directory exists."""
    if not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir)
            print(f"Created output directory: {output_dir}")
        except OSError as e:
            print(f"Error creating directory {output_dir}: {e}")

# ------------------- Java File Processing -------------------

def parse_java_file(file_path):
    """
    Parse the Java file to extract the package name, import statements, class name, and class code.
    """
    package_pattern = re.compile(r'^\s*package\s+([\w\.]+);', re.MULTILINE)
    import_pattern = re.compile(r'^\s*import\s+([\w\.]+);', re.MULTILINE)
    class_pattern = re.compile(r'^\s*public\s+class\s+(\w+)', re.MULTILINE)
    class_code_pattern = re.compile(r'(public\s+class\s+\w+[\s\S]*?)(?=public\s+class|\Z)', re.MULTILINE)

    package_name = None
    imports = []
    class_name = None
    class_code = ""

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract package name
        package_match = package_pattern.search(content)
        if package_match:
            package_name = package_match.group(1)

        # Extract import statements
        imports = import_pattern.findall(content)

        # Extract class name
        class_match = class_pattern.search(content)
        if class_match:
            class_name = class_match.group(1)

        # Extract class code
        class_codes = class_code_pattern.findall(content)
        if class_codes:
            # Assuming the first match is the primary class
            class_code = class_codes[0]
    except (IOError, UnicodeDecodeError) as e:
        print(f"Error reading {file_path}: {e}")

    return package_name, imports, class_name, class_code

def is_project_import(import_statement, source_dir):
    """
    Determine if the import statement is part of the project by checking if the corresponding class file exists.
    """
    class_path = import_statement.replace('.', os.sep) + '.java'
    full_path = os.path.join(source_dir, class_path)
    return os.path.isfile(full_path)

def collect_classes(full_class_name, source_dir, collected=None):
    """
    Recursively collect class definitions starting from the given fully qualified class name.
    """
    if collected is None:
        collected = {}

    if full_class_name in collected:
        return collected  # Already collected

    # Convert the fully qualified class name to file path
    class_path = full_class_name.replace('.', os.sep) + '.java'
    file_path = os.path.join(source_dir, class_path)

    if not os.path.isfile(file_path):
        print(f"Warning: Class '{full_class_name}' not found at '{file_path}'.")
        return collected

    # Parse the Java file
    package_name, imports, class_name, class_code = parse_java_file(file_path)

    if class_name != full_class_name.split('.')[-1]:
        print(f"Warning: Mismatch in class name for '{full_class_name}' in file '{file_path}'. Expected '{full_class_name.split('.')[-1]}', found '{class_name}'.")
        return collected

    # Add the class to collected
    collected[full_class_name] = class_code

    # Process imports in the order they appear
    for imp in imports:
        # Skip static imports and java.* or javax.* imports (external libraries)
        if imp.startswith("static ") or imp.startswith("java.") or imp.startswith("javax."):
            continue
        # Check if the import is part of the project
        if is_project_import(imp, source_dir):
            # Recursively collect the imported class
            collect_classes(imp, source_dir, collected)

    return collected

# ------------------- Writing to File and Console -------------------

def write_to_file_and_console(collected_classes, output_path, parent_class_name):
    """
    Write all collected class definitions to the output file and print to console without timestamps.
    """
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            # Header
            header = f"------------<{parent_class_name}.class>----------"
            print(header)
            f.write(header + '\n')

            # Parent Class
            if parent_class_name in collected_classes:
                parent_header = "// Parent class"
                print(parent_header)
                f.write(parent_header + '\n')
                
                parent_code = collected_classes[parent_class_name].strip().split('\n')
                for line in parent_code:
                    print(line)
                    f.write(line + '\n')
            else:
                warning_message = f"Warning: Parent class '{parent_class_name}' not found in collected classes."
                print(warning_message)
                f.write(warning_message + '\n')

            # Imported Classes
            imported_classes = {k: v for k, v in collected_classes.items() if k != parent_class_name}
            if imported_classes:
                imported_header = "// Imported classes"
                print(imported_header)
                f.write(imported_header + '\n')
                
                for imp_class, imp_code in imported_classes.items():
                    print(imp_code)
                    f.write(imp_code + '\n')
                    print()  # Add a blank line between classes
                    f.write('\n')
            else:
                no_imports_message = "// No imported classes found."
                print(no_imports_message)
                f.write(no_imports_message + '\n')

            # Footer
            footer = "----------------------------------------"
            print(footer)
            f.write(footer + '\n')

        print(f"All classes have been written to '{output_path}'.")
    except IOError as e:
        print(f"Error writing to file {output_path}: {e}")

# ------------------- Main Execution -------------------

def main():
    # Parse the fully qualified class name
    try:
        package_name, class_name = FULL_CLASS_NAME.rsplit('.', 1)
    except ValueError:
        print("Error: FULL_CLASS_NAME must include the package path (e.g., com.example.ParentOne).")
        return

    # Ensure the output directory exists
    ensure_output_directory(OUTPUT_DIR)

    # Remove previous output files with the same class name
    remove_previous_outputs(class_name, OUTPUT_DIR)

    # Generate the output file name with timestamp
    timestamp = get_current_timestamp()
    output_file_name = f"{class_name}-{timestamp}.java"
    output_path = os.path.join(OUTPUT_DIR, output_file_name)

    # Collect classes starting from the parent class
    collected = collect_classes(FULL_CLASS_NAME, SOURCE_DIR)

    if not collected:
        print("No classes were collected. Please check the class name and project root directory.")
        return

    # Write the collected classes to the output file and print to console
    write_to_file_and_console(collected, output_path, FULL_CLASS_NAME)

if __name__ == "__main__":
    main()
