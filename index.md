# GitHub Utils Project Index

**AI-powered GitHub repository monitoring tool with news tracking and fork analysis capabilities**

## Overview
**gh-utils** - GitHub repository monitoring tool with AI-powered summaries. Supports news tracking (commits/releases) and fork analysis with enhanced README comparison.

## Main Files

### Entry Point
- **gh-utils.py** - Main CLI entry point with command routing and URL-based processing
  - Standard commands: news, forks, add, remove, list, clear
  - URL-based processing: Process any GitHub repository directly without configuration
  - `is_github_url()` - Detects GitHub URLs in command arguments
  - `create_temp_repository()` - Creates temporary repository structure from URLs
  - Multiple syntax support for URL processing (see URL Processing section)

### Core Modules (`modules/`)

#### Base Architecture
- **base_processor.py** - Abstract base class for repository processors with template method pattern
  - `execute()` - Main workflow (load config → process repos → save state)
  - `_process_repository()` - Abstract method for concrete implementations
- **repository_mixin.py** - Shared GitHub data processing logic
  - `extract_repo_info()` - URL parsing and repository key generation
  - State comparison and incremental update utilities

#### Concrete Processors  
- **news_processor.py** - Tracks commits and releases across repositories
  - Inherits from BaseProcessor + RepositoryProcessorMixin
  - `_process_repository()` - Fetches commits/releases, generates AI summaries
- **forks_processor.py** - Analyzes repository forks ahead of parent
  - Enhanced with README comparison capabilities
  - `_process_repository()` - Fork detection, README analysis, AI summarization
  - `_update_fork_state()` - Fork-specific state tracking

#### GitHub Integration
- **github_fetcher.py** - GitHub CLI integration with comprehensive API access
  - `get_commits()` - Commit history with jq filtering
  - `get_releases()` - Release data extraction
  - `get_forks()` - Fork enumeration with metadata
  - `compare_fork_with_parent()` - Fork comparison with file change detection
  - `get_readme()` - README content fetching with base64 decoding
  - `readme_was_modified()` - README change detection in commits
  - `compare_readme_content()` - Normalized README comparison
  - `extract_owner_repo()` - URL parsing with regex
  - `get_latest_commit_sha()` - For incremental state tracking

#### AI Integration
- **ai_provider.py** - Abstract AI provider pattern with fallback handling
  - `create_ai_provider()` - Factory for Claude CLI vs OpenAI API
  - `ClaudeCLIProvider` - Claude CLI integration with subprocess execution
  - `OpenAIProvider` - OpenAI API integration with direct API calls
  - Token usage tracking and cost estimation
- **summary_generator.py** - AI orchestration with template-based prompts
  - `generate_summary()` - Main AI interaction interface
  - `_build_prompt()` - Context-aware prompt building (news vs forks)
  - `_build_commits_section()` - Commit data formatting for prompts
  - `_build_releases_section()` - Release data formatting for prompts
  - Enhanced with README sections for fork analysis
- **prompt_manager.py** - Centralized template loading and placeholder substitution
  - Supports multiple prompt types (summary, fork_summary)
  - Template file management from prompts/ directory

#### Configuration & Utilities
- **config_manager.py** - INI configuration with inline comment parsing
  - `get_setting()` - Type-safe configuration access
  - `get_boolean_setting()` - Boolean configuration parsing
  - `get_int_setting()` - Integer configuration with defaults
  - `load_state()` - JSON state file loading
  - `save_state()` - JSON state file persistence
  - `load_repositories()` - Extract repository list from [repositories] section
- **display.py** - Terminal formatting for news summaries and fork analysis
  - `display_news_summary()` - Commit/release formatting
  - `display_fork_summary()` - Fork analysis results
  - `display_forks_summary()` - Repository-level statistics
  - `display_loading()`, `display_error()`, `display_info()` - Status messages
- **debug_logger.py** - Debug output management
- **cost_tracker.py** - AI usage cost tracking and aggregation

### Configuration Files

#### `config.txt` (INI format)
**Main configuration with multiple sections:**
- `[ai]` - AI provider selection
  - `provider` - Choose between claude or openai
  - `model` - Model name for OpenAI (e.g., gpt-4o-mini)
- `[claude]` - Claude CLI path configuration
  - `claude_cli_path` - Path to Claude CLI executable (supports tilde expansion)
- `[openai]` - OpenAI API configuration
  - `api_key` - OpenAI API key (only required if provider=openai)
- `[repositories]` - Repository monitoring list  
  - Format: `name = github_url`
- `[settings]` - Application behavior
  - `save_state` - Enable/disable state persistence (true/false)
  - `debug` - Enable detailed logging and prompt preview
  - `timeout` - AI provider timeout in seconds
  - `show_costs` - Display AI token usage and costs
  - `max_commits`/`max_releases` - News analysis data fetch limits
  - `max_forks` - Maximum forks to check per repository
  - `min_commits_ahead` - Minimum commits ahead to consider for fork analysis
  - `fork_activity_days` - Only check forks active within X days
  - `exclude_private_forks` - Skip private forks in analysis

#### `state.json` (auto-managed)
**Tracks last processed commit SHA per repository for incremental processing**

### Prompt Templates
- **prompts/summary_prompt.txt** - News analysis template for commits/releases
  - `{repo_name}`, `{commits_section}`, `{releases_section}` placeholders
  - Terminal-specific formatting (no markdown, no emoji, direct bullet points)
  - Focus on 5-10 bullet points highlighting major changes
- **prompts/fork_summary_prompt.txt** - Enhanced fork analysis template with README sections
  - `{parent_readme}` - Always included parent repository README
  - `{fork_readme_section}` - Conditionally included fork README when different
  - `{fork_name}`, `{fork_url}`, `{commits_ahead}`, `{commits_section}` placeholders
  - Concise bullet-point format for terminal display

### State & Configuration
- **state.json** - JSON-based incremental state tracking per repository
  - `last_commit` - SHA of last processed commit
  - `last_release` - ID of last processed release  
  - `processed_forks` - Fork-specific tracking with commit SHAs
- **CLAUDE.md** - Project documentation and AI assistant guidance

### Dependencies
- **requirements.txt** - Minimal dependencies
  - `openai>=1.0.0` - Optional, only needed for OpenAI API provider
  - Core functionality uses Python standard library only

## Key Technical Features

### Dual AI Provider Architecture
- Abstract provider pattern supporting Claude CLI and OpenAI API
- Factory-based provider selection via configuration
- Claude CLI: piped input for large prompts, stream-json parsing with fallbacks
- OpenAI API: direct API calls with proper error handling and tokenization
- Comprehensive debug mode for both providers

### Incremental Processing Intelligence
- Only generates summaries when there are newer commits/releases
- Compares commit SHAs and release IDs to detect actual changes
- Prevents redundant AI API calls and reduces costs
- Sophisticated state comparison logic

### GitHub CLI Integration  
- 5,000/hour rate limits vs 60/hour direct API
- jq filtering for server-side data limiting
- Zero external Python dependencies
- Automatic authentication validation

### Configuration System
- INI-based configuration with comments and sections
- Supports multiple AI providers with separate configurations
- Tilde expansion support (`~/.claude/local/claude`)
- Configurable data limits and timeouts for performance tuning

### Enhanced Fork Analysis with README Intelligence
- **Smart README Detection**: Only fetches fork READMEs when modified in commits ahead
- **Content Comparison**: Normalized text comparison between parent and fork READMEs
- **Conditional Context**: Includes README sections in AI prompts only when meaningful
- **API Optimization**: Fetches parent README once per repository, fork READMEs conditionally
- **Rich AI Context**: Much larger prompts (25k-52k chars) with full README content for better analysis

### Modular Processor Architecture  
- **BaseProcessor**: Template method pattern for consistent workflow
- **RepositoryProcessorMixin**: 95% code reuse between news and fork processors
- **Extensible Design**: Easy to add new processor types (stars, issues, etc.)
- **Shared Components**: GitHubFetcher, SummaryGenerator, Display utilities
- **Clean Separation**: Business logic vs infrastructure concerns

### URL-Based Processing (No Configuration Required)
- **Direct URL Processing**: Process any GitHub repository without adding to configuration
- **Multiple Syntax Options**: Flexible command-line syntax for different use cases
  - `./gh-utils.py <url>` - Process URL with news analysis (default)
  - `./gh-utils.py <url> news` - Explicitly specify news analysis
  - `./gh-utils.py <url> forks` - Process URL for fork analysis
  - `./gh-utils.py news <url>` - Alternative syntax for news
  - `./gh-utils.py forks <url>` - Alternative syntax for forks
- **Temporary Repository Creation**: Creates in-memory repository structure from URLs
- **No State Persistence**: URL-based processing bypasses state tracking
- **Full Feature Support**: All processing features available without configuration setup
- **URL Detection**: Automatic detection of GitHub URLs (https/http/github.com prefixes)
- **Fallback Parsing**: Robust URL parsing with graceful error handling

### State Management
- JSON-based incremental processing per repository
- Tracks last processed commit SHA and release ID
- Fork-specific state tracking with processed fork history
- Optional state persistence via configuration
- Handles first-run and incremental scenarios gracefully
- **URL Processing Exception**: Direct URL processing bypasses state management