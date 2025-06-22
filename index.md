# GitHub Utils - Project Index

## Overview
**gh-utils** is a GitHub repository monitoring tool that generates AI-powered summaries of repository activity. It supports two main operations: tracking commits/releases across repositories (news) and analyzing repository forks that are ahead of their parent (forks).

## Main Entry Point
- **gh-utils.py**: Main command-line interface
  - Command router with factory pattern
  - Commands: `news`, `forks`, `add`, `remove`, `list`, `clear`
  - Creates appropriate processor instances

## Core Architecture

### Base Classes
- **modules/base_processor.py**: `BaseProcessor`
  - Abstract base class for all processors
  - Template method pattern: `execute()` → `load_config()` → `_process_repository()` → `save_state()`
  - Shared initialization: GitHubFetcher, SummaryGenerator, TerminalDisplay

- **modules/repository_mixin.py**: `RepositoryProcessorMixin`
  - Shared GitHub data processing logic
  - Methods: `extract_repo_info()`, `has_newer_releases()`, `should_process_repository()`
  - URL parsing and state comparison utilities

### Concrete Processors
- **modules/news_processor.py**: `NewsProcessor`
  - Inherits from BaseProcessor + RepositoryProcessorMixin
  - Key method: `_process_repository()` - handles commits/releases + individual branches
  - `_analyze_individual_branches()` - processes non-default branches separately
  - State management for both main branch and individual branches

- **modules/forks_processor.py**: `ForksProcessor`
  - Inherits from BaseProcessor + RepositoryProcessorMixin
  - Key method: `_process_repository()` - analyzes repository forks
  - Fork filtering and comparison logic

### GitHub Integration
- **modules/github_fetcher.py**: `GitHubFetcher`
  - GitHub CLI (`gh`) integration with subprocess calls
  - Methods:
    - `get_commits()`, `get_releases()`, `get_forks()`
    - `get_fork_info()`, `get_branch_comparison()`
    - `get_repository_branches()`, `get_branch_commits_since_base()`
    - `get_default_branch()`, `get_latest_commit_timestamp()`
  - Uses jq filtering for server-side JSON processing
  - Handles both same-repo and cross-repo comparisons

### AI Integration
- **modules/summary_generator.py**: `SummaryGenerator`
  - AI orchestration with template-based prompt building
  - Context detection: automatically chooses news vs forks prompts
  - Methods: `generate_summary()`, `_build_prompt()`
  - Integrates with PromptManager for template loading

- **modules/prompt_manager.py**: `PromptManager`
  - Centralized template loading from `prompts/` directory
  - Methods: `load_template()`, `build_prompt()`
  - Supports multiple prompt types: `summary`, `fork_summary`
  - Placeholder substitution with template variables

- **modules/ai_provider.py**: `AIProvider` (abstract)
  - **ClaudeProvider**: Claude CLI integration
  - **OpenAIProvider**: OpenAI API integration
  - Fallback handling and error recovery

### Configuration Management
- **modules/config_manager.py**: `ConfigManager`
  - INI-based configuration with inline comment support
  - Methods: `get_setting()`, `get_boolean_setting()`, `get_int_setting()`
  - Settings categories: `[ai]`, `[repositories]`, `[settings]`
  - Environment variable overrides (OPENAI_API_KEY, CLAUDE_CLI_PATH)

### Display and Output
- **modules/display.py**: `TerminalDisplay`
  - Terminal formatting for news summaries and fork analysis
  - Methods:
    - `display_news_summary()` - main repository summaries
    - `display_branch_summary()` - individual branch summaries
    - `display_fork_summary()` - fork analysis results
    - `_print_summary_section()` - formatted output with separators
  - ANSI hyperlink support for clickable repository names
  - Time formatting: `format_time_ago()`

### Utilities
- **modules/cost_tracker.py**: `CostTracker`
  - AI usage cost tracking and aggregation
  - Token counting and cost calculation
  - Methods: `track_usage()`, `format_cost_info()`

- **modules/debug_logger.py**: `DebugLogger`
  - Centralized debug output with performance optimization
  - Methods: `debug_api_call()`, `debug_tokens()`

- **modules/state_manager.py**: `StateManager`
  - JSON-based state persistence per repository
  - Methods: `should_process_branch_by_state()`, `update_branch_state()`
  - Tracks: `last_commit`, `last_release`, `processed_forks`, branch states

- **modules/commit_utils.py**: Commit filtering utilities
  - `filter_commits_since_last_processed()` - incremental processing

## Configuration Files

### config.txt (INI format)
**[ai] section:**
- `provider`: claude | openai
- `model`: OpenAI model name
- `claude_cli_path`: Path to Claude CLI
- `api_key`: OpenAI API key

**[repositories] section:**
- Format: `name = github_url`

**[settings] section:**
- News: `max_commits=50`, `max_releases=10`, `max_branches_per_repo=5`
- State: `save_state=true`, `debug=false`, `show_costs=false`
- Branches: `min_branch_commits=1`, `branch_activity_days=30` (unused)
- Forks: `max_forks=200`, `min_commits_ahead=1`, `exclude_private_forks=false`

### Prompt Templates (prompts/)
- **summary_prompt.txt**: News/commits summary template
- **fork_summary_prompt.txt**: Fork analysis template
- Templates use placeholder substitution for dynamic content

## Data Flow

### News Processing
1. `NewsProcessor.execute()` loads config and iterates repositories
2. For each repo: `_process_repository()` fetches commits/releases
3. `_analyze_individual_branches()` processes non-default branches
4. `SummaryGenerator.generate_summary()` creates AI summaries
5. `TerminalDisplay.display_news_summary()` formats output
6. State updated with new commit SHAs and branch states

### Fork Processing
1. `ForksProcessor.execute()` loads config and iterates repositories
2. For each repo: `_process_repository()` fetches fork list
3. Filters forks by activity and commits ahead
4. For each active fork: analyzes commits and generates summary
5. `TerminalDisplay.display_fork_summary()` formats results

## Key Features
- **Incremental Processing**: Only processes new commits/releases since last run
- **State Persistence**: JSON state files track progress per repository
- **Multi-Branch Analysis**: Separate summaries for each active branch
- **Fork-Aware**: Handles both regular repos and forks with cross-repo comparisons
- **AI Provider Flexibility**: Supports both Claude CLI and OpenAI API
- **Cost Tracking**: Monitors AI token usage and estimated costs
- **Debug Mode**: Detailed logging of API calls and processing steps

## Dependencies
- **GitHub CLI**: `gh` command must be authenticated
- **AI Provider**: Either Claude CLI or OpenAI API key
- **Python**: Standard library only (optional: `openai>=1.0.0`)