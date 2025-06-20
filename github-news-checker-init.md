# GitHub News Summary App - Detailed Implementation Plan

## Architecture Overview

```
github_news_summary/
├── main.py                  # Entry point
├── config.json              # Repository list
├── state.json               # Track last checked commits
├── modules/
│   ├── __init__.py
│   ├── github_fetcher.py    # GitHub API interaction
│   ├── summary_generator.py # Claude CLI integration
│   ├── display.py           # Terminal output formatting
│   └── config_manager.py    # JSON file handling
└── tests/
    ├── test_github_fetcher.py
    ├── test_summary_generator.py
    └── test_config_manager.py
```

## Core Components

### 1. Config Manager (`config_manager.py`)
```python
class ConfigManager:
    def __init__(self, config_path='config.json', state_path='state.json'):
        self.config_path = config_path
        self.state_path = state_path
    
    def load_repositories(self):
        """Load repository list from config.json"""
        # Returns: [{"url": "https://github.com/owner/repo", "name": "repo"}]
    
    def load_state(self):
        """Load last checked commits from state.json"""
        # Returns: {"owner/repo": {"last_commit": "sha", "last_check": "timestamp"}}
    
    def save_state(self, state_data):
        """Save updated state back to state.json"""
```

### 2. GitHub Fetcher (`github_fetcher.py`)
```python
import subprocess
import json
import re

class GitHubFetcher:
    def __init__(self):
        """GitHub CLI fetcher - uses gh command for API access"""
        # Check if gh is authenticated
        self._check_gh_auth()
    
    def _check_gh_auth(self):
        """Verify gh CLI is authenticated"""
        result = subprocess.run(['gh', 'auth', 'status'], 
                               capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError("GitHub CLI not authenticated. Run 'gh auth login'")
    
    def extract_owner_repo(self, url):
        """Extract owner/repo from GitHub URL"""
        # "https://github.com/ryoppippi/ccusage" -> ("ryoppippi", "ccusage")
        match = re.match(r'https://github.com/([^/]+)/([^/]+)', url)
        if match:
            return match.group(1), match.group(2)
        raise ValueError(f"Invalid GitHub URL: {url}")
    
    def get_commits(self, owner, repo, since=None):
        """Fetch commits using gh CLI"""
        cmd = ['gh', 'api', f'repos/{owner}/{repo}/commits']
        if since:
            cmd.append(f'?since={since}&per_page=100')
        else:
            cmd.append('?per_page=10')
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Failed to fetch commits: {result.stderr}")
        
        return json.loads(result.stdout)
    
    def get_releases(self, owner, repo):
        """Fetch releases using gh CLI"""
        cmd = ['gh', 'api', f'repos/{owner}/{repo}/releases', '--jq', '.[:10]']
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Failed to fetch releases: {result.stderr}")
        
        return json.loads(result.stdout) if result.stdout else []
    
    def get_latest_commit_sha(self, owner, repo):
        """Get SHA of the latest commit using gh CLI"""
        cmd = ['gh', 'api', f'repos/{owner}/{repo}/commits', 
               '--jq', '.[0].sha', '-H', 'per_page=1']
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Failed to fetch latest commit: {result.stderr}")
        
        return result.stdout.strip()
```

### 3. Summary Generator (`summary_generator.py`)
```python
class SummaryGenerator:
    def __init__(self):
        self.claude_cmd = "claude -p"
    
    def generate_summary(self, repo_data):
        """Use Claude CLI to generate summary"""
        prompt = self._build_prompt(repo_data)
        summary = self._call_claude(prompt)
        return summary
    
    def _build_prompt(self, repo_data):
        """Build prompt for Claude with commit/release info"""
        # Include: repo name, new commits, new releases
    
    def _call_claude(self, prompt):
        """Execute Claude CLI with subprocess"""
        # Use: subprocess.run(['claude', '-p', prompt])
```

### 4. Display Module (`display.py`)
```python
class TerminalDisplay:
    def __init__(self):
        # Use rich/colorama for pretty output
    
    def display_summary(self, repo_name, summary):
        """Display formatted summary with colors and borders"""
    
    def display_loading(self, message):
        """Show loading spinner/progress"""
    
    def display_error(self, error_msg):
        """Display error messages"""
```

### 5. Main Script (`main.py`)
```python
def main():
    # 1. Load configuration and state
    config_manager = ConfigManager()
    repos = config_manager.load_repositories()
    state = config_manager.load_state()
    
    # 2. Initialize components
    fetcher = GitHubFetcher()  # No API token needed - uses gh CLI auth
    generator = SummaryGenerator()
    display = TerminalDisplay()
    
    # 3. Process each repository
    for repo in repos:
        display.display_loading(f"Processing {repo['name']}...")
        
        # Extract owner/repo from URL
        owner, repo_name = fetcher.extract_owner_repo(repo['url'])
        
        # Get last checked commit
        last_commit = state.get(f"{owner}/{repo_name}", {}).get('last_commit')
        
        # Fetch new data
        commits = fetcher.get_commits(owner, repo_name, since=last_commit)
        releases = fetcher.get_releases(owner, repo_name)
        
        # Generate summary if there are updates
        if commits or releases:
            repo_data = {
                'name': repo['name'],
                'commits': commits,
                'releases': releases
            }
            summary = generator.generate_summary(repo_data)
            display.display_summary(repo['name'], summary)
            
            # Update state
            latest_sha = fetcher.get_latest_commit_sha(owner, repo_name)
            state[f"{owner}/{repo_name}"] = {
                'last_commit': latest_sha,
                'last_check': datetime.now().isoformat()
            }
    
    # 4. Save updated state
    config_manager.save_state(state)
```

## Configuration Files

### `config.json`
```json
{
  "repositories": [
    {
      "url": "https://github.com/ryoppippi/ccusage",
      "name": "ccusage"
    }
  ]
}
```

### `state.json`
```json
{
  "ryoppippi/ccusage": {
    "last_commit": "abc123...",
    "last_check": "2025-06-20T10:00:00"
  }
}
```

## Test Strategy

### Test Cases

1. **Config Manager Tests**
   - Test loading valid config.json
   - Test handling missing config.json
   - Test loading/saving state.json
   - Test handling corrupted JSON files

2. **GitHub Fetcher Tests**
   - Test URL parsing (extract owner/repo)
   - Test gh CLI command execution with mock subprocess
   - Test gh auth verification
   - Test handling gh CLI errors
   - Test commit fetching with/without 'since' parameter
   - Test JSON parsing from gh output

3. **Summary Generator Tests**
   - Test prompt building with various data
   - Test Claude CLI command execution
   - Test handling Claude CLI errors
   - Test parsing Claude output

4. **Integration Tests**
   - Test full flow with mock GitHub API
   - Test state persistence across runs
   - Test handling multiple repositories
   - Test error recovery

5. **Manual Test Checklist**
   - [ ] Run with empty state.json (first run)
   - [ ] Run with existing state.json (subsequent runs)
   - [ ] Test with repository that has no new commits
   - [ ] Test with repository that has new commits and releases
   - [ ] Test with invalid GitHub URL
   - [ ] Test with private repository (auth required)
   - [ ] Test Claude CLI integration
   - [ ] Test terminal output formatting

## MVP Implementation Focus

For the MVP, focus on:
1. GitHub CLI integration for commits and releases
2. Simple Claude CLI integration without error handling
3. Basic terminal output (no fancy formatting)
4. JSON file handling for config and state
5. Single repository processing (ccusage)

## Key Advantages of GitHub CLI Approach
- **No API rate limiting concerns** - Uses your authenticated session (5,000/hour)
- **No external Python dependencies** - Just subprocess and built-in modules
- **Richer data** - Full commit details including verification, signatures, parent commits
- **Simpler error handling** - gh CLI provides clear error messages
- **Automatic authentication** - Uses existing gh auth setup

## Dependencies

```requirements.txt
# No external dependencies required!
# GitHub CLI (gh) must be installed and authenticated
```

## Environment Setup
```bash
# Install GitHub CLI if not already installed
# macOS: brew install gh
# Linux: See https://github.com/cli/cli#installation

# Authenticate with GitHub (one-time setup)
gh auth login
```

## Usage
```bash
python main.py
```