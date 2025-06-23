# gh-utils Hybrid Testing Framework 🧪

A comprehensive testing framework for validating all core functionalities of the gh-utils GitHub repository monitoring tool.

## Overview

The Hybrid Testing Framework uses **real GitHub repository operations** combined with **mocked AI responses** to provide authentic integration testing while maintaining fast, predictable results.

## Test Types

The framework validates 3 core gh-utils functionalities:

1. **🍴 Forks Analysis**: `./gh-utils.py forks ccusage`
   - Tests fork detection and analysis capabilities
   - Validates multi-branch fork comparison

2. **📰 News about Forks**: `./gh-utils.py news test-ccusage`
   - Tests news detection on a fork repository (treated as regular repo)
   - Validates branch analysis and state management

3. **📰 News about Regular Repository**: `./gh-utils.py news testing`
   - Tests standard news functionality on standalone repository
   - Validates commit detection and incremental state updates

## Quick Start

### Prerequisites

- GitHub CLI authenticated: `gh auth login`
- Python 3.7+
- Access to test repositories:
  - `https://github.com/Durafen/ccusage` (fork)
  - `https://github.com/Durafen/testing` (regular)

### Running Tests

```bash
# Run complete test suite with timeout (recommended)
timeout 110 python3 test_framework/main_test.py

# Run with debug output
timeout 110 python3 test_framework/main_test.py --debug

# Run with debug script and logging (recommended for debugging)
test_framework/run_debug.sh

# Run without saving JSON reports
timeout 110 python3 test_framework/main_test.py --no-save-reports

# Quick test run (no timeout needed for basic functionality)
python3 test_framework/main_test.py --help
```

## Architecture

### Framework Components

- **`main_test.py`**: Main test orchestrator and entry point
- **`test_runner.py`**: Core test execution engine with AI mocking
- **`test_scenarios.py`**: Test scenario definitions and step implementations
- **`github_operations.py`**: Real GitHub repository operations (clone, commit, push)
- **`ai_mocking.py`**: AI provider mocking (OpenAI API & Claude CLI)
- **`validation.py`**: Output and state validation utilities
- **`test_reporter.py`**: Comprehensive reporting with ✅/❌ indicators

### Test Workflow

Each test follows a **8-step validation cycle**:

0. 🧹 **Clear all repository states** → Reset tracking for all test repos
1. 📰 **Run detection to clear news** → Clean slate for fresh run
2. 🔨 **Create main branch commit** → Push real changes to GitHub
3. 📰 **Run detection command** → Test main branch news detection
4. 🌿 **Create feature branch commit** → Push to last non-main branch
5. 📰 **Run detection command** → Test branch news detection
6. 🔨🌿 **Create commits on both branches** → Test multi-branch scenario
7. 📰 **Run detection command** → Validate comprehensive detection

## Sample Output

The framework features **improved visual formatting** with cleaner phase separation and streamlined output:

```
🚀 gh-utils Hybrid Testing Framework
==================================================
🔍 Validating test environment...
✅ Environment validation passed




🍴 TEST PHASE 1: FORKS ANALYSIS
============================================================
🔧 Executing: python3 .../gh-utils.py forks ccusage
✅ Command completed in 53.54s
🔧 Executing: python3 .../gh-utils.py forks ccusage
[Fork analysis output displayed...]
✅ Command completed in 43.40s




📰 TEST PHASE 2: NEWS ABOUT FORKS
============================================================
🔧 Executing: python3 .../gh-utils.py news test-ccusage
✅ Command completed in 16.98s
🔧 Executing: python3 .../gh-utils.py news test-ccusage
[News analysis output displayed...]
✅ Command completed in 13.69s




📰 TEST PHASE 3: NEWS ABOUT REGULAR REPOSITORY
============================================================
🔧 Executing: python3 .../gh-utils.py news testing
✅ Command completed in 11.26s

🧪 GH-UTILS HYBRID TESTING FRAMEWORK REPORT
================================================================================
📅 Session: 2025-06-23T12:34:56.789123
⏱️  Duration: 45.67 seconds

📊 OVERALL RESULTS
----------------------------------------
✅ Success Rate: 85.7%
🎯 Scenarios: 6/7 passed
📋 Steps: 24/28 passed

⚡ PERFORMANCE METRICS
----------------------------------------
⏱️  Average scenario time: 6.52s
🕐 Total execution time: 45.67s

🧪 TEST TYPE BREAKDOWN
----------------------------------------
✅ Forks Analysis
   Scenarios: 1/1 (100.0%)
   Avg Time: 8.34s

✅ News About Forks
   Scenarios: 2/3 (66.7%)
   Avg Time: 5.23s

✅ News About Regular
   Scenarios: 3/3 (100.0%)
   Avg Time: 6.12s
```

## Key Features

- **🔗 Real GitHub Integration**: Uses actual repositories with real commits
- **⚡ Fast AI Responses**: Mocked AI providers eliminate API delays and costs
- **📊 Comprehensive Reporting**: Detailed reports with success rates and timing
- **🔍 Deep Validation**: Tests command success, output patterns, state updates, and performance
- **🧹 Automatic Cleanup**: Cleans up temporary files and test artifacts
- **🛡️ Error Recovery**: Continues testing even if individual scenarios fail

## Hybrid Approach Benefits

| Aspect | Real GitHub | Mocked AI | Result |
|--------|-------------|-----------|---------|
| **Repository Operations** | ✅ Authentic | - | Real integration testing |
| **AI Processing** | - | ✅ Fast & Predictable | No API costs or delays |
| **State Management** | ✅ Real files | - | Validates actual state logic |
| **GitHub API** | ✅ Live calls | - | Tests rate limiting & auth |

## Troubleshooting

### Common Issues

**"GitHub CLI not authenticated"**
```bash
gh auth login
gh auth status  # Verify authentication
```

**"Repository not found"**
- Ensure you have access to the test repositories
- Check your GitHub permissions

**"Command timed out"**
- Check your network connection
- Verify GitHub API is accessible

**Import errors**
```bash
# Ensure you're running from the project root
cd /path/to/gh-utils
python3 test_framework/main_test.py
```

### Debug Mode

Enable debug mode for detailed output:
```bash
python3 test_framework/main_test.py --debug

# Or use the debug script with logging (creates test_framework.log)
test_framework/run_debug.sh
```

### Debug Script and Logging

The `run_debug.sh` bash script provides enhanced debugging with automatic logging:

**Script Features:**
- **Auto-navigation**: Changes to project root from script directory
- **Clean logging**: Removes old `test_framework.log` before each run
- **Live output**: Shows test progress in terminal via `tee`
- **Complete capture**: Saves all stdout/stderr to `test_framework.log`
- **Unbuffered output**: Uses `python3 -u` for real-time display

**Generated Files:**
- **`test_framework.log`**: Complete test execution log with all debug output
- **`success.md`**: Success tracking log created by test framework (when tests pass)

Debug mode shows:
- GitHub operations (clone, commit, push)
- AI mocking activity
- Validation results
- Performance metrics
- Error details

The `run_debug.sh` script automatically saves all output to `test_framework.log` for post-run analysis, while `success.md` tracks successful test completions.

## Development

### Git Worktree Architecture

The test framework uses a **git worktree + symlink setup** for cross-branch access:

**Structure:**
```
/github-utils/                    # Main project (any branch)
├── test_framework -> ../github-utils-tests/test_framework/  # Symlink
└── ...

/github-utils-tests/              # Worktree (test_framework branch)
├── .gitignore
└── test_framework/               # Test framework source code
    ├── main_test.py
    ├── test_runner.py
    └── ...
```

**Development Workflow:**
```bash
# Run tests from any branch in main project
timeout 110 python3 test_framework/main_test.py --debug

# Commit test framework changes from main project directory
git -C ../github-utils-tests add test_framework/
git -C ../github-utils-tests commit -m "test: improve validation and framework components"
# Note: DO NOT push test framework changes to remote

# Alternative: Navigate to worktree directory
cd ../github-utils-tests
git add test_framework/ && git commit -m "test: improve validation"
# Note: DO NOT push test framework changes to remote
cd ../github-utils  # Back to main development
```

**Benefits:**
- ✅ **Universal Access**: Test framework available from any branch
- ✅ **Correct Commits**: Test changes automatically go to `test_framework` branch
- ✅ **Live Updates**: Changes immediately visible in main project
- ✅ **Clean Separation**: No mixing of main app and test code

### Adding New Test Scenarios

1. **Define scenario** in `test_scenarios.py`
2. **Add validation logic** in `validation.py`
3. **Update AI responses** in `ai_mocking.py` if needed
4. **Test scenario** individually before integration

### Extending AI Mocking

Add new mock responses in `ai_mocking.py`:
```python
def _create_custom_response(self) -> str:
    return "✅ Custom AI analysis complete"

# Add to mock_responses dictionary
self.mock_responses['custom_scenario'] = self._create_custom_response()
```

## Performance

- **Average test suite runtime**: 45-60 seconds
- **Individual scenario time**: 5-10 seconds
- **GitHub operations**: 2-5 seconds per commit
- **AI mocking**: < 0.1 seconds per call

## Security

- **No API keys required**: AI responses are mocked
- **Read-only testing**: Only creates test commits, no destructive operations
- **Isolated test data**: Uses dedicated test repositories
- **Cleanup guaranteed**: Removes temporary files even on failures

---

**Ready to test?** Run `python3 test_framework/main_test.py --debug` to get started! 🚀