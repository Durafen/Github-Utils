from .base_processor import BaseProcessor
from .repository_mixin import RepositoryProcessorMixin

class NewsProcessor(BaseProcessor, RepositoryProcessorMixin):
    """Processor for news summaries (commits and releases)"""
    
    def __init__(self, repositories=None):
        super().__init__(template_name='summary', repositories=repositories)
    
    def _process_repository(self, repo):
        """Process repository for news updates"""
        owner, repo_name, repo_key = self.extract_repo_info(repo['url'])
        
        # Get last state
        last_commit = self.state.get(repo_key, {}).get('last_commit')
        last_release = self.state.get(repo_key, {}).get('last_release')
        
        # Fetch data with configured limits
        max_commits = self.config_manager.get_int_setting('max_commits', 10)
        max_releases = self.config_manager.get_int_setting('max_releases', 10)
        
        commits = self.fetcher.get_commits(owner, repo_name, since=last_commit, limit=max_commits)
        releases = self.fetcher.get_releases(owner, repo_name, limit=max_releases)
        
        # Check for updates
        has_newer_commits = self.has_newer_commits(commits, last_commit, owner, repo_name)
        has_newer_releases = self.has_newer_releases(releases, last_release)
        
        # Generate summary if needed
        if (has_newer_commits and commits) or (has_newer_releases and releases):
            if self.config_manager.get_boolean_setting('debug'):
                self.display.display_loading(f"Processing {repo['name']}...")
            
            repo_data = {
                'name': repo['name'],
                'commits': commits if has_newer_commits else [],
                'releases': releases if has_newer_releases else []
            }
            result = self.generator.generate_summary(repo_data)
            show_costs = self.config_manager.get_boolean_setting('show_costs')
            
            # Get current version
            version = self.fetcher.get_latest_version(owner, repo_name)
            
            self.display.display_summary(repo['name'], result['summary'], result['cost_info'], show_costs, repo['url'], version)
            
            self.update_repository_state(repo_key, has_newer_commits, has_newer_releases,
                                       commits, releases, owner, repo_name)