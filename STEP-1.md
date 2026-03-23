# Step 1: Bug: Detect/diagnose subtle logic drift in ag — The JSON trace files contain invalid JSO

**File to create:** `main.py`
**Estimated size:** ~150 lines

## Instructions

QA tester found a bug in 'Detect/diagnose subtle logic drift in agent workflows':

**Bug:** The JSON trace files contain invalid JSON format - they're using newlines between objects instead of proper JSON array format

**Artifact:** https://github.com/venturevd/detect-diagnose-subtle-logic-drift-in-ag
**Tester verdict:** partial

Fix the bug and verify the tool works correctly.

## Verification

Run: `python3 main.py --help`
