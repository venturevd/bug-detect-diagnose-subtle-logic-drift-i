# Step 1: Create analyze command script

**File to create:** `main.py`
**Estimated size:** ~200 lines

## Instructions

Write a Python script that implements the analyze command with proper trace loading logic. The script should:
1. Load agent execution traces from a specified directory
2. Validate each trace before processing
3. Count and report both valid and skipped traces
4. Provide clear output about which traces were skipped and why
5. Include command-line arguments for input directory and output format

## Verification

Run: `python3 main.py --help`
