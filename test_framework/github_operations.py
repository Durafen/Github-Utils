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


class GitHubOperations:
    """Manages real GitHub repository operations for testing"""
    
    def __init__(self, debug=False):
        self.debug = debug
        self.temp_dirs = {}
        self.test_repos = {
            'ccusage': 'https://github.com/Durafen/ccusage',
            'testing': 'https://github.com/Durafen/testing'
        }
        self._check_github_auth()
    
    def _check_github_auth(self):
        """Verify GitHub CLI authentication and setup git config"""
        try:
            result = subprocess.run(['gh', 'auth', 'status'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                raise RuntimeError("GitHub CLI not authenticated. Run 'gh auth login'")
            
            # Get GitHub token for git operations
            token_result = subprocess.run(['gh', 'auth', 'token'], 
                                        capture_output=True, text=True, timeout=10)
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
        """Run command with error handling"""
        try:
            if self.debug:
                print(f"🔧 Running: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd, timeout=timeout)
            if result.returncode != 0 and self.debug:
                print(f"❌ Command failed: {result.stderr}")
            return result
        except subprocess.TimeoutExpired:
            raise RuntimeError(f"Command timed out after {timeout}s: {' '.join(cmd)}")
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
            if self.debug:
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
            if self.debug:
                print(f"⚠️ Git auth setup failed: {e}")
    
    def create_test_commit(self, repo_name: str, branch: str = 'main', 
                          message: Optional[str] = None) -> bool:
        """Create and push a test commit to specified branch"""
        if repo_name not in self.temp_dirs:
            if self.debug:
                print(f"❌ Repository {repo_name} not set up")
            return False
        
        repo_dir = self.temp_dirs[repo_name]
        timestamp = int(time.time())
        
        if not message:
            message = f"Test commit - {datetime.now().isoformat()}"
        
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
                if self.debug:
                    print(f"❌ Commit failed: {result_commit.stderr}")
                return False
            
            # Push changes
            result_push = self._run_command(['git', 'push', 'origin', branch], cwd=repo_dir)
            if result_push.returncode != 0:
                if self.debug:
                    print(f"❌ Push failed: {result_push.stderr}")
                return False
            
            if self.debug:
                print(f"✅ Created commit on {repo_name}/{branch}: {message}")
            else:
                print(f"📝 Commit: {repo_name}/{branch}")
            
            # Small delay to ensure GitHub API reflects the change
            time.sleep(2)
            return True
            
        except Exception as e:
            if self.debug:
                print(f"❌ Commit creation failed: {e}")
            return False
    
    def create_test_branch(self, repo_name: str, branch_name: str, 
                          from_branch: str = 'main') -> bool:
        """Create a new test branch"""
        if repo_name not in self.temp_dirs:
            return False
        
        repo_dir = self.temp_dirs[repo_name]
        
        try:
            # Checkout base branch and pull
            self._run_command(['git', 'checkout', from_branch], cwd=repo_dir)
            self._run_command(['git', 'pull', 'origin', from_branch], cwd=repo_dir)
            
            # Delete existing branch if it exists (both local and remote)
            self._run_command(['git', 'branch', '-D', branch_name], cwd=repo_dir)  # Ignore errors
            self._run_command(['git', 'push', 'origin', '--delete', branch_name], cwd=repo_dir)  # Ignore errors
            
            # Create and checkout new branch
            result = self._run_command(['git', 'checkout', '-b', branch_name], cwd=repo_dir)
            if result.returncode != 0:
                return False
            
            # Push new branch to origin
            push_result = self._run_command(['git', 'push', '-u', 'origin', branch_name], cwd=repo_dir)
            
            if self.debug:
                status = "✅" if push_result.returncode == 0 else "⚠️"
                print(f"{status} Branch {branch_name} created/updated on {repo_name}")
            
            return push_result.returncode == 0
            
        except Exception as e:
            if self.debug:
                print(f"❌ Branch creation failed: {e}")
            return False
    
    def cleanup_test_artifacts(self, keep_commits: bool = False) -> bool:
        """Clean up temporary directories and test branches"""
        try:
            # Clean up test branches first
            for repo_name in self.temp_dirs.keys():
                self._cleanup_test_branches(repo_name)
            
            # Clean up temporary directories
            for repo_name, temp_dir in self.temp_dirs.items():
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
                    if self.debug:
                        print(f"✅ Cleaned up temp directory for {repo_name}")
            
            self.temp_dirs.clear()
            
            # Optionally clean up test commits (not implemented to avoid complexity)
            if not keep_commits and self.debug:
                print("ℹ️  Test commits remain in repositories (manual cleanup required)")
            
            return True
            
        except Exception as e:
            if self.debug:
                print(f"❌ Cleanup failed: {e}")
            return False
    
    def _cleanup_test_branches(self, repo_name: str) -> bool:
        """Delete test branches from remote repository"""
        if repo_name not in self.temp_dirs:
            return False
        
        repo_dir = self.temp_dirs[repo_name]
        test_branches = ['test-feature']  # List of test branches to clean up
        
        try:
            for branch in test_branches:
                # Delete remote branch
                result = self._run_command(['git', 'push', 'origin', '--delete', branch], cwd=repo_dir)
                if self.debug:
                    status = "✅" if result.returncode == 0 else "ℹ️"
                    print(f"{status} Cleaned up remote branch {branch} on {repo_name}")
            return True
        except Exception as e:
            if self.debug:
                print(f"⚠️ Branch cleanup failed: {e}")
            return False
    
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
    if ops.create_test_commit('testing', 'main', 'Test framework validation commit'):
        print("✅ Test commit successful")
    else:
        print("❌ Test commit failed")
    
    # Cleanup
    ops.cleanup_test_artifacts()
    print("✅ Module test complete")