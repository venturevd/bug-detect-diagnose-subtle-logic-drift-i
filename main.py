#!/usr/bin/env python3
"""
Fix the bug in the JSON trace files that contain invalid JSON format.
The bug is that the files are using newlines between objects instead of proper JSON array format.
"""

import json
import os
import argparse

def fix_json_trace_file(file_path):
    """
    Fix a single JSON trace file by converting newline-separated objects into a proper JSON array.

    Args:
        file_path (str): Path to the JSON trace file
    """
    try:
        # Read the file content
        with open(file_path, 'r') as f:
            content = f.read()

        # Try to parse as newline-separated JSON objects
        try:
            # Split by newlines and parse each object
            objects = [json.loads(line) for line in content.strip().split('\n') if line.strip()]

            # Write back as proper JSON array
            with open(file_path, 'w') as f:
                json.dump(objects, f, indent=2)

            print(f"Fixed {file_path}")
            return True
        except json.JSONDecodeError as e:
            print(f"Error parsing {file_path}: {e}")
            return False
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def fix_json_trace_files_in_directory(directory):
    """
    Fix all JSON trace files in a directory.

    Args:
        directory (str): Directory containing JSON trace files
    """
    if not os.path.isdir(directory):
        print(f"Directory {directory} does not exist")
        return

    # Find all .json files in the directory
    json_files = [f for f in os.listdir(directory) if f.endswith('.json')]

    if not json_files:
        print(f"No JSON files found in {directory}")
        return

    # Process each file
    for json_file in json_files:
        file_path = os.path.join(directory, json_file)
        fix_json_trace_file(file_path)

def main():
    """
    Main function to parse arguments and fix JSON trace files.
    """
    parser = argparse.ArgumentParser(description='Fix JSON trace files with invalid format')
    parser.add_argument('directory', nargs='?', default='.', help='Directory containing JSON trace files (default: current directory)')

    args = parser.parse_args()

    # Fix JSON trace files in the specified directory
    fix_json_trace_files_in_directory(args.directory)

if __name__ == "__main__":
    main()