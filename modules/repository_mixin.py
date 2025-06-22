from datetime import datetime
from .state_manager import StateManager

class RepositoryProcessorMixin:
    """Mixin providing shared GitHub data processing logic"""
    
    def extract_repo_info(self, repo_url):
        """Extract owner, repo name, and repo key from URL"""
        owner, repo_name = self.fetcher.extract_owner_repo(repo_url)
        return owner, repo_name, f"{owner}/{repo_name}".lower()
    
    def has_newer_commits(self, commits, last_commit, owner, repo_name):
        """Check if there are newer commits than last processed"""
        if commits and last_commit:
            latest_sha = self.fetcher.get_latest_commit_sha(owner, repo_name)
            return latest_sha != last_commit
        elif commits and not last_commit:
            return True  # First run with commits
        return False
    
    def has_newer_releases(self, releases, last_release):
        """Check if there are newer releases than last processed"""
        if releases and last_release:
            latest_release_id = releases[0]['id']
            return str(latest_release_id) != str(last_release)
        elif releases and not last_release:
            return True  # First run with releases
        return False
    
    def update_repository_state(self, repo_key, has_newer_commits, has_newer_releases, 
                               commits, releases, owner, repo_name):
        """Update state for repository with new commit/release info"""
        StateManager.update_basic_repository_state(
            self.state, repo_key,
            commits if has_newer_commits else None,
            releases if has_newer_releases else None,
            self.fetcher, owner, repo_name
        )
    
