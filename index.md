# GitHub Utils - Project Index

## Overview
**gh-utils** is a GitHub repository monitoring tool that generates AI-powered summaries of repository activity with **4-worker parallel processing** for 70% faster execution. It supports two main operations: tracking commits/releases across repositories (news) and analyzing repository forks that are ahead of their parent (forks).

## Main Entry Point
- **gh-utils.py**: Main command-line interface
  - Command router with factory pattern
  - Commands: `news`, `forks`, `add`, `remove`, `list`, `clear`
  - Creates appropriate processor instances
  - Supports both URL and alias-based repository processing

## Core Architecture

### Parallel Processing Base Class
- **modules/parallel_base_processor.py**: `ParallelBaseProcessor`
  - **Thread-safe base class** for all repository processors
  - **4-worker ThreadPoolExecutor** with configurable `max_workers`
  - **Display queue system** (`_display_queue`) for ordered, race-condition-free output
  - **Per-repository locking** (`_repo_locks`) prevents state corruption
  - **Global state lock** (`_state_lock`) synchronizes state file operations
  - **Thread-safe display methods**: `_safe_display_*()` variants
  - **Incremental state saving** per repository completion
  - Key methods: `execute()`, `_process_repository_safe()`, `_display_worker()`
  - Abstract properties: `state_type` for state file management
  - **Performance**: 7 repositories ~90s sequential → ~38s parallel

### Shared Logic Mixin
- **modules/repository_mixin.py**: `RepositoryProcessorMixin`
  - Shared GitHub data processing logic
  - Methods: `extract_repo_info()`, `has_newer_releases()`, `should_process_repository()`
  - URL parsing and state comparison utilities
  - Cross-repository and fork-aware comparison logic

### Concrete Processors
- **modules/news_processor.py**: `NewsProcessor`
  - Inherits from **ParallelBaseProcessor** + RepositoryProcessorMixin
  - Key method: `_process_repository()` - handles commits/releases + individual branches
  - `_analyze_individual_branches()` - processes non-default branches separately
  - `_process_selective_branches()` - optimized branch subset processing
  - **State management** for both main branch and individual branches
  - **Thread-safe display calls**: All `self.display.*` → `self._safe_display_*`
  - **Early-exit optimization** with `StateManager.main_branch_unchanged()`

- **modules/forks_processor.py**: `ForksProcessor`
  - Inherits from **ParallelBaseProcessor** + RepositoryProcessorMixin
  - Key method: `_process_repository()` - analyzes repository forks
  - **Multi-branch fork analysis** with `_process_fork_branches()`
  - **Smart fork filtering** with `_should_process_fork_by_state()`
  - **README comparison** for enhanced fork insights
  - **Thread-safe display calls**: All fork display operations queued
  - **State optimization** with lightweight fork pre-filtering

### GitHub Integration
- **modules/github_fetcher.py**: `GitHubFetcher`
  - GitHub CLI (`gh`) integration with subprocess calls
  - **Performance Optimized**: Token caching eliminates 85% auth overhead (~6x faster)
  - Key methods: `_setup_token_cache()` - caches GH_TOKEN environment variable
  - **Thread-safe**: All API calls are stateless and parallelizable
  - Methods:
    - `get_commits()`, `get_releases()`, `get_forks()`
    - `get_fork_info()`, `get_branch_comparison()`
    - `get_repository_branches()`, `get_branch_commits_since_base()`
    - `get_default_branch()`, `get_latest_commit_timestamp()`
    - `get_readme()`, `generate_readme_diff()` - README analysis for forks
    - `get_current_main_sha()` - early-exit optimization
  - Uses jq filtering for server-side JSON processing
  - Handles both same-repo and cross-repo comparisons

### AI Integration
- **modules/summary_generator.py**: `SummaryGenerator`
  - AI orchestration with template-based prompt building
  - **Thread-safe**: Each processor instance can generate concurrently
  - Context detection: automatically chooses news vs forks prompts
  - Methods: `generate_summary()`, `_build_prompt()`
  - Integrates with PromptManager for template loading

- **modules/prompt_manager.py**: `PromptManager`
  - Centralized template loading from `prompts/` directory
  - **Thread-safe**: Template loading is stateless
  - Methods: `load_template()`, `build_prompt()`
  - Supports multiple prompt types: `summary`, `fork_summary`
  - Placeholder substitution with template variables

- **modules/ai_provider.py**: `AIProvider` (abstract)
  - **ClaudeProvider**: Claude CLI integration
  - **OpenAIProvider**: OpenAI API integration
  - **Thread-safe**: All providers support concurrent execution
  - Fallback handling and error recovery

### Configuration Management
- **modules/config_manager.py**: `ConfigManager`
  - INI-based configuration with **comment preservation** across updates
  - **Thread-safe**: Configuration loading is stateless
  - Methods: `get_setting()`, `get_boolean_setting()`, `get_int_setting()`
  - `save_config()` - maintains user comments when writing updates
  - Settings categories: `[ai]`, `[repositories]`, `[settings]`
  - Environment variable overrides (OPENAI_API_KEY, CLAUDE_CLI_PATH)
  - **Parallel settings**: `max_workers`, `repo_timeout`
  - **Fail-fast validation**: Immediate feedback on configuration errors

### Display and Output
- **modules/display.py**: `TerminalDisplay`
  - Terminal formatting for news summaries and fork analysis
  - **NOT thread-safe**: Must be accessed through display queue
  - Methods:
    - `display_news_summary()` - main repository summaries
    - `display_branch_summary()` - individual branch summaries
    - `display_fork_summary()` - fork analysis results
    - `display_forks_header()`, `display_forks_summary()` - fork headers
    - `display_no_updates()`, `display_error()` - status messages
    - `_print_summary_section()` - formatted output with separators
  - ANSI hyperlink support for clickable repository names
  - Time formatting: `format_time_ago()`

### State Management
- **modules/state_manager.py**: `StateManager`
  - **Thread-safe** static methods for state operations
  - JSON-based state persistence per repository
  - Methods: 
    - `should_process_branch_by_state()`, `update_branch_state()`
    - `needs_repository_processing()` - early-exit optimization
    - `main_branch_unchanged()` - performance optimization
    - `update_fork_state()` - fork-specific state management
  - Tracks: `last_commit`, `last_release`, `processed_forks`, branch states
  - **Parallel-safe**: All state operations use proper locking

### Utilities
- **modules/cost_tracker.py**: `CostTracker`
  - AI usage cost tracking and aggregation
  - **Thread-safe**: Instance-based tracking per processor
  - Token counting and cost calculation
  - Methods: `track_usage()`, `format_cost_info()`, `add_cost()`, `reset()`

- **modules/debug_logger.py**: `DebugLogger`
  - Centralized debug output with performance optimization
  - **Thread-safe**: Can be used from parallel processors
  - Methods: `debug_api_call()`, `debug_tokens()`, `debug()`
  - Cached settings for performance

- **modules/commit_utils.py**: Commit filtering utilities
  - **Thread-safe**: Stateless filtering functions
  - `filter_commits_since_last_processed()` - incremental processing
  - Used by both news and forks processors

- **modules/comment_preserving_parser.py**: `CommentPreservingINIParser`
  - Custom INI parser that preserves comments and formatting
  - **Thread-safe**: File operations use proper locking
  - Methods: `parse_file()`, `add_repository()`, `remove_repository()`, `save_file()`
  - Handles repository section management with comment preservation
  - Atomic file operations with backup/restore on failure
  - Used by ConfigManager for repository modifications

## Module Organization
- **modules/__init__.py**: Package initialization (minimal)
- All modules use relative imports within the package
- No external dependencies in core modules (except optional openai)
- **Thread-safety**: All modules designed for parallel execution

## Configuration Files

### config.txt (INI format)
**[ai] section:**
- `provider`: claude | openai
- `model`: OpenAI model name
- `claude_cli_path`: Path to Claude CLI
- `api_key`: OpenAI API key
- `timeout`: AI execution timeout (seconds)
- `show_costs`: Display AI token costs

**[repositories] section:**
- Format: `name = github_url`

**[settings] section:**
- **General**: `save_state=true`, `debug=false`, `show_costs=false`
- **News**: `max_commits=50`, `max_releases=10`, `max_branches_per_repo=5`
- **Branches**: `min_branch_commits=1`, `analyze_default_branch=false`
- **Forks**: `max_forks=200`, `min_commits_ahead=1`, `exclude_private_forks=false`
- **Parallel**: `max_workers=4`, `repo_timeout=60` - **NEW: parallel processing configuration**
- **API**: `timeout=30` - GitHub API timeout in seconds

### Prompt Templates (prompts/)
- **summary_prompt.txt**: News/commits summary template
- **fork_summary_prompt.txt**: Fork analysis template
- Templates use placeholder substitution for dynamic content

### Debug and Analysis Files
- **debug_prompts/**: AI prompt debugging output (timestamp-named files)
- **test_reports/**: Test framework execution reports
- **optimization.md**, **parallel_analysis.md**, **state_analysis.md**: Performance analysis
- **workers.md**: Parallel processing implementation specification

### Other Project Files
- **.gitignore**: Excludes config.txt, state files, __pycache__, .DS_Store
- **LICENSE**: MIT License
- **README.md**: User-facing documentation and setup guide
- **CLAUDE.md**: AI assistant instructions for code development
- **config.example.txt**: Template configuration file with all settings
- **requirements.txt**: Optional dependencies (openai>=1.0.0 for OpenAI provider)
- **benchmark.py**: Performance benchmarking script
- **profile_main.py**: Profiling script for performance analysis

## Data Flow

### Parallel News Processing
1. `NewsProcessor.execute()` starts ThreadPoolExecutor with 4 workers
2. **Display queue thread** started for ordered output
3. **Per-repository workers**: Each worker processes `_process_repository()` concurrently
4. **Thread-safe state access**: Per-repo locks prevent corruption
5. For each repo: `_process_repository()` fetches commits/releases
6. `_analyze_individual_branches()` processes non-default branches
7. `SummaryGenerator.generate_summary()` creates AI summaries (parallel-safe)
8. **Queued display**: `_safe_display_news_summary()` queues output
9. **Immediate state save**: State updated per repository completion
10. **Display thread shutdown**: Ordered output completion

### Parallel Fork Processing
1. `ForksProcessor.execute()` starts ThreadPoolExecutor with 4 workers
2. **Display queue thread** started for ordered output
3. **Per-repository workers**: Each worker processes repository forks concurrently
4. **Smart filtering**: `_should_process_fork_by_state()` pre-filters forks
5. **Multi-branch analysis**: `_process_fork_branches()` analyzes all fork branches
6. **README comparison**: Intelligent README diff analysis
7. **Queued display**: `_safe_display_fork_summary()` queues results
8. **Thread-safe state**: Fork state updated with proper locking

## Key Features
- **🚀 Parallel Processing**: 4-worker concurrent execution (70% faster than sequential)
- **🔒 Thread Safety**: Complete synchronization with display queue and per-repo locking
- **⚡ Performance Optimized**: GitHub CLI token caching for 6x faster API calls
- **📊 Incremental Processing**: Only processes new commits/releases since last run
- **💾 State Persistence**: Separate JSON state files for news and forks per repository
- **🌿 Multi-Branch Analysis**: Separate AI summaries for each active branch
- **🏷️ Repository Aliases**: Process repos using short names instead of full URLs
- **🍴 Fork-Aware**: Handles both regular repos and forks with cross-repo comparisons
- **🤖 AI Provider Flexibility**: Supports both Claude CLI and OpenAI API
- **💰 Cost Tracking**: Monitors AI token usage and estimated costs
- **💬 Comment-Preserving Config**: INI configuration maintains user comments
- **⚠️ Fail-Fast Architecture**: Immediate feedback on configuration/auth issues
- **🐛 Debug Mode**: Detailed logging of API calls and processing steps

## Performance Optimizations
- **🔄 Parallel Processing**: 4-worker ThreadPoolExecutor (configurable max_workers)
- **🔗 Token Caching**: GitHubFetcher caches GH_TOKEN for 6x faster API calls
- **🏃 Early Exit**: `StateManager.main_branch_unchanged()` skips unchanged repositories
- **📈 Incremental Updates**: State tracking prevents redundant processing
- **🌐 Server-side Filtering**: GitHub API jq queries reduce data transfer
- **⏱️ Lazy Evaluation**: Branches analyzed only when changes detected
- **🔀 Smart Fork Filtering**: Pre-filters forks by timestamp before expensive operations
- **💾 Incremental State Saving**: Progress preserved on individual repository completion

## Thread Safety Design
- **🏗️ ParallelBaseProcessor**: Thread-safe base class with proper synchronization
- **🔐 Locking Strategy**: Per-repository locks + global state lock
- **📺 Display Queue**: Background thread serializes all output
- **🔄 Stateless Components**: GitHubFetcher, SummaryGenerator, AIProvider are thread-safe
- **⚠️ Thread-Safe Display**: All `self.display.*` → `self._safe_display_*` in processors
- **💾 Protected State**: StateManager uses static methods with proper locking

## Test Framework (Symlinked)
- **test_framework/**: Symlink to `../github-utils-tests/test_framework/`
- Separate git worktree on `test_framework` branch
- Allows running tests from any branch without file duplication
- Main test entry: `test_framework/main_test.py`
- Run with: `timeout 110 python3 test_framework/main_test.py --debug`

## Dependencies
- **GitHub CLI**: `gh` command must be authenticated
- **AI Provider**: Either Claude CLI or OpenAI API key
- **Python**: Standard library only (optional: `openai>=1.0.0`)
- **Threading**: Uses concurrent.futures.ThreadPoolExecutor for parallel processing

## Performance Benchmarks
- **Sequential**: 7 repositories × ~13s each = ~90s total
- **Parallel (4 workers)**: 7 repositories in ~38s = **58% improvement**
- **Worker efficiency**: Automatic scaling with `min(repository_count, max_workers)`
- **Timeout protection**: Global (180s) and per-repository (60s default) timeouts