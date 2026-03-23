# JSON Trace File Fix Tool

## Description
This tool fixes JSON trace files that contain invalid JSON format. The bug is that the files are using newlines between objects instead of proper JSON array format.

## Usage
```bash
python3 main.py [directory]
```

- `directory`: Optional. Directory containing JSON trace files (default: current directory)
- `--help`: Show help message and exit

## Example
```bash
python3 main.py ./traces
```

This will fix all JSON files in the `./traces` directory.

## How It Works
1. The tool reads each JSON file in the specified directory
2. It attempts to parse the content as newline-separated JSON objects
3. If successful, it writes the objects back as a proper JSON array
4. If parsing fails, it reports the error and skips the file

## Requirements
- Python 3.6+
- No external dependencies (stdlib only)

## Verification
Run the following command to verify the tool works:

```bash
python3 main.py --help
```

This should display the help message.