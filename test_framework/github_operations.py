#!/usr/bin/env python3
"""
GitHub Operations Module for Test Framework
Handles real GitHub repository operations for testing
"""

import subprocess
import tempfile
import os
import shutil
import time
from datetime import datetime
from typing import Dict, Optional, List

# Import test commit patterns
try:
    from .test_commit_patterns import TestCommitPatterns
except ImportError:
    from test_commit_patterns import TestCommitPatterns


class GitHubOperations:
    """Manages real GitHub repository operations for testing"""
    
    def __init__(self, debug=False):
        self.debug = debug
        self.temp_dirs = {}
        self.test_repos = {
            'ant-javacard': 'https://github.com/Durafen/ant-javacard',
            'testing': 'https://github.com/Durafen/testing'
        }
        self._check_github_auth()
    
    def _check_github_auth(self):
        """Verify GitHub CLI authentication and setup git config"""
        try:
            result = self._run_command(['gh', 'auth', 'status'], timeout=10)
            if result.returncode != 0:
                raise RuntimeError("GitHub CLI not authenticated. Run 'gh auth login'")
            
            # Get GitHub token for git operations
            token_result = self._run_command(['gh', 'auth', 'token'], timeout=10)
            if token_result.returncode == 0:
                self.github_token = token_result.stdout.strip()
                if self.debug:
                    print("✅ GitHub CLI authentication verified with token")
            else:
                self.github_token = None
                if self.debug:
                    print("✅ GitHub CLI authentication verified (no token)")
                    
        except Exception as e:
            raise RuntimeError(f"GitHub authentication failed: {e}")
    
    def _run_command(self, cmd: List[str], cwd: Optional[str] = None, timeout: int = 30) -> subprocess.CompletedProcess:
        """Run command with error handling and real-time output"""
        try:
            if self.debug and not ('git' in cmd and 'log' in cmd and '--max-count' in cmd):
                print(f"🔧 Running: {' '.join(cmd)}")
            
            # Use elegant real-time subprocess solution
            captured_lines = []
            with subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                cwd=cwd,
                env={**os.environ, 'PYTHONUNBUFFERED': '1'}
            ) as process:
                
                # Real-time output display and capture
                for line in iter(process.stdout.readline, ''):
                    if self.debug:
                        print(line, end='')
                    captured_lines.append(line)
                
                return_code = process.wait()
            
            # Create CompletedProcess-like object for compatibility
            class CompletedProcessMock:
                def __init__(self, returncode, stdout, stderr):
                    self.returncode = returncode
                    self.stdout = stdout
                    self.stderr = stderr
            
            stdout = ''.join(captured_lines)
            stderr = ""  # Combined with stdout above
            
            if return_code != 0:
                print(f"❌ Command failed with return code: {return_code}")
            
            return CompletedProcessMock(return_code, stdout, stderr)
            
        except Exception as e:
            raise RuntimeError(f"Command execution failed: {e}")
    
    def setup_test_repositories(self) -> bool:
        """Clone test repositories to temporary directories"""
        try:
            for repo_name, repo_url in self.test_repos.items():
                if repo_name not in self.temp_dirs:
                    temp_dir = tempfile.mkdtemp(prefix=f'gh_test_{repo_name}_')
                    
                    # Clone repository
                    result = self._run_command(['git', 'clone', repo_url, temp_dir])
                    if result.returncode != 0:
                        raise RuntimeError(f"Failed to clone {repo_name}: {result.stderr}")
                    
                    # Configure git to use GitHub CLI helper for authentication
                    self._setup_git_auth(temp_dir)
                    
                    self.temp_dirs[repo_name] = temp_dir
                    if self.debug:
                        print(f"✅ Cloned {repo_name} to {temp_dir}")
            
            return True
        except Exception as e:
            print(f"❌ Setup failed: {e}")
            return False
    
    def _setup_git_auth(self, repo_dir: str):
        """Setup git authentication using GitHub CLI"""
        try:
            # Configure git to use GitHub CLI for authentication
            self._run_command(['git', 'config', '--local', 'credential.helper', ''], cwd=repo_dir)
            self._run_command(['git', 'config', '--local', 'credential.https://github.com.helper', '!gh auth git-credential'], cwd=repo_dir)
            
            if self.debug:
                print(f"✅ Configured git authentication for {repo_dir}")
        except Exception as e:
            print(f"⚠️ Git auth setup failed: {e}")
    
    def create_test_commit(self, repo_name: str, branch: Optional[str] = None, 
                          message: Optional[str] = None) -> bool:
        """Create and push a test commit to specified branch"""
        import sys
        import os
        
        if repo_name not in self.temp_dirs:
            print(f"❌ Repository {repo_name} not set up")
            return False
        
        repo_dir = self.temp_dirs[repo_name]
        timestamp = int(time.time())
        
        if not message:
            message = f"Test commit - {datetime.now().isoformat()}"
        
        # Use default branch if none specified
        if not branch:
            # Import GitHubFetcher to get default branch
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from modules.github_fetcher import GitHubFetcher
            
            fetcher = GitHubFetcher()
            repo_url = self.test_repos.get(repo_name)
            owner, repo = repo_url.split('github.com/')[1].split('/')[:2]
            branch = fetcher.get_default_branch(owner, repo)
        
        try:
            # Ensure we're on the correct branch
            self._run_command(['git', 'checkout', branch], cwd=repo_dir)
            
            # Pull latest changes
            self._run_command(['git', 'pull', 'origin', branch], cwd=repo_dir)
            
            # Create test file
            test_file = os.path.join(repo_dir, f'test_{timestamp}.txt')
            with open(test_file, 'w') as f:
                f.write(f"Test content: {message}\nTimestamp: {timestamp}\nBranch: {branch}\n")
            
            # Add and commit
            self._run_command(['git', 'add', test_file], cwd=repo_dir)
            result_commit = self._run_command(['git', 'commit', '-m', message], cwd=repo_dir)
            if result_commit.returncode != 0:
                print(f"❌ Commit failed: {result_commit.stderr}")
                return False
            
            # Push changes
            result_push = self._run_command(['git', 'push', 'origin', branch], cwd=repo_dir)
            if result_push.returncode != 0:
                print(f"❌ Push failed: {result_push.stderr}")
                return False
            
            if self.debug:
                print(f"✅ Created commit on {repo_name}/{branch}: {message}")
            else:
                # Show the actual GitHub repository owner/name
                repo_url = self.test_repos.get(repo_name, '')
                if 'github.com/' in repo_url:
                    repo_path = repo_url.split('github.com/')[-1]
                    if repo_path.endswith('.git'):
                        repo_path = repo_path[:-4]
                    print(f"📝 Commit: {repo_path}/{branch}")
                else:
                    print(f"📝 Commit: {repo_name}/{branch}")
            
            # Small delay to ensure GitHub API reflects the change
            time.sleep(2)
            return True
            
        except Exception as e:
            print(f"❌ Commit creation failed: {e}")
            return False
    
    def _branch_exists_local(self, branch_name: str, repo_dir: str) -> bool:
        """Check if branch exists locally"""
        result = self._run_command(['git', 'branch', '--list', branch_name], cwd=repo_dir)
        return result.stdout.strip() != ''

    def _branch_exists_remote(self, branch_name: str, repo_dir: str) -> bool:
        """Check if branch exists on remote"""
        result = self._run_command(['git', 'ls-remote', '--heads', 'origin', branch_name], cwd=repo_dir)
        return result.stdout.strip() != ''
    
    def create_dynamic_test_branch(self, repo_name: str, branch_name: str) -> bool:
        """Create a new branch with specified unique name"""
        if repo_name not in self.temp_dirs:
            print(f"❌ Repository {repo_name} not set up")
            return False
        
        repo_dir = self.temp_dirs[repo_name]
        
        try:
            # Get default branch and checkout/pull
            # Import GitHubFetcher to get default branch
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from modules.github_fetcher import GitHubFetcher
            
            fetcher = GitHubFetcher()
            repo_url = self.test_repos.get(repo_name)
            owner, repo = repo_url.split('github.com/')[1].split('/')[:2]
            default_branch = fetcher.get_default_branch(owner, repo)
            
            self._run_command(['git', 'checkout', default_branch], cwd=repo_dir)
            self._run_command(['git', 'pull', 'origin', default_branch], cwd=repo_dir)
            
            # Check and delete existing branch if it exists
            if self._branch_exists_local(branch_name, repo_dir):
                self._run_command(['git', 'branch', '-D', branch_name], cwd=repo_dir)
            if self._branch_exists_remote(branch_name, repo_dir):
                self._run_command(['git', 'push', 'origin', '--delete', branch_name], cwd=repo_dir)
            
            # Create new branch
            result = self._run_command(['git', 'checkout', '-b', branch_name], cwd=repo_dir)
            if result.returncode != 0:
                print(f"❌ Failed to create branch {branch_name}: {result.stderr}")
                return False
            
            # Push to remote
            push_result = self._run_command(['git', 'push', '-u', 'origin', branch_name], cwd=repo_dir)
            
            if self.debug:
                status = "✅" if push_result.returncode == 0 else "❌"
                print(f"{status} Created NEW branch: {branch_name} on {repo_name}")
            
            return push_result.returncode == 0
            
        except Exception as e:
            print(f"❌ NEW branch creation failed: {e}")
            return False
    
    def get_test_commits_in_history(self, repo_name: str, branch: str = 'main', max_commits: int = 50) -> List[Dict]:
        """Find test commits in repository history using both GitHub API and local git log"""
        test_commits = []
        patterns = TestCommitPatterns()
        
        try:
            # Method 1: Use GitHub API for remote repository
            repo_url = self.test_repos.get(repo_name)
            if repo_url and 'github.com/' in repo_url:
                repo_path = repo_url.split('github.com/')[-1]
                if repo_path.endswith('.git'):
                    repo_path = repo_path[:-4]
                
                # Get commits from GitHub API
                api_result = self._run_command([
                    'gh', 'api', f'repos/{repo_path}/commits',
                    '--jq', f'.[0:{max_commits}][] | {{sha: .sha, message: .commit.message, date: .commit.author.date, author: .commit.author.name}}'
                ])
                
                if api_result.returncode == 0:
                    for line in api_result.stdout.strip().split('\n'):
                        if line.strip():
                            try:
                                import json
                                commit_data = json.loads(line)
                                message = commit_data.get('message', '').strip()
                                
                                if patterns.is_test_commit(message):
                                    test_commits.append({
                                        'sha': commit_data.get('sha'),
                                        'message': message,
                                        'date': commit_data.get('date'),
                                        'author': commit_data.get('author'),
                                        'branch': branch,
                                        'source': 'github_api'
                                    })
                                    
                            except json.JSONDecodeError:
                                continue
            
            # Method 2: Use local git log if repository is cloned
            if repo_name in self.temp_dirs:
                repo_dir = self.temp_dirs[repo_name]
                
                # Checkout the branch first
                self._run_command(['git', 'checkout', branch], cwd=repo_dir)
                self._run_command(['git', 'pull', 'origin', branch], cwd=repo_dir)
                
                # Get commits using git log
                git_result = self._run_command([
                    'git', 'log', f'--max-count={max_commits}', 
                    '--pretty=format:%H|%s|%ai|%an', branch
                ], cwd=repo_dir)
                
                if git_result.returncode == 0:
                    for line in git_result.stdout.strip().split('\n'):
                        if line.strip():
                            parts = line.split('|', 3)
                            if len(parts) >= 4:
                                sha, message, date, author = parts
                                message = message.strip()
                                
                                if patterns.is_test_commit(message):
                                    # Check if we already have this commit from API
                                    existing = next((c for c in test_commits if c['sha'] == sha), None)
                                    if not existing:
                                        test_commits.append({
                                            'sha': sha,
                                            'message': message,
                                            'date': date,
                                            'author': author,
                                            'branch': branch,
                                            'source': 'local_git'
                                        })
            
            if self.debug and test_commits:
                print(f"🔍 Found {len(test_commits)} test commits in {repo_name}/{branch}")
                for commit in test_commits[:5]:  # Show first 5
                    print(f"   📝 {commit['sha'][:8]}: {commit['message']}")
                if len(test_commits) > 5:
                    print(f"   ... and {len(test_commits) - 5} more")
            
            return test_commits
            
        except Exception as e:
            print(f"❌ Error analyzing commit history for {repo_name}/{branch}: {e}")
            return []
    
    def get_all_test_commits(self, repo_name: str) -> Dict[str, List[Dict]]:
        """Get test commits from all branches of a repository"""
        all_commits = {}
        
        try:
            # Get all branches
            branches = self.get_available_branches(repo_name)
            if not branches:
                # Fallback to default branch instead of hardcoded 'main'
                import sys
                import os
                sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                from modules.github_fetcher import GitHubFetcher
                
                fetcher = GitHubFetcher()
                repo_url = self.test_repos.get(repo_name)
                if repo_url:
                    owner, repo = repo_url.split('github.com/')[1].split('/')[:2]
                    default_branch = fetcher.get_default_branch(owner, repo)
                    branches = [default_branch]
                else:
                    branches = ['main']  # Ultimate fallback
            
            for branch in branches:
                commits = self.get_test_commits_in_history(repo_name, branch)
                if commits:
                    all_commits[branch] = commits
            
            if self.debug:
                total_commits = sum(len(commits) for commits in all_commits.values())
                print(f"🔍 Found {total_commits} total test commits across {len(all_commits)} branches in {repo_name}")
            
            return all_commits
            
        except Exception as e:
            print(f"❌ Error getting all test commits for {repo_name}: {e}")
            return {}

    def delete_test_commits_safely(self, repo_name: str, branch: str = 'main', dry_run: bool = False) -> bool:
        """Safely delete test commits from a branch using git reset --hard"""
        if repo_name not in self.temp_dirs:
            print(f"❌ Repository {repo_name} not set up for local operations")
            return False
        
        repo_dir = self.temp_dirs[repo_name]
        patterns = TestCommitPatterns()
        
        try:
            # Checkout the branch and pull latest
            self._run_command(['git', 'checkout', branch], cwd=repo_dir)
            self._run_command(['git', 'pull', 'origin', branch], cwd=repo_dir)
            
            # Get commit history with more details
            git_result = self._run_command([
                'git', 'log', '--max-count=100', 
                '--pretty=format:%H|%s|%ai|%an', branch
            ], cwd=repo_dir)
            
            if git_result.returncode != 0:
                print(f"❌ Failed to get git log for {repo_name}/{branch}")
                return False
            
            commits = []
            for line in git_result.stdout.strip().split('\n'):
                if line.strip():
                    parts = line.split('|', 3)
                    if len(parts) >= 4:
                        sha, message, date, author = parts
                        commits.append({
                            'sha': sha.strip(),
                            'message': message.strip(),
                            'date': date.strip(),
                            'author': author.strip(),
                            'is_test': patterns.is_test_commit(message.strip())
                        })
            
            if not commits:
                if self.debug:
                    print(f"ℹ️  No commits found in {repo_name}/{branch}")
                return True
            
            # Find the first non-test commit (going backwards from HEAD)
            reset_to_sha = None
            test_commits_to_delete = []
            
            for i, commit in enumerate(commits):
                if commit['is_test']:
                    test_commits_to_delete.append(commit)
                else:
                    # Found first non-test commit - this is our reset target
                    reset_to_sha = commit['sha']
                    break
            
            if not test_commits_to_delete:
                if self.debug:
                    print(f"ℹ️  No test commits found to delete in {repo_name}/{branch}")
                return True
            
            if not reset_to_sha:
                # All commits are test commits - this is dangerous, reset to initial commit
                if self.debug:
                    print(f"⚠️  All recent commits are test commits in {repo_name}/{branch}")
                    print(f"   This would delete {len(test_commits_to_delete)} commits")
                    if not dry_run:
                        print(f"   Skipping deletion to avoid destroying repository history")
                return False
            
            if self.debug or dry_run:
                print(f"🗑️  Found {len(test_commits_to_delete)} test commits to delete in {repo_name}/{branch}")
                for commit in test_commits_to_delete[:5]:  # Show first 5
                    print(f"   📝 {commit['sha'][:8]}: {commit['message']}")
                if len(test_commits_to_delete) > 5:
                    print(f"   ... and {len(test_commits_to_delete) - 5} more")
                print(f"🎯 Will reset to: {reset_to_sha[:8]} ({commits[len(test_commits_to_delete)]['message'][:50]}...)")
            
            if dry_run:
                print("🔍 DRY RUN: No actual deletion performed")
                return True
            
            # Perform the actual deletion
            if self.debug:
                print(f"🗑️  Deleting {len(test_commits_to_delete)} test commits from {repo_name}/{branch}")
            
            # First, explicitly remove any test files
            import glob
            test_files = glob.glob(os.path.join(repo_dir, 'test_*.txt'))
            if test_files and self.debug:
                print(f"🗑️  Removing {len(test_files)} test files: {[os.path.basename(f) for f in test_files]}")
                for test_file in test_files:
                    try:
                        # Remove from filesystem
                        os.remove(test_file)
                        # Remove from git index if it was staged
                        self._run_command(['git', 'rm', '--cached', os.path.basename(test_file)], cwd=repo_dir)
                    except FileNotFoundError:
                        pass  # File already deleted
                    except Exception as e:
                        print(f"⚠️  Could not remove test file {test_file}: {e}")
            
            # Reset to the target commit
            reset_result = self._run_command(['git', 'reset', '--hard', reset_to_sha], cwd=repo_dir)
            if reset_result.returncode != 0:
                print(f"❌ Git reset failed: {reset_result.stderr}")
                return False
            
            # Force push to update remote (this is the destructive operation)
            push_result = self._run_command(['git', 'push', '--force-with-lease', 'origin', branch], cwd=repo_dir)
            if push_result.returncode != 0:
                print(f"❌ Force push failed: {push_result.stderr}")
                print(f"   Remote may have been updated by someone else")
                return False
            
            # Verify test files are completely removed
            remaining_test_files = glob.glob(os.path.join(repo_dir, 'test_*.txt'))
            if remaining_test_files and self.debug:
                print(f"⚠️  {len(remaining_test_files)} test files still remain: {[os.path.basename(f) for f in remaining_test_files]}")
            elif self.debug:
                print(f"✅ All test files successfully removed from {repo_name}/{branch}")
            
            if self.debug:
                print(f"✅ Successfully deleted {len(test_commits_to_delete)} test commits from {repo_name}/{branch}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error deleting test commits from {repo_name}/{branch}: {e}")
            return False
    
    def delete_all_test_commits(self, repo_name: str, dry_run: bool = False) -> bool:
        """Delete test commits from all branches of a repository"""
        try:
            branches = self.get_available_branches(repo_name)
            if not branches:
                # Fallback to default branch instead of hardcoded 'main'
                import sys
                import os
                sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                from modules.github_fetcher import GitHubFetcher
                
                fetcher = GitHubFetcher()
                repo_url = self.test_repos.get(repo_name)
                if repo_url:
                    owner, repo = repo_url.split('github.com/')[1].split('/')[:2]
                    default_branch = fetcher.get_default_branch(owner, repo)
                    branches = [default_branch]
                else:
                    branches = ['main']  # Ultimate fallback
            
            overall_success = True
            total_deleted = 0
            
            for branch in branches:
                if self.debug:
                    print(f"\n🔍 Processing branch: {repo_name}/{branch}")
                
                success = self.delete_test_commits_safely(repo_name, branch, dry_run)
                if not success:
                    overall_success = False
                    print(f"⚠️  Failed to clean {repo_name}/{branch}")
            
            if self.debug and overall_success:
                print(f"✅ Completed test commit cleanup for all branches in {repo_name}")
            
            return overall_success
            
        except Exception as e:
            print(f"❌ Error cleaning all test commits from {repo_name}: {e}")
            return False

    def cleanup_test_commits(self, dry_run: bool = False) -> bool:
        """Main method to cleanup test commits from all test repositories"""
        if self.debug:
            print(f"🧹 Starting test commit cleanup {'(DRY RUN)' if dry_run else ''}...")
        
        overall_success = True
        cleanup_summary = {}
        
        try:
            # Ensure repositories are set up
            if not self.setup_test_repositories():
                print("❌ Failed to setup repositories for cleanup")
                return False
            
            # Process each test repository
            for repo_name in self.test_repos.keys():
                if self.debug:
                    print(f"\n🔍 Processing repository: {repo_name}")
                
                repo_success = self.delete_all_test_commits(repo_name, dry_run)
                cleanup_summary[repo_name] = repo_success
                
                if not repo_success:
                    overall_success = False
                    print(f"⚠️  Failed to clean test commits from {repo_name}")
                else:
                    if self.debug:
                        print(f"✅ Successfully cleaned test commits from {repo_name}")
            
            # Summary report
            if self.debug:
                print(f"\n📊 Test Commit Cleanup Summary:")
                print(f"   Overall Success: {'✅' if overall_success else '❌'}")
                for repo, success in cleanup_summary.items():
                    status = "✅" if success else "❌"
                    print(f"   {repo}: {status}")
                
                if dry_run:
                    print(f"🔍 DRY RUN: No actual commits were deleted")
                elif overall_success:
                    print(f"🎉 All test repositories cleaned successfully!")
                else:
                    print(f"⚠️  Some repositories had cleanup failures")
            else:
                # Non-debug mode: show simple one-liner
                if not dry_run:
                    print("🗑️ Cleaning commits, branches, files")
            
            return overall_success
            
        except Exception as e:
            if self.debug:
                print(f"❌ Test commit cleanup failed: {e}")
            return False
    
    def cleanup_test_commits_for_repos(self, repo_names: List[str], dry_run: bool = False) -> bool:
        """Cleanup test commits for specific repositories only"""
        if self.debug:
            print(f"🧹 Cleaning test commits for repositories: {', '.join(repo_names)} {'(DRY RUN)' if dry_run else ''}")
        
        overall_success = True
        
        try:
            # Ensure repositories are set up
            if not self.setup_test_repositories():
                return False
            
            for repo_name in repo_names:
                if repo_name not in self.test_repos:
                    print(f"⚠️  Repository {repo_name} not found in test_repos")
                    continue
                
                success = self.delete_all_test_commits(repo_name, dry_run)
                if not success:
                    overall_success = False
            
            return overall_success
            
        except Exception as e:
            print(f"❌ Selective test commit cleanup failed: {e}")
            return False

    def cleanup_test_artifacts(self, keep_commits: bool = False, clean_commits: bool = False, clean_branches: bool = True) -> bool:
        """Clean up temporary directories, test branches, and optionally test commits
        
        Args:
            keep_commits: Legacy parameter for backwards compatibility (ignored)
            clean_commits: If True, delete test commits from repositories
            clean_branches: If True, delete test branches from repositories
        """
        overall_success = True
        
        try:
            # Clean up test commits first (if requested)
            if clean_commits:
                if self.debug:
                    print("🧹 Cleaning up test commits from repositories...")
                commit_cleanup_success = self.cleanup_test_commits(dry_run=False)
                if not commit_cleanup_success:
                    overall_success = False
                    print("⚠️  Test commit cleanup had some failures")
            else:
                if self.debug:
                    print("ℹ️  Skipping test commit cleanup (clean_commits=False)")
            
            # Clean up test branches (if requested)
            if clean_branches:
                if self.debug:
                    print("🧹 Cleaning up test branches from repositories...")
                else:
                    print("🗑️ Cleaning commits, branches, files")
                for repo_name in self.temp_dirs.keys():
                    branch_success = self._cleanup_test_branches(repo_name)
                    if not branch_success:
                        overall_success = False
            else:
                if self.debug:
                    print("ℹ️  Skipping test branch cleanup (clean_branches=False)")
            
            # Clean up temporary directories
            for repo_name, temp_dir in self.temp_dirs.items():
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
                    if self.debug:
                        print(f"✅ Cleaned up temp directory for {repo_name}")
            
            self.temp_dirs.clear()
            
            # Summary message about test commits
            if not clean_commits:
                if self.debug:
                    print("ℹ️  Test commits remain in repositories (use clean_commits=True to remove)")
            
            if self.debug and overall_success:
                print("✅ All cleanup operations completed successfully")
            elif self.debug:
                print("⚠️  Some cleanup operations had failures")
            
            return overall_success
            
        except Exception as e:
            print(f"❌ Cleanup failed: {e}")
            return False
    
    def _cleanup_test_branches(self, repo_name: str) -> bool:
        """Delete test branches from remote repository using pattern matching"""
        if repo_name not in self.temp_dirs:
            return False
        
        repo_dir = self.temp_dirs[repo_name]
        
        try:
            # Get all remote branches using GitHub CLI
            repo_url = self.test_repos.get(repo_name)
            if not repo_url or 'github.com/' not in repo_url:
                if self.debug:
                    print(f"❌ Invalid repo URL for {repo_name}")
                return False
            
            repo_path = repo_url.split('github.com/')[-1]
            if repo_path.endswith('.git'):
                repo_path = repo_path[:-4]
            
            # Get all branches
            result = self._run_command(['gh', 'api', f'repos/{repo_path}/branches', '--jq', '.[].name'])
            if result.returncode != 0:
                if self.debug:
                    print(f"❌ Failed to get branches for {repo_name}")
                return False
            
            all_branches = [branch.strip() for branch in result.stdout.strip().split('\n') if branch.strip()]
            
            # Filter for test branches using patterns
            test_branch_patterns = ['test-feature', 'test-new-']
            test_branches = []
            
            for branch in all_branches:
                # Check if branch matches any test pattern
                if any(branch.startswith(pattern) for pattern in test_branch_patterns):
                    test_branches.append(branch)
            
            if not test_branches:
                if self.debug:
                    print(f"ℹ️ No test branches found to clean up in {repo_name}")
                return True
            
            if self.debug:
                print(f"🗑️ Found {len(test_branches)} test branches to delete in {repo_name}: {test_branches}")
            
            # Delete each test branch
            overall_success = True
            for branch in test_branches:
                # Double-check branch exists remotely before deletion
                if self._branch_exists_remote(branch, repo_dir):
                    delete_result = self._run_command(['git', 'push', 'origin', '--delete', branch], cwd=repo_dir)
                    if delete_result.returncode == 0:
                        if self.debug:
                            print(f"✅ Deleted remote branch {branch} from {repo_name}")
                    else:
                        overall_success = False
                        if self.debug:
                            print(f"❌ Failed to delete branch {branch} from {repo_name}: {delete_result.stderr}")
                else:
                    if self.debug:
                        print(f"ℹ️ Remote branch {branch} does not exist on {repo_name}, skipping")
            
            return overall_success
            
        except Exception as e:
            print(f"⚠️ Branch cleanup failed for {repo_name}: {e}")
            return False
    
    def get_available_branches(self, repo_name: str) -> List[str]:
        """Get list of available branches for a repository using GitHub CLI"""
        try:
            # Get GitHub URL for the repo
            repo_url = self.test_repos.get(repo_name)
            if not repo_url:
                print(f"❌ Repository {repo_name} not found in test_repos")
                return []
            
            # Extract owner/repo from URL
            if 'github.com/' not in repo_url:
                print(f"❌ Invalid GitHub URL: {repo_url}")
                return []
            
            repo_path = repo_url.split('github.com/')[-1]
            if repo_path.endswith('.git'):
                repo_path = repo_path[:-4]
            
            # Use GitHub CLI to get branches
            result = self._run_command(['gh', 'api', f'repos/{repo_path}/branches', '--jq', '.[].name'])
            
            if result.returncode == 0:
                branches = [branch.strip() for branch in result.stdout.strip().split('\n') if branch.strip()]
                if self.debug:
                    print(f"✅ Found branches for {repo_name}: {branches}")
                return branches
            else:
                print(f"❌ Failed to get branches for {repo_name}: {result.stderr}")
                return []
                
        except Exception as e:
            if self.debug:
                print(f"❌ Error getting branches for {repo_name}: {e}")
            return []
    
    def get_last_non_main_branch(self, repo_name: str) -> Optional[str]:
        """Get the last non-main branch for a repository"""
        try:
            branches = self.get_available_branches(repo_name)
            if not branches:
                return None
            
            # Filter out main/master branches
            non_main_branches = [b for b in branches if b not in ['main', 'master']]
            
            if not non_main_branches:
                if self.debug:
                    print(f"ℹ️  No non-main branches found for {repo_name}")
                return None
            
            # Return the last one (assumes most recently created/alphabetically last)
            last_branch = non_main_branches[-1]
            if self.debug:
                print(f"✅ Selected last non-main branch for {repo_name}: {last_branch}")
            return last_branch
            
        except Exception as e:
            print(f"❌ Error getting last non-main branch for {repo_name}: {e}")
            return None

    def get_repository_url(self, repo_name: str) -> Optional[str]:
        """Get repository URL by name"""
        return self.test_repos.get(repo_name)
    
    def is_repository_ready(self, repo_name: str) -> bool:
        """Check if repository is set up and ready"""
        return repo_name in self.temp_dirs and os.path.exists(self.temp_dirs[repo_name])


# Test the module functionality
if __name__ == "__main__":
    # Simple test
    ops = GitHubOperations(debug=True)
    print("🧪 Testing GitHub Operations Module")
    
    if ops.setup_test_repositories():
        print("✅ Repository setup successful")
    else:
        print("❌ Repository setup failed")
        exit(1)
    
    # Test commit creation
    if ops.create_test_commit('testing', None, 'Test framework validation commit'):
        print("✅ Test commit successful")
    else:
        print("❌ Test commit failed")
    
    # Cleanup
    ops.cleanup_test_artifacts()
    print("✅ Module test complete")