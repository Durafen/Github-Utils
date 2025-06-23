#!/bin/bash

# Get script directory and change to project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

# Clean up old log
rm -f test_framework.log

# Parse command line arguments and pass them through
echo "🤖 Starting test with debug logging..."
python3 -u test_framework/main_test.py "$@" 2>&1 | tee test_framework.log

echo "📋 Log saved to test_framework.log"