#!/usr/bin/env python3
"""
Run a project's verification command and return a machine-readable status.

Usage:
  python3 verify_refactor.py --test-cmd "npm test"
  python3 verify_refactor.py --test-cmd "mvn test"

This script deliberately does not guess the project's test command.
The Agent must supply the repository's established verification command.
"""

import argparse
import subprocess
import sys

parser = argparse.ArgumentParser()
parser.add_argument("--test-cmd", required=True, help="Existing project test/verification command")
args = parser.parse_args()

print(f"[VERIFY] running: {args.test_cmd}")
result = subprocess.run(args.test_cmd, shell=True)
if result.returncode == 0:
    print("[VERIFY] PASS")
    sys.exit(0)

print(f"[VERIFY] FAIL (exit={result.returncode})")
sys.exit(result.returncode)
