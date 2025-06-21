# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**gh-utils** is a GitHub repository monitoring tool that generates AI-powered summaries of repository activity. It supports two main operations: tracking commits/releases across repositories (news) and analyzing repository forks that are ahead of their parent (forks). The tool supports both Claude CLI and OpenAI API for generating concise summaries.

## Architecture

The project uses a **modular processor pattern** with extensive code reuse through abstract base classes and mixins:

### Core Architecture Pattern
- **BaseProcessor** (`modules/base_processor.py`): Abstract base class providing common repository processing workflow (load config → process repos → save state)
- **RepositoryProcessorMixin** (`modules/repository_mixin.py`): Shared GitHub data processing logic (URL parsing, state comparisons, incremental updates)
- **Concrete Processors**: NewsProcessor and ForksProcessor inherit from BaseProcessor + Mixin for 95% code reuse

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
2. **BaseProcessor.execute()**: Template method loads config → processes each repo → saves state
3. **Concrete _process_repository()**: Processor-specific logic (news: commits/releases, forks: fork analysis)
4. **Shared Components**: GitHubFetcher, SummaryGenerator, TerminalDisplay handle implementation details

## Key Technical Decisions

**Processor Pattern with Mixins**: Eliminates 80% code duplication between news and forks processing. Adding new repository processors requires only implementing `_process_repository()` method.

**Template-Based AI Integration**: PromptManager loads external templates (`prompts/*.txt`) with placeholder substitution. SummaryGenerator detects context (news vs forks) and builds appropriate prompts automatically.

**GitHub CLI with jq Filtering**: Uses `gh api` commands with server-side jq filtering for 5,000/hour rate limits. Handles multiple JSON objects per line for fork listings.

**Incremental State Management**: JSON-based state tracking per repository with configurable persistence. Only processes repositories with actual newer content (commit SHA/release ID comparison).

## Commands

### Running the Application
```bash
# News: track commits and releases (default)
./gh-utils.py
./gh-utils.py news

# Forks: analyze repository forks ahead of parent
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
./gh-utils.py news    # Shows prompt details, API calls, token usage

# Enable cost tracking (edit config.txt: show_costs = true)
./gh-utils.py news    # Shows AI token usage and estimated costs

# Test different AI providers (edit config.txt)
# provider = openai (requires api_key)
# provider = claude (requires claude_cli_path)
./gh-utils.py news

# Test without state persistence (edit config.txt: save_state = false)
./gh-utils.py news    # Always shows all recent activity

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

## Adding New Repository Processors

The modular architecture makes adding new processors straightforward:

1. **Create Processor Class**: Inherit from `BaseProcessor` and `RepositoryProcessorMixin`
2. **Implement _process_repository()**: Add processor-specific logic for repository analysis
3. **Create Prompt Template**: Add `prompts/{name}_prompt.txt` with placeholders
4. **Update Command Router**: Add processor to `processors` dict in `gh-utils.py`
5. **Add Configuration**: Add processor-specific settings to `config.txt` [settings] section

Example minimal processor:
```python
from .base_processor import BaseProcessor
from .repository_mixin import RepositoryProcessorMixin

class MyProcessor(BaseProcessor, RepositoryProcessorMixin):
    def __init__(self):
        super().__init__(template_name='my_template')
    
    def _process_repository(self, repo):
        owner, repo_name, repo_key = self.extract_repo_info(repo['url'])
        # Custom processing logic here
        # Use self.fetcher, self.generator, self.display
```

## Code Architecture Notes

**Configuration Parsing**: ConfigManager handles inline comments in INI files by splitting on '#' and stripping whitespace. Use `get_setting(key, default)` with defaults for new settings.

**GitHub API Integration**: GitHubFetcher uses subprocess.run with `gh api` commands and jq filtering. Multiple JSON objects per line require line-by-line parsing, not direct json.loads().

**AI Context Detection**: SummaryGenerator automatically detects prompt context by checking for 'fork_name' in repo_data and builds appropriate prompts (news vs forks).

**State Management**: JSON state tracks `last_commit`, `last_release`, and `processed_forks` per repository. Only update state after successful AI generation to prevent skipping on retry.

**Cost Tracking**: CostTracker integrates with AI providers to track token usage and costs. Both Claude CLI (estimated) and OpenAI API (actual) costs are calculated with current pricing: Claude Sonnet 4 ($3/$15 per MTok), OpenAI GPT-4o-mini ($0.15/$0.60 per MTok).

**Debug Infrastructure**: DebugLogger provides performance-optimized debug output with cached settings. Use `debug_api_call()` for API operations and `debug_tokens()` for cost analysis.

**Enhanced Fork Analysis**: Fork processor includes intelligent README comparison - fetches parent README once, fork READMs conditionally when modified, and provides rich AI context with full README content for superior analysis.

**Error Recovery**: BaseProcessor continues processing remaining repositories when individual repos fail. Use try/catch around individual repo processing, not entire command execution.

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