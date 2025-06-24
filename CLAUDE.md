# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**gh-utils** is a GitHub repository monitoring tool that generates AI-powered summaries of repository activity. It supports two main operations: tracking commits/releases across repositories (news) and analyzing repository forks that are ahead of their parent (forks). The tool supports both Claude CLI and OpenAI API for generating concise summaries.

## Architecture

The project uses a **parallel processor pattern** with extensive code reuse through abstract base classes and mixins:

### Core Architecture Pattern
- **ParallelBaseProcessor** (`modules/parallel_base_processor.py`): Thread-safe base class providing 4-worker concurrent repository processing with display queue synchronization
- **RepositoryProcessorMixin** (`modules/repository_mixin.py`): Shared GitHub data processing logic (URL parsing, state comparisons, incremental updates)
- **Concrete Processors**: NewsProcessor and ForksProcessor inherit from ParallelBaseProcessor + Mixin for 95% code reuse

### Parallel Processing Components
- **ThreadPoolExecutor**: 4-worker concurrent processing with configurable `max_workers`
- **Display Queue System**: Background thread for ordered, race-condition-free output
- **Per-Repository Locking**: `_repo_locks` prevents state corruption during concurrent processing
- **Global State Lock**: `_state_lock` synchronizes state file operations
- **Thread-Safe Display Methods**: All `self.display.*` calls replaced with `self._safe_display_*` variants

### Shared Components
- **GitHubFetcher** (`modules/github_fetcher.py`): GitHub CLI integration with methods for commits, releases, forks, and fork comparisons
- **SummaryGenerator** (`modules/summary_generator.py`): AI orchestration with template-based prompt building via PromptManager
- **PromptManager** (`modules/prompt_manager.py`): Centralized template loading supporting multiple prompt types (summary, fork_summary)
- **AIProvider** (`modules/ai_provider.py`): Abstract provider pattern supporting Claude CLI and OpenAI API with fallback handling
- **ConfigManager** (`modules/config_manager.py`): INI-based configuration with inline comment parsing and state persistence
- **TerminalDisplay** (`modules/display.py`): Terminal formatting for news summaries and fork analysis results
- **CostTracker** (`modules/cost_tracker.py`): AI usage cost tracking and aggregation with sub-cent precision
- **DebugLogger** (`modules/debug_logger.py`): Centralized debug output with performance-optimized caching

### Command Processing Flow
1. **Command Router** (`gh-utils.py`): Factory pattern creates appropriate processor (NewsProcessor/ForksProcessor)
2. **ParallelBaseProcessor.execute()**: Manages ThreadPoolExecutor, display queue, and parallel repository processing
3. **Concrete _process_repository()**: Processor-specific logic (news: commits/releases, forks: fork analysis)
4. **Shared Components**: GitHubFetcher, SummaryGenerator, thread-safe display handle implementation details

## Key Technical Decisions

**Parallel Processing with Thread Safety**: 4-worker ThreadPoolExecutor with comprehensive synchronization eliminates sequential bottlenecks. Display queue ensures ordered output, per-repository locks prevent state corruption.

**Processor Pattern with Mixins**: Eliminates 80% code duplication between news and forks processing. Adding new repository processors requires only implementing `_process_repository()` method.

**Template-Based AI Integration**: PromptManager loads external templates (`prompts/*.txt`) with placeholder substitution. SummaryGenerator detects context (news vs forks) and builds appropriate prompts automatically.

**GitHub CLI with jq Filtering**: Uses `gh api` commands with server-side jq filtering for 5,000/hour rate limits. Handles multiple JSON objects per line for fork listings.

**Incremental State Management**: JSON-based state tracking per repository with configurable persistence. Only processes repositories with actual newer content (commit SHA/release ID comparison).

## Commands

### Running the Application
```bash
# News: track commits and releases (default) - runs with 4 parallel workers
./gh-utils.py
./gh-utils.py news

# Forks: analyze repository forks ahead of parent - runs with 4 parallel workers
./gh-utils.py forks

# Repository management
./gh-utils.py add <github_url> [name]     # Add repository to config
./gh-utils.py remove <name>               # Remove repository 
./gh-utils.py list                        # List configured repos with status
./gh-utils.py clear <name>                # Reset tracking for repository
```

### Development and Testing
```bash
# Setup and installation
cp config.example.txt config.txt
pip install -r requirements.txt
gh auth login

# Enable debug mode (edit config.txt: debug = true)
./gh-utils.py news    # Shows prompt details, API calls, token usage, parallel worker activity

# Enable cost tracking (edit config.txt: show_costs = true)
./gh-utils.py news    # Shows AI token usage and estimated costs

# Test different AI providers (edit config.txt)
# provider = openai (requires api_key)
# provider = claude (requires claude_cli_path)
./gh-utils.py news

# Test without state persistence (edit config.txt: save_state = false)
./gh-utils.py news    # Always shows all recent activity

# Test parallel processing performance
time ./gh-utils.py news    # Should complete in ~30-40s for 7 repos vs ~90s sequential

# Run with timeout for testing
timeout 30 ./gh-utils.py news
timeout 60 ./gh-utils.py forks

# Test core functionality
./gh-utils.py add https://github.com/octocat/Hello-World test-repo
./gh-utils.py list
./gh-utils.py remove test-repo

# Test environment variable override
export OPENAI_API_KEY="your-key"
./gh-utils.py news

# Test first-run setup (creates config from example)
mv config.txt config.txt.backup
./gh-utils.py news
mv config.txt.backup config.txt

# Test GitHub API endpoints directly
gh api repos/owner/repo/commits --jq '.[0:3]'
gh api repos/owner/repo/forks --jq '.[0:3]'
gh api repos/parent/repo/compare/main...fork:repo:main

# Test specific Python modules directly
python3 -c "from modules.cost_tracker import CostTracker; print('Cost tracking loaded')"
python3 -c "from modules.debug_logger import DebugLogger; print('Debug logging loaded')"
python3 -c "from modules.parallel_base_processor import ParallelBaseProcessor; print('Parallel processing loaded')"

# Run comprehensive test framework (all 3 core functionalities)
timeout 110 python3 test_framework/main_test.py --debug

# Test framework development workflow
cd ../github-utils-tests          # Edit test framework files
git add test_framework/ && git commit -m "test: improve validation"
cd ../github-utils               # Back to main development
```

### Required Dependencies
- **GitHub CLI**: `gh auth login` (must be authenticated)
- **AI Provider**: Either Claude CLI path OR OpenAI API key in config.txt
- **Python**: Uses standard library only (optional: `openai>=1.0.0` for OpenAI provider)

### Environment Variables Support
Configuration can use environment variable overrides (higher priority than config.txt):
- `OPENAI_API_KEY`: OpenAI API key
- `CLAUDE_CLI_PATH`: Path to Claude CLI executable

### Security Notes
- **config.txt is git-ignored**: Contains sensitive API keys and credentials
- **Use config.example.txt**: Template for safe configuration setup
- **Environment variables**: Preferred for CI/CD and production deployments
- **Never commit credentials**: All sensitive data excluded from git history

## Configuration Structure

The `config.txt` file uses INI format with inline comment support:

**[ai]**: AI provider selection
- `provider`: `claude` or `openai`
- `model`: OpenAI model name (e.g., `gpt-4o-mini`)

**[repositories]**: Repository monitoring list
- Format: `name = github_url`

**[settings]**: Application behavior
- News: `max_commits`, `max_releases`, `save_state`, `debug`, `timeout`, `show_costs`
- Forks: `max_forks`, `min_commits_ahead`, `fork_activity_days`, `exclude_private_forks`
- Parallel: `max_workers` (default: 4), `repo_timeout` (default: 60)

## Adding New Repository Processors

The parallel architecture makes adding new processors straightforward:

1. **Create Processor Class**: Inherit from `ParallelBaseProcessor` and `RepositoryProcessorMixin`
2. **Implement _process_repository()**: Add processor-specific logic for repository analysis
3. **Use Thread-Safe Display**: Replace `self.display.*` with `self._safe_display_*` methods
4. **Create Prompt Template**: Add `prompts/{name}_prompt.txt` with placeholders
5. **Update Command Router**: Add processor to `processors` dict in `gh-utils.py`
6. **Add Configuration**: Add processor-specific settings to `config.txt` [settings] section

Example minimal processor:
```python
from .parallel_base_processor import ParallelBaseProcessor
from .repository_mixin import RepositoryProcessorMixin

class MyProcessor(ParallelBaseProcessor, RepositoryProcessorMixin):
    def __init__(self):
        super().__init__(template_name='my_template')
    
    @property
    def state_type(self):
        return 'my_processor'
    
    def _process_repository(self, repo):
        owner, repo_name, repo_key = self.extract_repo_info(repo['url'])
        # Custom processing logic here
        # Use self.fetcher, self.generator, self._safe_display_* methods
```

## Code Architecture Notes

**Parallel Processing Implementation**: ParallelBaseProcessor uses ThreadPoolExecutor with configurable workers (default: 4). Display queue (`_display_queue`) serializes all output through background thread. Per-repository locks (`_repo_locks`) and global state lock (`_state_lock`) prevent race conditions.

**Thread-Safe Display Pattern**: All display operations must use `_safe_display_*` methods which queue display functions for execution by background thread. Direct `self.display.*` calls will cause race conditions and garbled output.

**Configuration Parsing**: ConfigManager handles inline comments in INI files by splitting on '#' and stripping whitespace. **Comment Preservation**: `save_config()` method maintains user comments when writing configuration updates. Use `get_setting(key, default)` with defaults for new settings.

**GitHub API Integration**: GitHubFetcher uses subprocess.run with `gh api` commands and jq filtering. **Performance Optimized**: `_setup_token_cache()` method caches GH_TOKEN environment variable to eliminate 85% authentication overhead (~6x faster API calls). Multiple JSON objects per line require line-by-line parsing, not direct json.loads().

**AI Context Detection**: SummaryGenerator automatically detects prompt context by checking for 'fork_name' in repo_data and builds appropriate prompts (news vs forks).

**State Management**: JSON state tracks `last_commit`, `last_release`, and `processed_forks` per repository. Only update state after successful AI generation to prevent skipping on retry. Parallel processing includes incremental state saving per repository.

**Cost Tracking**: CostTracker integrates with AI providers to track token usage and costs. Both Claude CLI (estimated) and OpenAI API (actual) costs are calculated with current pricing: Claude Sonnet 4 ($3/$15 per MTok), OpenAI GPT-4o-mini ($0.15/$0.60 per MTok).

**Debug Infrastructure**: DebugLogger provides performance-optimized debug output with cached settings. Use `debug_api_call()` for API operations and `debug_tokens()` for cost analysis.

**Enhanced Fork Analysis**: Fork processor includes intelligent README comparison - fetches parent README once, fork READMs conditionally when modified, and provides rich AI context with full README content for superior analysis.

**Error Recovery**: ParallelBaseProcessor continues processing remaining repositories when individual repos fail. Use try/catch around individual repo processing, not entire command execution. Per-repository isolation prevents failures from affecting other repositories.

## Performance Characteristics

**Parallel Execution**: 4-worker processing achieves ~70% performance improvement over sequential execution. 7 repositories: ~90s sequential → ~38s parallel.

**Worker Scaling**: `max_workers` is automatically limited to `min(repository_count, configured_max_workers)` to avoid unnecessary overhead.

**Timeout Protection**: Global timeout (180s) and per-repository timeout (`repo_timeout`, default 60s) prevent hanging.

## Troubleshooting

### Common Issues

**"GitHub CLI not found"**
- Install: `brew install gh` (macOS) or visit cli.github.com
- Authenticate: `gh auth login`
- Verify: `gh auth status`

**"OpenAI API key invalid"**
- Check API key at platform.openai.com/api-keys
- Verify environment variable: `echo $OPENAI_API_KEY`
- Test API access: `python3 -c "import openai; print('OpenAI accessible')"`

**"No repositories configured"**
- Add repository: `./gh-utils.py add <github_url>`
- Check config: `./gh-utils.py list`

**"Permission denied"**
- Make executable: `chmod +x gh-utils.py`

**"First run fails with config error"**
- Copy template: `cp config.example.txt config.txt`
- Edit AI provider settings in config.txt

**"Garbled output during parallel execution"**
- Ensure all display calls use `self._safe_display_*` methods
- Never use direct `self.display.*` or `print()` in processor methods

**"State corruption with parallel processing"**
- Verify per-repository state updates use proper locking
- Check that `_save_repository_state()` is called within repository locks

## Test Framework Setup

The project uses a **git worktree + symlink architecture** for cross-branch test framework access:

### Architecture
- **Main Development**: `test-with-framework` branch (latest main app code)
- **Test Framework**: `test_framework` branch (pure test framework code only)
- **Worktree**: `../github-utils-tests` (separate directory for test development)
- **Symlink**: `test_framework/` → `../github-utils-tests/test_framework/`

### Setup (One-time)
```bash
# Create worktree for test framework development
git worktree add ../github-utils-tests test_framework

# Create symlink in main project (works from any branch)
ln -s ../github-utils-tests/test_framework ./test_framework
```

### Directory Structure
```
/github-utils/                    # Main project (any branch)
├── modules/
├── gh-utils.py
├── test_framework -> ../github-utils-tests/test_framework/  # Symlink
└── ...

/github-utils-tests/              # Worktree (test_framework branch)
├── .gitignore
└── test_framework/               # Test framework files
    ├── main_test.py
    ├── test_runner.py
    └── ...
```

### Development Workflow
```bash
# Run tests from ANY branch
timeout 110 python3 test_framework/main_test.py --debug

# Edit test framework
cd ../github-utils-tests
# Make changes to test_framework/ files
git add test_framework/ && git commit -m "test: improve validation"
git push origin test_framework

# Back to main development
cd ../github-utils
# Continue working on main app (commits go to current branch)
```

### Benefits
- ✅ **Universal Access**: Run tests from any branch without file copying
- ✅ **Correct Commits**: Test changes automatically commit to `test_framework` branch
- ✅ **Live Updates**: Changes in worktree immediately visible in main directory
- ✅ **Clean Separation**: No mixing of main app and test framework code
- ✅ **Branch Independence**: Main development unaffected by test framework changes

### Troubleshooting Test Framework
**"Test framework not found"**
- Verify symlink: `ls -la test_framework/`
- Recreate symlink: `ln -s ../github-utils-tests/test_framework ./test_framework`

**"Worktree not found"**
- Check worktrees: `git worktree list`
- Recreate if needed: `git worktree add ../github-utils-tests test_framework`