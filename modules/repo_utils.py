"""Repository utility functions - converted from RepositoryProcessorMixin"""

from datetime import datetime
from .state_manager import StateManager

class RepoUtils:
    """Static utility functions for repository processing"""
    
    @staticmethod
    def extract_repo_info(repo_url, fetcher):
        """Extract owner, repo name, and repo key from URL"""
        owner, repo_name = fetcher.extract_owner_repo(repo_url)
        return owner, repo_name, f"{owner}/{repo_name}".lower()
    
    @staticmethod
    def has_newer_commits(commits, last_commit, fetcher, owner, repo_name):
        """Check if there are newer commits than last processed"""
        if commits and last_commit:
            latest_sha = fetcher.get_latest_commit_sha(owner, repo_name)
            return latest_sha != last_commit
        elif commits and not last_commit:
            return True  # First run with commits
        return False
    
    @staticmethod  
    def has_newer_releases(releases, last_release):
        """Check if there are newer releases than last processed"""
        if releases and last_release:
            latest_release_id = releases[0]['id']
            return str(latest_release_id) != str(last_release)
        elif releases and not last_release:
            return True  # First run with releases
        return False
    
    @staticmethod
    def update_repository_state(state, repo_key, has_newer_commits, has_newer_releases, 
                               commits, releases, fetcher, owner, repo_name):
        """Update state for repository with new commit/release info"""
        StateManager.update_basic_repository_state(
            state, repo_key,
            commits if has_newer_commits else None,
            releases if has_newer_releases else None,
            fetcher, owner, repo_name
        )