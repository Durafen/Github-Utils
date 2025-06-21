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
    
    def _run_gh_command(self, cmd, parse_json=True):
        """Run gh command with error handling and optional JSON parsing"""
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"GitHub CLI command failed: {result.stderr}")
        
        if parse_json and result.stdout.strip():
            return json.loads(result.stdout)
        return result.stdout if not parse_json else []
    
    def extract_owner_repo(self, url):
        """Extract owner/repo from GitHub URL"""
        match = re.match(r'https://github.com/([^/]+)/([^/]+)', url)
        if match:
            return match.group(1), match.group(2)
        raise ValueError(f"Invalid GitHub URL: {url}")
    
    def get_commits(self, owner, repo, since=None, limit=10):
        """Fetch commits using gh CLI"""
        cmd = ['gh', 'api', f'repos/{owner}/{repo}/commits']
        if since:
            cmd.extend(['--jq', f'map(select(.sha != "{since}"))[:{limit}]'])
        else:
            cmd.extend(['--jq', f'.[:{limit}]'])
        
        return self._run_gh_command(cmd)
    
    def get_releases(self, owner, repo, limit=5):
        """Fetch releases using gh CLI"""
        cmd = ['gh', 'api', f'repos/{owner}/{repo}/releases', '--jq', f'.[:{limit}]']
        return self._run_gh_command(cmd)
    
    def get_latest_commit_sha(self, owner, repo):
        """Get SHA of the latest commit using gh CLI"""
        cmd = ['gh', 'api', f'repos/{owner}/{repo}/commits', '--jq', '.[0].sha']
        result = self._run_gh_command(cmd, parse_json=False)
        return result.strip().replace('"', '')
    
    def get_latest_version(self, owner, repo):
        """Get the latest version from releases, fallback to tags"""
        try:
            # Try releases first
            releases = self.get_releases(owner, repo, limit=1)
            if releases and releases[0].get('tag_name'):
                return releases[0]['tag_name']
            
            # Fallback to tags
            cmd = ['gh', 'api', f'repos/{owner}/{repo}/tags', '--jq', '.[0].name']
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip().replace('"', '')
            
            return None
        except Exception:
            return None
    
    def get_forks(self, owner, repo, limit=20):
        """Get active forks list with basic info using gh CLI"""
        cmd = ['gh', 'api', f'repos/{owner}/{repo}/forks', 
               '--jq', f'.[:{limit}] | .[] | {{name, full_name, owner: .owner.login, default_branch, updated_at, private}}']
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Failed to fetch forks: {result.stderr}")
        
        # Parse multiple JSON objects on separate lines
        forks = []
        if result.stdout.strip():
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    forks.append(json.loads(line))
        return forks

    def compare_fork_with_parent(self, parent_owner, parent_repo, fork_owner, fork_repo, fork_branch='main'):
        """Compare fork with parent repository using gh CLI"""
        cmd = ['gh', 'api', f'repos/{parent_owner}/{parent_repo}/compare/{fork_branch}...{fork_owner}:{fork_repo}:{fork_branch}',
               '--jq', '{ahead_by, behind_by, status, commits: [.commits[] | {sha: .sha[0:7], message: .commit.message, author: .commit.author}], files: [.files[] | .filename]}']
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            # Fork comparison can fail for various reasons (branch mismatch, private repos, etc.)
            # Return empty result rather than failing completely
            return {'ahead_by': 0, 'behind_by': 0, 'status': 'error', 'commits': [], 'files': []}
        
        return json.loads(result.stdout) if result.stdout.strip() else {}

    def get_fork_commits(self, fork_owner, fork_repo, limit=10):
        """Get commit details for fork (reuses existing get_commits pattern)"""
        return self.get_commits(fork_owner, fork_repo, limit=limit)
    
    def get_readme(self, owner, repo):
        """Get README content for repository using gh CLI"""
        # Try common README filenames
        readme_files = ['README.md', 'README.rst', 'README.txt', 'README', 'readme.md', 'readme.rst', 'readme.txt', 'readme']
        
        for filename in readme_files:
            try:
                cmd = ['gh', 'api', f'repos/{owner}/{repo}/contents/{filename}', '--jq', '.content']
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0 and result.stdout.strip():
                    # Content is base64 encoded, decode it
                    import base64
                    content = result.stdout.strip().replace('"', '')
                    try:
                        decoded_content = base64.b64decode(content).decode('utf-8')
                        return decoded_content
                    except Exception:
                        # If decoding fails, return the encoded content
                        return content
            except Exception:
                continue
        
        return None  # No README found
    
    def readme_was_modified(self, comparison_result):
        """Check if README files were modified in the comparison result"""
        if not comparison_result or 'files' not in comparison_result:
            return False
        
        readme_patterns = ['readme', 'README']
        files = comparison_result.get('files', [])
        
        for file in files:
            file_lower = file.lower()
            for pattern in readme_patterns:
                if pattern.lower() in file_lower:
                    return True
        
        return False
    
    def compare_readme_content(self, parent_readme, fork_readme):
        """Compare README content between parent and fork"""
        if parent_readme is None and fork_readme is None:
            return False  # Both are None, no difference
        
        if parent_readme is None or fork_readme is None:
            return True  # One is None, different
        
        # Normalize content for comparison (strip whitespace, normalize line endings)
        parent_normalized = parent_readme.strip().replace('\r\n', '\n').replace('\r', '\n')
        fork_normalized = fork_readme.strip().replace('\r\n', '\n').replace('\r', '\n')
        
        return parent_normalized != fork_normalized