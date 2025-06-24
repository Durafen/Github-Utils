# gh-utils: AI-Powered GitHub Repository Monitor

gh-utils turns every repo you watch into a personal GitHub newsfeed—pulling fresh commits & releases and delivering bite-sized AI summaries right in your terminal.

## 🚀 Features

- **Repository News Tracking**: Monitor commits and releases across multiple repositories with individual branch analysis
- **Fork Analysis**: Analyze repository forks that are ahead of their parent with multi-branch support
- **Dual AI Provider Support**: Choose between Claude CLI and OpenAI API
- **Parallel Processing**: 4-worker concurrent repository processing for 70% faster execution
- **Incremental State Management**: Only processes repositories with new activity
- **Terminal-Friendly Output**: Clean, formatted summaries without markdown clutter
- **Thread-Safe Architecture**: Complete display synchronization with per-repository locking
- **Modular Architecture**: Extensible processor pattern for adding new analysis types
- **Cost Tracking**: Monitor AI token usage and estimated costs
- **Enhanced Fork Analysis**: Intelligent README comparison for better fork insights
- **Multi-Branch Analysis**: Separate AI summaries for individual repository branches
- **Repository Aliases**: Process repositories using short aliases instead of full URLs (`./gh-utils.py news ccusage`)
- **Cross-Repository Comparison**: Handles both regular repos and forks with intelligent branching

## 📦 Installation

### Prerequisites

- **Python 3.7+**
- **GitHub CLI** (`gh`) with authentication: `gh auth login`
- **AI Provider**: Either Claude CLI or OpenAI API access

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/gh-utils.git
   cd gh-utils
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure GitHub CLI**
   ```bash
   gh auth login
   ```

4. **Set up configuration**
   ```bash
   cp config.example.txt config.txt
   # Edit config.txt with your AI provider settings
   ```

## ⚙️ Configuration

### AI Provider Setup

#### Option 1: OpenAI API (Recommended)
1. Get your API key from [OpenAI Platform](https://platform.openai.com/api-keys)
2. Edit `config.txt`:
   ```ini
   [ai]
   provider = openai
   
   [openai]
   api_key = your_openai_api_key_here
   model = gpt-4o-mini
   ```

#### Option 2: Claude CLI
1. Install Claude CLI and authenticate
2. Edit `config.txt`:
   ```ini
   [ai]
   provider = claude
   
   [claude]
   claude_cli_path = ~/.claude/local/claude
   ```

### Environment Variables (Optional)
You can use environment variables instead of storing credentials in config files:
```bash
export OPENAI_API_KEY="your_api_key_here"
export CLAUDE_CLI_PATH="/path/to/claude"
```

### Repository Configuration
Add repositories to monitor in `config.txt`:
```ini
[repositories]
my-repo = https://github.com/username/repository
another-repo = https://github.com/org/project
```

## 🔧 Usage

### Basic Commands

```bash
# Track commits and releases (default command)
./gh-utils.py
./gh-utils.py news

# Analyze repository forks
./gh-utils.py forks

# Repository management
./gh-utils.py add <github_url> [name]     # Add repository
./gh-utils.py remove <name>               # Remove repository
./gh-utils.py list                        # List configured repos
./gh-utils.py clear <name>                # Reset tracking state
```

### Alias-Based Processing

Process configured repositories using their alias names:

```bash
# Process repository by alias (defaults to news)
./gh-utils.py ccusage
./gh-utils.py my-repo

# Process specific repository by alias for news
./gh-utils.py news ccusage
./gh-utils.py news my-repo

# Process specific repository by alias for forks
./gh-utils.py forks ccusage
./gh-utils.py forks my-repo

# Alternative syntax: alias first, then processor
./gh-utils.py ccusage news
./gh-utils.py ccusage forks
```

### URL-Based Processing

Process any GitHub repository without adding to configuration:

```bash
# Analyze news for any repository URL
./gh-utils.py https://github.com/owner/repo
./gh-utils.py https://github.com/owner/repo news
./gh-utils.py news https://github.com/owner/repo

# Analyze forks for any repository URL  
./gh-utils.py https://github.com/owner/repo forks
./gh-utils.py forks https://github.com/owner/repo


### Configuration Options

Edit `config.txt` to customize behavior:

```ini
[settings]
# General
debug = true                    # Enable detailed logging
save_state = true              # Enable incremental processing
show_costs = true              # Display AI token costs
timeout = 30                   # AI provider timeout

# News tracking
max_commits = 50               # Maximum commits per repo
max_releases = 10              # Maximum releases per repo
max_branches_per_repo = 5      # Maximum branches to analyze per repo
min_branch_commits = 1         # Minimum commits ahead for branch analysis

# Fork analysis
max_forks = 200                # Maximum forks to analyze
min_commits_ahead = 1          # Minimum commits ahead
fork_activity_days = 90        # Only check recent forks
exclude_private_forks = true   # Skip private forks

# Parallel processing
max_workers = 4                # Number of parallel workers
repo_timeout = 60              # Timeout per repository
```

### Examples

```bash
# First run - processes all recent activity
./gh-utils.py news

# Subsequent runs - only new activity (with save_state=true)
./gh-utils.py news

# Add a new repository with alias
./gh-utils.py add https://github.com/torvalds/linux kernel

# Process specific repository by alias
./gh-utils.py news kernel
./gh-utils.py forks kernel

# Alternative alias syntax
./gh-utils.py kernel           # defaults to news
./gh-utils.py kernel forks     # explicit forks

# Check what forks are ahead of your repositories
./gh-utils.py forks

# Debug mode with detailed output
# Option 1: Command line flag (overrides config.txt)
./gh-utils.py news --debug

# Option 2: Config file setting (persistent)
# Edit config.txt: debug = true
./gh-utils.py news
```

### Sample Output

**News tracking with branch analysis:**
```
--------------------------------------------------------------------------------
📊 my-repo Summary - v2.1.0 (+5) (2h ago) ($<0.001, 1,234 tokens)
--------------------------------------------------------------------------------
- Fixed critical bug in authentication system
- Added new API endpoints for user management
- Updated documentation with latest examples

--------------------------------------------------------------------------------
🌿 feature-branch (+3) (1h ago) ($<0.001, 456 tokens) 
--------------------------------------------------------------------------------
- Implemented advanced caching mechanism for better performance
- Added comprehensive unit tests for new features
```

**Fork analysis:**
```
--------------------------------------------------------------------------------
🍴 user/my-repo-fork (+12) (3h ago)
--------------------------------------------------------------------------------
Branches:
  ├─ main: +8 commits ⭐
  └─ experimental: +4 commits

- Enhanced the core algorithm with machine learning capabilities
- Added Docker support for easier deployment
- Comprehensive refactoring of the authentication module
```

## 🧪 Testing

### Test Core Functionality
```bash
# Test repository management
./gh-utils.py add https://github.com/octocat/Hello-World test-repo
./gh-utils.py list
./gh-utils.py remove test-repo

# Test alias functionality
./gh-utils.py news test-repo     # Process by alias
./gh-utils.py test-repo          # Alias first (defaults to news)
./gh-utils.py test-repo forks    # Alias with explicit processor

# Test both AI providers
./gh-utils.py news

# Test fork analysis
./gh-utils.py forks
```

### Test Configuration
```bash
# Test environment variable override
export OPENAI_API_KEY="your-key"
./gh-utils.py news

# Test first-run setup (if config.txt doesn't exist)
mv config.txt config.txt.backup
./gh-utils.py news  # Should create from config.example.txt
mv config.txt.backup config.txt
```

## 🏗️ Architecture

The project uses a **parallel processor pattern** with extensive code reuse:

- **ParallelBaseProcessor**: Thread-safe base class with 4-worker concurrent processing
- **RepositoryProcessorMixin**: Shared GitHub data processing logic  
- **NewsProcessor & ForksProcessor**: Concrete implementations inheriting from parallel base classes
- **GitHubFetcher**: GitHub CLI integration with comprehensive API access
- **SummaryGenerator**: AI orchestration with template-based prompts
- **ConfigManager**: INI-based configuration with environment variable support

### Parallel Processing Features
- **4-worker ThreadPoolExecutor**: Concurrent repository processing
- **Thread-safe display queue**: Ordered output without race conditions
- **Per-repository locking**: Prevents state corruption
- **Incremental state saving**: Progress preserved on individual repository completion

## 🔒 Security

- **Never commit API keys**: Use `config.txt` (ignored by git) or environment variables
- **Template system**: `config.example.txt` provides safe configuration template
- **Environment variables**: Override config file settings securely
- **Clean git history**: No credentials stored in repository history

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

### Development Setup
```bash
# Enable debug mode for development
# Option 1: Command line flag (temporary)
./gh-utils.py news --debug

# Option 2: Config file setting (persistent)
# Edit config.txt: debug = true

# Test with timeout for development
timeout 30 ./gh-utils.py news --debug
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🐛 Troubleshooting

### Common Issues

**"GitHub CLI not found"**
- Install GitHub CLI: `brew install gh` (macOS) or visit [cli.github.com](https://cli.github.com)
- Authenticate: `gh auth login`

**"OpenAI API key invalid"**
- Verify your API key at [OpenAI Platform](https://platform.openai.com/api-keys)
- Check environment variable: `echo $OPENAI_API_KEY`

**"No repositories configured"**
- Add repositories: `./gh-utils.py add <github_url>`
- Check config: `./gh-utils.py list`

**"Permission denied"**
- Make script executable: `chmod +x gh-utils.py`

### Debug Mode
Enable detailed logging in two ways:
- **Command line**: `./gh-utils.py news --debug` (overrides config.txt)
- **Config file**: Set `debug = true` in config.txt (persistent)

Debug output includes:
- GitHub API calls and responses
- AI prompt details and token usage
- State management operations
- Cost calculations

## 📊 Cost Information

The tool tracks AI token usage and provides cost estimates:
- **OpenAI GPT-4o-mini**: ~$0.15/$0.60 per 1M tokens (input/output)
- **Claude Sonnet 4**: ~$3/$15 per 1M tokens (input/output)

Enable cost tracking with `show_costs = true` in config.txt.