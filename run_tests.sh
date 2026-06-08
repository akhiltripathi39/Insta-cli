#!/usr/bin/env bash
# Test runner for Instagram CLI E2E test suite

# Exit on error
set -e

# Change directory to project root
cd "$(dirname "$0")"

# Execute the test suite using virtual environment's python
echo "======================================================================"
echo "Running Instagram CLI E2E Test Suite (49 test cases, Tiers 1-4)..."
echo "======================================================================"
./venv/bin/python3 -m unittest tests/test_suite.py -v
echo "======================================================================"
echo "All E2E tests completed successfully!"
echo "======================================================================"
