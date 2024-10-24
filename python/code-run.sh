#!/bin/bash

# Execute the Python script with arguments
python project_to_json.py \
    --source '{"grc-saas-events-broker": "D:/supports/Dhanush/code/temp/2024-09-06/grc-saas-events-broker"}' \
    --destination "D:/temp/destFolder" \
    --omit_files "package-lock*" "README*" ".gitignore" ".*" "Docker*" "gradle*" "settings*" "*.sh" "*.xml" "*.config" "*.options" "*.md" \
    --omit_folders ".*" ".idea" "target" "node_modules" ".git*" ".cra" ".vscode" "helm" "gradle" "test" "build" "bin" \
    --max_files_per_json 100 \
    --max_json_size_mb 10
