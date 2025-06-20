import subprocess
import json
import re


class GitHubFetcher:
    def __init__(self):
        """GitHub CLI fetcher - uses gh command for API access"""
        self._check_gh_auth()
    
    def _check_gh_auth(self):
        """Verify gh CLI is authenticated"""
        result = subprocess.run(['gh', 'auth', 'status'], 
                               capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError("GitHub CLI not authenticated. Run 'gh auth login'")
    
    def extract_owner_repo(self, url):
        """Extract owner/repo from GitHub URL"""
        match = re.match(r'https://github.com/([^/]+)/([^/]+)', url)
        if match:
            return match.group(1), match.group(2)
        raise ValueError(f"Invalid GitHub URL: {url}")
    
    def get_commits(self, owner, repo, since=None):
        """Fetch commits using gh CLI"""
        cmd = ['gh', 'api', f'repos/{owner}/{repo}/commits']
        if since:
            cmd.extend(['--jq', f'map(select(.sha != "{since}"))[:10]'])
        else:
            cmd.extend(['--jq', '.[:10]'])
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Failed to fetch commits: {result.stderr}")
        
        return json.loads(result.stdout) if result.stdout.strip() else []
    
    def get_releases(self, owner, repo):
        """Fetch releases using gh CLI"""
        cmd = ['gh', 'api', f'repos/{owner}/{repo}/releases', '--jq', '.[:5]']
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Failed to fetch releases: {result.stderr}")
        
        return json.loads(result.stdout) if result.stdout.strip() else []
    
    def get_latest_commit_sha(self, owner, repo):
        """Get SHA of the latest commit using gh CLI"""
        cmd = ['gh', 'api', f'repos/{owner}/{repo}/commits', 
               '--jq', '.[0].sha']
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Failed to fetch latest commit: {result.stderr}")
        
        return result.stdout.strip().replace('"', '')