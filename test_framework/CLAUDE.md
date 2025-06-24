# gh-utils Hybrid Testing Framework 🧪

A comprehensive testing framework for validating all core functionalities of the gh-utils GitHub repository monitoring tool.

## Overview

The Hybrid Testing Framework uses **real GitHub repository operations** combined with **mocked AI responses** to provide authentic integration testing while maintaining fast, predictable results.

## Test Types

The framework validates 3 core gh-utils functionalities:

1. **🍴 Forks Analysis**: `./gh-utils.py forks ant-javacard`
   - Tests fork detection and analysis capabilities
   - Validates multi-branch fork comparison

2. **📰 News about Forks**: `./gh-utils.py news test-ant-javacard`
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
  - `https://github.com/Durafen/ant-javacard` (fork)
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

Each test follows a **10-step validation cycle**:

0. 🧹 **Clear all repository states** → Reset tracking for all test repos
1. 📰 **Run detection to clear news** → Clean slate for fresh run
2. 🔨 **Create main branch commit** → Push real changes to GitHub
3. 📰 **Run detection command** → Test main branch news detection
4. 🌿 **Create feature branch commit** → Push to non-main branch
5. 📰 **Run detection command** → Test branch news detection
6. 🔨🌿 **Create commits on both branches** → Test multi-branch scenario
7. 📰 **Run detection command** → Validate comprehensive detection
8. 🌟 **Create NEW branch + commit** → Test single new branch scenario
9. 📰 **Run detection command** → Validate NEW branch detection

**Enhanced NEW Branch Testing (Steps 8-9):**
- Creates timestamp-based unique branch names (`test-new-1234567890`)
- Tests dynamic branch discovery and analysis patterns
- Validates new branch appears in news/forks output correctly

## Sample Output

The framework features **improved visual formatting** with cleaner phase separation and streamlined output:

```
🚀 gh-utils Hybrid Testing Framework
==================================================
🔍 Validating test environment...
✅ Environment validation passed




🍴 TEST PHASE 1: FORKS ANALYSIS
============================================================
🔧 Executing: python3 .../gh-utils.py forks ant-javacard
✅ Command completed in 53.54s
🔧 Executing: python3 .../gh-utils.py forks ant-javacard
[Fork analysis output displayed...]
✅ Command completed in 43.40s




📰 TEST PHASE 2: NEWS ABOUT FORKS
============================================================
🔧 Executing: python3 .../gh-utils.py news test-ant-javacard
✅ Command completed in 16.98s
🔧 Executing: python3 .../gh-utils.py news test-ant-javacard
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
- **🚨 Enhanced Validation**: Detects broken AI generation and empty output sections
- **🧹 Automatic Cleanup**: Cleans up temporary files, test commits, and test branches
- **🌿 Dynamic Branch Management**: Creates and deletes test branches using pattern matching (`test-feature`, `test-new-*`)
- **⚙️ Configurable Cleanup**: Per-phase cleanup controlled by `delete_commits_after_phase` setting
- **🛡️ Error Recovery**: Continues testing even if individual scenarios fail
- **🚀 Real-time Output**: Elegant subprocess handling with live command output display

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

# Or use the debug script with logging (creates tests.log)
test_framework/run_debug.sh
```

### Debug Script and Logging

The `run_debug.sh` bash script provides enhanced debugging with automatic logging:

**Script Features:**
- **Auto-navigation**: Changes to project root from script directory
- **Clean logging**: Removes old `tests.log` before each run
- **Live output**: Shows test progress in terminal via `tee`
- **Complete capture**: Saves all stdout/stderr to `tests.log`
- **Unbuffered output**: Uses `python3 -u` for real-time display

**Generated Files:**
- **`tests.log`**: Complete test execution log with all debug output
- **`test_reports/test_report_YYYYMMDD_HHMMSS.json`**: Detailed JSON test reports with metrics
- **`success.md`**: Success tracking log created by test framework (when tests pass)

Debug mode shows:
- GitHub operations (clone, commit, push)
- AI mocking activity
- Validation results
- Performance metrics
- Error details

The `run_debug.sh` script automatically saves all output to `tests.log` for post-run analysis, while `success.md` tracks successful test completions.

### Enhanced Validation System

The framework now includes **advanced output validation** that detects broken main program functionality:

**🚨 Critical Validation Features:**
- **Content Density Checks**: Validates fork entries (🍴), branch trees (├─), AI bullet points (-), and cost tracking ($<0.001)
- **Section Completeness**: Detects empty sections with headers but no content
- **Smart Filtering**: Only validates non-first runs (first runs are baseline/hidden)
- **Failure Detection**: Shows `🚨 CRITICAL VALIDATION FAILURE!` when main gh-utils program has bugs

**What Gets Validated:**
- All `forks` commands except first run of each phase
- All `news` commands except first run of each phase
- Skip validation for `clear` commands (minimal output expected)

**Sample Validation Failure Output:**
```
🔧 Executing: python3 .../gh-utils.py forks ant-javacard
🚨 CRITICAL VALIDATION FAILURE!
   Content density validation failed, Section completeness validation failed
   This indicates the main gh-utils program has bugs!
❌ Command completed in 39.80s
⚠️  Validation issues: Content density validation failed, Section completeness validation failed
```

This ensures the test framework correctly identifies when the main program is broken, rather than falsely reporting success.

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

**🔍 Reading from Test Framework:**
```bash
# Read any test framework file (works from main project directory)
cat test_framework/main_test.py
cat test_framework/settings.txt
cat test_framework/CLAUDE.md

# Edit test framework files (symlink provides live access)
# Changes are immediately visible in both directories
```

**📝 Committing Test Framework Changes:**

**⚠️ CRITICAL: Due to symlink setup, git operations must be run from the symlinked directory or use git -C to target the worktree!**

```bash
# RECOMMENDED METHOD: Work from within the symlinked directory
cd test_framework/  # Navigate into the symlinked directory in main project
git status          # Shows status in test_framework branch (via symlink)
git add .           # Add all modified test framework files
git commit -m "test: improve validation and framework components"
git status          # Should show clean working tree on test_framework branch

# ALTERNATIVE: Use git -C to target the worktree (if symlink access unavailable)
git -C ../github-utils-tests add test_framework/
git -C ../github-utils-tests commit -m "test: improve validation and framework components" 
git -C ../github-utils-tests status  # Verify commit went to test_framework branch

# DON'T DO THIS: Never try to add symlinked files from main project directory
# git add test_framework/  # ❌ FAILS: "pathspec 'test_framework/file.py' is beyond a symbolic link"

# Verify commits are on correct branch
cd test_framework/ && git log --oneline -3  # Shows test framework commits
cd .. && git log --oneline -3               # Shows main app commits (different branch)
```

**🔍 Checking Worktree Status:**
```bash
# From main project directory
git worktree list                    # Shows both directories and their branches
ls -la | grep test_framework        # Confirms symlink setup: test_framework -> ../github-utils-tests/test_framework

# Check which branch you're on in each location
cd test_framework/ && git branch    # Should show * test_framework
cd .. && git branch                 # Shows main app branch (e.g., * updates)
```

**🌳 How the Git Worktree Works:**
- `test_framework/` in main project → **symlink** → `../github-utils-tests/test_framework/`
- Reading: Works directly through symlink from any branch
- Writing: Files update in both locations instantly (same inode)
- Committing: Must use `git -C ../github-utils-tests` or `cd` to worktree
- Branches: Main project commits go to current branch, worktree commits go to `test_framework` branch

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

## Recent Improvements (Last 10 Commits)

**Latest Enhancements:**
- **🌿 Fixed Branch Cleanup**: Dynamic pattern matching now properly deletes `test-feature` and `test-new-*` branches across all 3 phases
- **🔧 Repository Configuration**: Updated from ccusage to ant-javacard for better testing scenarios  
- **✅ Pattern Validation**: Improved validation with streamlined GitHub operations
- **🚨 Error Visibility**: Test framework errors now always visible regardless of debug mode
- **🆕 10-Step Validation**: Implemented comprehensive validation cycles with NEW branch creation
- **🔍 Repository Validation**: Added critical repository validation in step 1 of every phase
- **📚 Documentation**: Enhanced README with clear git worktree usage instructions
- **⚡ Real-time Output**: Elegant subprocess solution with live command output display
- **⏱️ Timeout Handling**: Improved timeout configuration and display settings
- **🧹 Configurable Cleanup**: Per-phase commit cleanup controlled by settings

## Cleanup System Architecture

The framework now features **two-tier cleanup** with comprehensive artifact management:

### **Phase-End Cleanup** (After each test phase)
- **Triggered by**: `delete_commits_after_phase = true` setting
- **Scope**: Test commits + test branches from all active repositories
- **Frequency**: After forks analysis, news about forks, and news regular repo phases

### **Final Cleanup** (At framework completion)  
- **Triggered by**: Framework shutdown
- **Scope**: Temporary directories, any remaining test artifacts
- **Frequency**: Once at the end of test execution

### **Dynamic Branch Detection**
```python
# Patterns used for test branch cleanup
test_branch_patterns = ['test-feature', 'test-new-']

# Matches branches like:
# - test-feature
# - test-new-1234567890  
# - test-new-1750729248
```

## Security

- **No API keys required**: AI responses are mocked
- **Read-only testing**: Only creates test commits, no destructive operations
- **Isolated test data**: Uses dedicated test repositories
- **Cleanup guaranteed**: Removes temporary files, commits, and branches even on failures

---

**Ready to test?** Run `python3 test_framework/main_test.py --debug` to get started! 🚀