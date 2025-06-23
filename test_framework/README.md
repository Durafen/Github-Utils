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
# Run complete test suite
python3 test_framework/main_test.py

# Run with debug output
python3 test_framework/main_test.py --debug

# Run without saving JSON reports
python3 test_framework/main_test.py --no-save-reports
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

Each test follows a **7-step validation cycle**:

1. ✅ **Clear repository state** → Reset tracking for fresh run
2. 🔨 **Create main branch commit** → Push real changes to GitHub
3. 📰 **Run detection command** → Test main branch news detection
4. 🌿 **Create feature branch commit** → Push to feature branch
5. 📰 **Run detection command** → Test branch news detection
6. 🔨🌿 **Create commits on both branches** → Test multi-branch scenario
7. 📰 **Run detection command** → Validate comprehensive detection

## Sample Output

```
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
```

Debug mode shows:
- GitHub operations (clone, commit, push)
- AI mocking activity
- Validation results
- Performance metrics
- Error details

## Development

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