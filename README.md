# Bug: Detect/diagnose subtle logic drift in agent workflows — The drift analysis reports show 0 traces

## Description

This tool detects and diagnoses subtle logic drift in agent workflows. It collects agent execution traces, analyzes them for logic drift using statistical methods (Kolmogorov-Smirnov test), and generates comprehensive reports.

**Bug fixed:** The drift analysis reports now correctly show the number of traces loaded and generate reports based on actual data rather than default values, even when traces are in newline-separated JSON format.

## Features

- Loads agent execution traces from JSON files
- Handles both proper JSON arrays and newline-separated JSON objects
- Detects logic drift using statistical analysis
- Generates detailed text reports with drift analysis results
- Shows workflow distribution and drift detection per workflow type

## Requirements

- Python 3.6+
- numpy, scipy (installed via requirements.txt)

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python3 main.py [directory] [options]
```

### Arguments

- `directory`: Optional. Directory containing JSON trace files (default: current directory)
- `--output`: Optional. Output file for the analysis report (default: print to console)
- `--help`: Show help message and exit

### Example

```bash
# Analyze traces in current directory
python3 main.py .

# Analyze traces in specific directory and save report
python3 main.py ./traces --output analysis_report.txt
```

## How It Works

1. **Trace Loading**: The tool reads JSON files from the specified directory, handling both proper JSON arrays and newline-separated JSON objects.
2. **Drift Analysis**: For each workflow type, the tool compares execution metrics between batches using the Kolmogorov-Smirnov test.
3. **Report Generation**: A detailed report is generated showing:
   - Total traces analyzed
   - Workflow distribution
   - Drift detection results per workflow
   - Statistical analysis details

## Verification

Run the following command to verify the tool works:

```bash
python3 main.py --help
```

This should display the help message with usage instructions.