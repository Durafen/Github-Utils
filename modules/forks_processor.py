from .base_processor import BaseProcessor
from .repository_mixin import RepositoryProcessorMixin
from .debug_logger import DebugLogger
from .cost_tracker import CostTracker
from datetime import datetime

class ForksProcessor(BaseProcessor, RepositoryProcessorMixin):
    """Processor for fork analysis (forks ahead of parent)"""
    
    def __init__(self, repositories=None):
        super().__init__(template_name='fork_summary', repositories=repositories)
        self.debug_logger = DebugLogger(self.config_manager)
        self.cost_tracker = CostTracker()
    
    def _process_repository(self, repo):
        """Process repository for active forks ahead of parent"""
        # Reset cost tracking at start of each repository
        self.cost_tracker.reset()
        
        owner, repo_name, repo_key = self.extract_repo_info(repo['url'])
        
        # Get configuration limits
        max_forks = self.config_manager.get_int_setting('max_forks', 20)
        min_commits_ahead = self.config_manager.get_int_setting('min_commits_ahead', 1)
        
        try:
            # Get parent repository README once at start
            if self.config_manager.get_boolean_setting('debug'):
                self.display.display_loading(f"Fetching parent README for {repo['name']}...")
            parent_readme = self.fetcher.get_readme(owner, repo_name)
            
            # Get forks for this repository
            if self.config_manager.get_boolean_setting('debug'):
                self.display.display_loading(f"Checking forks for {repo['name']}...")
            forks = self.fetcher.get_forks(owner, repo_name, limit=max_forks)
            
            # Debug output
            self.debug_logger.debug(f"Checking up to {max_forks} forks for {repo['name']}")
            self.debug_logger.debug(f"Found {len(forks)} total forks")
            
            if not forks:
                if self.config_manager.get_boolean_setting('debug'):
                    self.display.display_no_active_forks(repo['name'])
                # Display summary even when no forks found
                self.display.display_forks_summary(
                    repo['name'],
                    0,  # active_count
                    0,  # total_count
                    self.cost_tracker.get_total_cost_info(),
                    self.config_manager.get_boolean_setting('show_costs'),
                    repo.get('url')
                )
                return
            
            # Track found ahead forks
            ahead_forks = []
            
            # Check each fork for commits ahead
            for fork in forks:
                fork_owner = fork['owner']
                fork_name = fork['name']
                fork_branch = fork.get('default_branch', 'main')
                
                # Compare fork with parent
                comparison = self.fetcher.compare_fork_with_parent(
                    owner, repo_name, fork_owner, fork_name, fork_branch
                )
                
                commits_ahead = comparison.get('ahead_by', 0)
                
                # Only process forks that are ahead by minimum threshold
                if commits_ahead >= min_commits_ahead:
                    # Get commit details for the fork
                    fork_commits = self.fetcher.get_fork_commits(fork_owner, fork_name, limit=commits_ahead)
                    
                    # Check if this fork needs processing based on saved state
                    fork_name_full = f"{fork_owner}/{fork_name}"
                    if not self._should_process_fork(repo_key, fork_name_full, fork_commits):
                        if self.config_manager.get_boolean_setting('debug'):
                            self.display.display_loading(f"Skipping {fork_name_full} - no new commits since last check")
                        continue
                    
                    # Check if README was modified in this fork's commits ahead
                    fork_readme = None
                    if self.fetcher.readme_was_modified(comparison):
                        if self.config_manager.get_boolean_setting('debug'):
                            self.display.display_loading(f"README modified in {fork_owner}/{fork_name}, fetching...")
                        fork_readme = self.fetcher.get_readme(fork_owner, fork_name)
                    
                    ahead_forks.append({
                        'fork_name': f"{fork_owner}/{fork_name}",
                        'fork_url': f"https://github.com/{fork_owner}/{fork_name}",
                        'commits_ahead': commits_ahead,
                        'commits': fork_commits,
                        'readme': fork_readme
                    })
            
            show_costs = self.config_manager.get_boolean_setting('show_costs')
            
            # Generate summaries for forks that are ahead
            if ahead_forks:
                # Display repository header once
                self.display.display_forks_header(repo['name'], repo.get('url'))
                
                for fork_info in ahead_forks:
                    # Build README sections for prompt
                    parent_readme_text = parent_readme if parent_readme else "No README found in parent repository."
                    
                    fork_readme_section = ""
                    fork_readme = fork_info.get('readme')
                    if fork_readme and self.fetcher.compare_readme_content(parent_readme, fork_readme):
                        fork_readme_section = fork_readme
                    elif not fork_readme:
                        fork_readme_section = "No README changes in this fork."
                    else:
                        fork_readme_section = "Fork README identical to parent."
                    
                    # Build fork data for AI summary
                    fork_data = {
                        'name': repo['name'],
                        'fork_name': fork_info['fork_name'],
                        'fork_url': fork_info['fork_url'],
                        'commits_ahead': fork_info['commits_ahead'],
                        'commits': fork_info['commits'],
                        'parent_readme': parent_readme_text,
                        'fork_readme_section': fork_readme_section
                    }
                    
                    result = self.generator.generate_summary(fork_data)
                    
                    # Accumulate costs
                    if 'cost_info' in result:
                        self.cost_tracker.add_cost(result['cost_info'])
                    
                    self.display.display_fork_summary(
                        repo['name'], 
                        fork_info['fork_name'], 
                        fork_info['fork_url'],
                        fork_info['commits_ahead'], 
                        result['summary']
                    )
                    
                    # Update fork state tracking
                    self._update_fork_state(repo_key, fork_info)
            else:
                if self.config_manager.get_boolean_setting('debug'):
                    self.display.display_no_active_forks(repo['name'])
            
            # Display repository-level fork summary
            self.display.display_forks_summary(
                repo['name'],
                len(ahead_forks),
                len(forks),
                self.cost_tracker.get_total_cost_info(),
                show_costs,
                repo.get('url')
            )
                
        except Exception as e:
            if "404" in str(e):
                self.display.display_error(f"Repository {repo['name']} not found or not accessible")
            else:
                raise
    
    def _should_process_fork(self, repo_key, fork_name, fork_commits):
        """Check if fork needs processing based on saved state"""
        if not self.config_manager.get_boolean_setting('save_state', 'true'):
            return True
            
        repo_state = self.state.get(repo_key, {})
        processed_forks = repo_state.get('processed_forks', {})
        
        if fork_name not in processed_forks:
            return True
            
        # Compare latest commit with saved state
        if not fork_commits:
            return False
            
        current_latest_commit = fork_commits[0]['sha'] if fork_commits else None
        saved_latest_commit = processed_forks[fork_name].get('last_ahead_commit')
        
        # Process if commits have changed
        return current_latest_commit != saved_latest_commit

    def _update_fork_state(self, repo_key, fork_info):
        """Update state tracking for processed forks"""
        updated_state = self.state.get(repo_key, {})
        
        # Initialize fork tracking section
        if 'processed_forks' not in updated_state:
            updated_state['processed_forks'] = {}
        
        # Update fork-specific state
        fork_key = fork_info['fork_name']
        updated_state['processed_forks'][fork_key] = {
            'last_ahead_commit': fork_info['commits'][0]['sha'] if fork_info['commits'] else None,
            'commits_ahead': fork_info['commits_ahead'],
            'last_check': datetime.now().isoformat()
        }
        
        # Update general fork check timestamp
        updated_state['last_fork_check'] = datetime.now().isoformat()
        
        self.state[repo_key] = updated_state