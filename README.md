# gh-utils: AI-Powered GitHub Repository Monitor

An intelligent GitHub repository monitoring tool that generates AI-powered summaries of repository activity using Claude CLI or OpenAI API.

## 🚀 Features

- **Repository News Tracking**: Monitor commits and releases across multiple repositories
- **Fork Analysis**: Analyze repository forks that are ahead of their parent
- 
- **Dual AI Provider Support**: Choose between Claude CLI and OpenAI API
- **Incremental State Management**: Only processes repositories with new activity
- **Terminal-Friendly Output**: Clean, formatted summaries without markdown clutter
- **Modular Architecture**: Extensible processor pattern for adding new analysis types
- **Cost Tracking**: Monitor AI token usage and estimated costs
- **Enhanced Fork Analysis**: Intelligent README comparison for better fork insights

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
max_commits = 10               # Maximum commits per repo
max_releases = 10              # Maximum releases per repo

# Fork analysis
max_forks = 200                # Maximum forks to analyze
min_commits_ahead = 1          # Minimum commits ahead
fork_activity_days = 90        # Only check recent forks
exclude_private_forks = true   # Skip private forks
```

### Examples

```bash
# First run - processes all recent activity
./gh-utils.py news

# Subsequent runs - only new activity (with save_state=true)
./gh-utils.py news

# Add a new repository
./gh-utils.py add https://github.com/torvalds/linux kernel

# Check what forks are ahead of your repositories
./gh-utils.py forks

# Debug mode with detailed output
# (set debug=true in config.txt first)
./gh-utils.py news
```

## 🧪 Testing

### Test Core Functionality
```bash
# Test repository management
./gh-utils.py add https://github.com/octocat/Hello-World test-repo
./gh-utils.py list
./gh-utils.py remove test-repo

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

The project uses a **modular processor pattern** with extensive code reuse:

- **BaseProcessor**: Abstract base class for repository processing workflow
- **RepositoryProcessorMixin**: Shared GitHub data processing logic  
- **NewsProcessor & ForksProcessor**: Concrete implementations inheriting from base classes
- **GitHubFetcher**: GitHub CLI integration with comprehensive API access
- **SummaryGenerator**: AI orchestration with template-based prompts
- **ConfigManager**: INI-based configuration with environment variable support

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
# Edit config.txt: debug = true

# Test with timeout for development
timeout 30 ./gh-utils.py news
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
Enable detailed logging by setting `debug = true` in config.txt to see:
- GitHub API calls and responses
- AI prompt details and token usage
- State management operations
- Cost calculations

## 📊 Cost Information

The tool tracks AI token usage and provides cost estimates:
- **OpenAI GPT-4o-mini**: ~$0.15/$0.60 per 1M tokens (input/output)
- **Claude Sonnet 4**: ~$3/$15 per 1M tokens (input/output)

Enable cost tracking with `show_costs = true` in config.txt.