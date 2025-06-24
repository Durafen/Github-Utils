import subprocess
import json
import re
import os


class GitHubFetcher:
    def __init__(self, debug_logger=None):
        """GitHub CLI fetcher - uses gh command for API access"""
        self.debug_logger = debug_logger
        self._setup_token_cache()
        self._check_gh_auth()
    
    def _setup_token_cache(self):
        """Enhanced token caching with validation and proper error handling"""
        try:
            result = subprocess.run(['gh', 'auth', 'token'], 
                                   capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                token = result.stdout.strip()
                if token and self._validate_token(token):
                    os.environ['GH_TOKEN'] = token
                    if self.debug_logger:
                        self.debug_logger.debug("✅ Token caching successful")
                else:
                    if self.debug_logger:
                        self.debug_logger.debug("⚠️  Token validation failed - using normal auth")
            else:
                if self.debug_logger:
                    self.debug_logger.debug(f"⚠️  gh auth token failed: {result.stderr}")
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, OSError) as e:
            if self.debug_logger:
                self.debug_logger.debug(f"⚠️  Token caching failed: {e}")
            # Fallback to normal auth without caching
    
    def _validate_token(self, token):
        """Validate token works with a lightweight API call"""
        try:
            # Quick validation - check if token allows basic API access
            result = subprocess.run(['gh', 'api', 'user'], 
                                   capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, OSError):
            return False
    
    def _check_gh_auth(self):
        """Verify gh CLI is authenticated"""
        result = subprocess.run(['gh', 'auth', 'status'], 
                               capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError("GitHub CLI not authenticated. Run 'gh auth login'")
    
    def _run_gh_command(self, cmd, parse_json=True, timeout=30):
        """Run gh command with error handling and optional JSON parsing"""
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            raise RuntimeError(f"GitHub CLI command timed out after {timeout}s: {' '.join(cmd)}")
        
        if result.returncode != 0:
            raise RuntimeError(f"GitHub CLI command failed: {result.stderr}")
        
        if parse_json and result.stdout.strip():
            return json.loads(result.stdout)
        return result.stdout if not parse_json else []
    
    def _run_gh_command_multiline_json(self, cmd, timeout=30):
        """Run gh command and parse multiple JSON objects (one per line)"""
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            return []  # Return empty list for timeout instead of raising exception
        
        if result.returncode != 0:
            return []  # Return empty list instead of raising exception
        
        objects = []
        if result.stdout.strip():
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    try:
                        objects.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue  # Skip invalid JSON lines
        return objects
    
    def extract_owner_repo(self, url):
        """Extract owner/repo from GitHub URL"""
        match = re.match(r'https://github.com/([^/]+)/([^/]+)', url)
        if match:
            return match.group(1), match.group(2)
        raise ValueError(f"Invalid GitHub URL: {url}")
    
    def get_commits(self, owner, repo, since=None, limit=10, branch=None):
        """Fetch commits using gh CLI"""
        if branch:
            endpoint = f'repos/{owner}/{repo}/commits?sha={branch}&per_page={limit}'
        else:
            endpoint = f'repos/{owner}/{repo}/commits?per_page={limit}'
        
        cmd = ['gh', 'api', endpoint]
        if since:
            cmd.extend(['--jq', f'map(select(.sha != "{since}"))[:{limit}]'])
        else:
            cmd.extend(['--jq', f'.[:{limit}]'])
        
        return self._run_gh_command(cmd)
    
    def get_releases(self, owner, repo, limit=5):
        """Fetch releases using gh CLI"""
        cmd = ['gh', 'api', f'repos/{owner}/{repo}/releases?per_page={limit}', '--jq', f'.[:{limit}]']
        return self._run_gh_command(cmd)
    
    def get_latest_commit_sha(self, owner, repo):
        """Get SHA of the latest commit using gh CLI"""
        cmd = ['gh', 'api', f'repos/{owner}/{repo}/commits', '--jq', '.[0].sha']
        result = self._run_gh_command(cmd, parse_json=False)
        return result.strip().replace('"', '')
    
    def get_latest_commit_timestamp(self, owner, repo, branch=None):
        """Get timestamp of the latest commit using gh CLI"""
        if branch:
            cmd = ['gh', 'api', f'repos/{owner}/{repo}/commits/{branch}', '--jq', '.commit.author.date']
        else:
            cmd = ['gh', 'api', f'repos/{owner}/{repo}/commits', '--jq', '.[0].commit.author.date']
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
            try:
                cmd = ['gh', 'api', f'repos/{owner}/{repo}/tags', '--jq', '.[0].name']
                result = self._run_gh_command(cmd, parse_json=False)
                if result.strip():
                    return result.strip().replace('"', '')
            except RuntimeError:
                pass
            
            return None
        except Exception:
            return None
    
    def get_forks(self, owner, repo, limit=20):
        """Get active forks list with basic info using gh CLI"""
        cmd = ['gh', 'api', f'repos/{owner}/{repo}/forks?per_page={limit}', 
               '--jq', f'.[:{limit}] | .[] | {{name, full_name, owner: .owner.login, default_branch, updated_at, private}}']
        
        return self._run_gh_command_multiline_json(cmd)

    
    def get_readme(self, owner, repo):
        """Get README content for repository using gh CLI"""
        # Try common README filenames
        readme_files = ['README.md', 'README.rst', 'README.txt', 'README', 'readme.md', 'readme.rst', 'readme.txt', 'readme']
        
        for filename in readme_files:
            try:
                cmd = ['gh', 'api', f'repos/{owner}/{repo}/contents/{filename}', '--jq', '.content']
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
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
            except (subprocess.TimeoutExpired, Exception):
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
    
    def generate_readme_diff(self, parent_readme, fork_readme):
        """Generate unified diff showing what changed with context"""
        if parent_readme is None and fork_readme is None:
            return "No README changes."
        
        if parent_readme is None:
            return "Fork added README (parent has no README)."
        
        if fork_readme is None:
            return "Fork removed README."
        
        # Normalize content for comparison
        parent_normalized = parent_readme.strip().replace('\r\n', '\n').replace('\r', '\n')
        fork_normalized = fork_readme.strip().replace('\r\n', '\n').replace('\r', '\n')
        
        if parent_normalized == fork_normalized:
            return "No README changes."
        
        # Use difflib for proper sequential diff (not set-based)
        import difflib
        
        parent_lines = parent_normalized.splitlines()
        fork_lines = fork_normalized.splitlines()
        
        # Generate diff with NO context to minimize output
        diff = list(difflib.unified_diff(
            parent_lines,
            fork_lines,
            fromfile='parent/README',
            tofile='fork/README',
            lineterm='',
            n=0  # No context lines
        ))
        
        if not diff:
            return "No README changes."
        
        # Extract ONLY actual changes (+ and - lines), no context, no headers
        changes = []
        for line in diff:
            if line.startswith('+++') or line.startswith('---') or line.startswith('@@'):
                continue  # Skip all headers and metadata
            elif line.startswith('-') and len(line.strip()) > 1:
                changes.append(line)
            elif line.startswith('+') and len(line.strip()) > 1:
                changes.append(line)
            # Skip context lines (starting with ' ')
        
        if not changes:
            return "No significant README changes."
        
        # Return all changes without limiting
        return '\n'.join(changes)
    
    def get_fork_branches(self, fork_owner, fork_repo, limit=None):
        """Get all branches for a fork repository using gh CLI"""
        return self.get_repository_branches(fork_owner, fork_repo, limit)
    
    def get_repository_branches(self, owner, repo, limit=None):
        """Get all branches for any repository using gh CLI"""
        cmd = ['gh', 'api', f'repos/{owner}/{repo}/branches']
        if limit:
            cmd.extend(['--jq', f'.[:{limit}] | .[] | {{name, commit: {{sha, url}}, protected}}'])
        else:
            cmd.extend(['--jq', '.[] | {name, commit: {sha, url}, protected}'])
        
        return self._run_gh_command_multiline_json(cmd)
    
    def compare_branch_with_parent(self, parent_owner, parent_repo, parent_branch, fork_owner, fork_repo, fork_branch):
        """Compare specific fork branch with specific parent branch using gh CLI"""
        cmd = ['gh', 'api', f'repos/{parent_owner}/{parent_repo}/compare/{parent_branch}...{fork_owner}:{fork_repo}:{fork_branch}',
               '--jq', '{ahead_by, behind_by, status, commits: [.commits[] | {sha: .sha[0:7], message: .commit.message, author: .commit.author}], files: [.files[] | .filename]}']
        
        try:
            return self._run_gh_command(cmd)
        except RuntimeError:
            # Branch comparison can fail for various reasons
            return {'ahead_by': 0, 'behind_by': 0, 'status': 'error', 'commits': [], 'files': []}
    
    
    def get_default_branch(self, owner, repo):
        """Get the default branch for a repository"""
        cmd = ['gh', 'api', f'repos/{owner}/{repo}', '--jq', '.default_branch']
        try:
            result = self._run_gh_command(cmd, parse_json=False)
            return result.strip().replace('"', '')
        except RuntimeError:
            return 'main'  # Fallback to 'main' if we can't determine
    
    def get_branch_commits(self, owner, repo, branch_name, since=None, limit=10):
        """Get commits for a specific branch"""
        cmd = ['gh', 'api', f'repos/{owner}/{repo}/commits', '--field', f'sha={branch_name}']
        if since:
            cmd.extend(['--jq', f'map(select(.sha != "{since}"))[:{limit}]'])
        else:
            cmd.extend(['--jq', f'.[:{limit}]'])
        
        return self._run_gh_command(cmd)
    
    def get_branch_commits_since_base(self, owner, repo, branch, base_branch, limit=None):
        """Get commits in branch that are ahead of base branch (adaptive for forks/non-forks)"""
        is_fork, parent_owner, parent_name = self.get_fork_info(owner, repo)
        
        if limit:
            # Filter out merge commits (parents.length > 1) for cleaner branch analysis
            jq_filter = f'.commits | map(select(.parents | length == 1))[:{limit}] | map({{sha: .sha, commit: {{message: .commit.message, author: .commit.author, committer: .commit.committer}}}})'
        else:
            jq_filter = '.commits | map(select(.parents | length == 1)) | map({sha: .sha, commit: {message: .commit.message, author: .commit.author, committer: .commit.committer}})'
        
        if is_fork:
            # Cross-repository comparison for forks
            cmd = ['gh', 'api', f'repos/{parent_owner}/{parent_name}/compare/{base_branch}...{owner}:{repo}:{branch}', '--jq', jq_filter]
        else:
            # Same-repository comparison for non-forks
            cmd = ['gh', 'api', f'repos/{owner}/{repo}/compare/{base_branch}...{branch}', '--jq', jq_filter]
        
        return self._run_gh_command(cmd)

    def get_fork_info(self, owner, repo):
        """Check if repository is a fork and get parent info"""
        cmd = ['gh', 'api', f'repos/{owner}/{repo}', '--jq', '{fork: .fork, parent: .parent}']
        result = self._run_gh_command(cmd)
        
        is_fork = result.get('fork', False)
        parent = result.get('parent')
        
        if is_fork and parent:
            return True, parent['owner']['login'], parent['name']
        return False, None, None

    def get_branch_comparison(self, owner, repo, base_branch, compare_branch):
        """Adaptive branch comparison: cross-repo for forks, same-repo for non-forks"""
        is_fork, parent_owner, parent_name = self.get_fork_info(owner, repo)
        
        try:
            if is_fork:
                # Cross-repository comparison for forks (like forks module)
                cmd = ['gh', 'api', f'repos/{parent_owner}/{parent_name}/compare/{base_branch}...{owner}:{repo}:{compare_branch}',
                       '--jq', '{ahead_by: .ahead_by, behind_by: .behind_by}']
            else:
                # Same-repository comparison for non-forks
                cmd = ['gh', 'api', f'repos/{owner}/{repo}/compare/{base_branch}...{compare_branch}',
                       '--jq', '{ahead_by: .ahead_by, behind_by: .behind_by}']
            
            return self._run_gh_command(cmd)
        except RuntimeError as e:
            # Handle orphan branches (no common ancestor) - treat as independent branches
            if "No common ancestor" in str(e):
                return {'ahead_by': -1, 'behind_by': 0, 'is_orphan': True}
            # Other errors - treat as no difference
            return {'ahead_by': 0, 'behind_by': 0}

    def get_branch_shas_only(self, owner, repo, limit=None):
        """Get lightweight branch list with only names and SHAs for performance optimization"""
        cmd = ['gh', 'api', f'repos/{owner}/{repo}/branches']
        if limit:
            cmd.extend(['--jq', f'.[:{limit}] | .[] | {{name, commit: {{sha}}}}'])
        else:
            cmd.extend(['--jq', '.[] | {name, commit: {sha}}'])
        
        return self._run_gh_command_multiline_json(cmd)

    def get_fork_last_commits(self, owner, repo, limit=None):
        """Get fork list with their default branch SHAs only for performance optimization"""
        per_page = limit or 20
        cmd = ['gh', 'api', f'repos/{owner}/{repo}/forks?per_page={per_page}']
        if limit:
            cmd.extend(['--jq', f'.[:{limit}] | .[] | {{owner: .owner.login, name, full_name, default_branch, updated_at, private}}'])
        else:
            cmd.extend(['--jq', '.[] | {owner: .owner.login, name, full_name, default_branch, updated_at, private}'])
        
        return self._run_gh_command_multiline_json(cmd)


    def get_current_main_sha(self, owner, repo):
        """Get current main/default branch SHA (lightweight check)"""
        default_branch = self.get_default_branch(owner, repo)
        cmd = ['gh', 'api', f'repos/{owner}/{repo}/branches/{default_branch}', '--jq', '.commit.sha']
        try:
            result = self._run_gh_command(cmd, parse_json=False)
            return result.strip().replace('"', '')
        except RuntimeError:
            return None

