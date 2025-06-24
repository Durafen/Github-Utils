from .parallel_base_processor import ParallelBaseProcessor
from .repository_mixin import RepositoryProcessorMixin
from .debug_logger import DebugLogger
from .cost_tracker import CostTracker
from .commit_utils import filter_commits_since_last_processed
from .state_manager import StateManager
from datetime import datetime

class ForksProcessor(ParallelBaseProcessor, RepositoryProcessorMixin):
    """Processor for fork analysis (forks ahead of parent)"""
    
    def __init__(self, repositories=None):
        super().__init__(template_name='fork_summary', repositories=repositories)
        self.debug_logger = DebugLogger(self.config_manager)
        self.cost_tracker = CostTracker()
    
    @property
    def state_type(self):
        return 'forks'
    
    def _process_repository(self, repo):
        """Process repository for active forks ahead of parent"""
        # Reset cost tracking at start of each repository
        self.cost_tracker.reset()
        
        owner, repo_name, repo_key = self.extract_repo_info(repo['url'])
        
        # Get configuration limits
        max_forks = self.config_manager.get_int_setting('max_forks', 20)
        min_commits_ahead = self.config_manager.get_int_setting('min_commits_ahead', 1)
        max_branches_per_fork = self.config_manager.get_int_setting('max_branches_per_fork', 5)
        max_commits = self.config_manager.get_int_setting('max_commits', 10)
        analyze_default_branch_always = self.config_manager.get_boolean_setting('analyze_default_branch_always', True)
        
        try:
            # Get parent default branch
            parent_default_branch = self.fetcher.get_default_branch(owner, repo_name)
            
            # Get latest commit timestamp for headline
            try:
                last_commit_timestamp = self.fetcher.get_latest_commit_timestamp(owner, repo_name)
            except Exception:
                last_commit_timestamp = None
            
            # Get parent repository README once at start
            if self.config_manager.get_boolean_setting('debug'):
                self._safe_display_loading(f"Fetching parent README for {repo['name']}...")
            parent_readme = self.fetcher.get_readme(owner, repo_name)
            
            # Get forks for this repository
            if self.config_manager.get_boolean_setting('debug'):
                self._safe_display_loading(f"Checking forks for {repo['name']}...")
            forks = self.fetcher.get_forks(owner, repo_name, limit=max_forks)
            
            # Debug output
            self.debug_logger.debug(f"Checking up to {max_forks} forks for {repo['name']}")
            self.debug_logger.debug(f"Found {len(forks)} total forks")
            
            if not forks:
                if self.config_manager.get_boolean_setting('debug'):
                    self._safe_display_no_active_forks(repo['name'])
                # Display summary even when no forks found
                self._safe_display_forks_summary(
                    repo['name'],
                    0,  # active_count
                    0,  # total_count
                    self.cost_tracker.get_total_cost_info(),
                    self.config_manager.get_show_costs_setting(),
                    repo.get('url')
                )
                return
            
            # Track found ahead forks
            ahead_forks = []
            show_costs = self.config_manager.get_show_costs_setting()
            header_displayed = False
            
            # OPTIMIZATION: Smart fork filtering with early exit
            # Stage 1: Get lightweight fork list (just names and default branch info)
            current_forks = self.fetcher.get_fork_last_commits(owner, repo_name, max_forks)
            
            # Stage 2: Filter by state before expensive operations
            forks_to_process = []
            for fork in current_forks:
                fork_full_name = fork['full_name']
                if self._should_process_fork_by_state(repo_key, fork_full_name, fork):
                    forks_to_process.append(fork)
            
            if not forks_to_process:
                if self.config_manager.get_boolean_setting('debug'):
                    self._safe_display_no_fork_changes(repo['name'])
                # Display summary even when no forks need processing
                self._safe_display_forks_summary(
                    repo['name'], 0, len(current_forks), 
                    self.cost_tracker.get_total_cost_info(),
                    self.config_manager.get_show_costs_setting(),
                    repo.get('url')
                )
                return
            
            # Stage 3: Full processing only for changed forks
            ahead_forks = self._process_fork_subset(forks_to_process, repo, owner, repo_name, parent_default_branch, max_branches_per_fork, min_commits_ahead, analyze_default_branch_always, max_commits, parent_readme, repo_key)
            
            # Show message if no forks found after processing all
            if not ahead_forks:
                if self.config_manager.get_boolean_setting('debug'):
                    self._safe_display_no_active_forks(repo['name'])
            
            # Display repository-level fork summary
            self._safe_display_forks_summary(
                repo['name'],
                len(ahead_forks),
                len(current_forks),
                self.cost_tracker.get_total_cost_info(),
                show_costs,
                repo.get('url')
            )
                
        except Exception as e:
            if "404" in str(e):
                self._safe_display_error(f"Repository {repo['name']} not found or not accessible")
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
        """Update state tracking for processed forks with multi-branch support"""
        StateManager.update_fork_state(self.state, repo_key, fork_info)
    
    def _transform_comparison_commits(self, comparison_commits):
        """Transform comparison API commits to match expected structure for summary generator"""
        transformed_commits = []
        for commit in comparison_commits:
            # Transform from comparison format to expected format
            transformed_commit = {
                'sha': commit.get('sha', ''),
                'commit': {
                    'message': commit.get('message', ''),
                    'author': commit.get('author', {})
                }
            }
            transformed_commits.append(transformed_commit)
        return transformed_commits

    def _process_fork_branches(self, parent_owner, parent_repo, parent_default_branch, fork_owner, fork_name, 
                              fork_default_branch, max_branches_per_fork, min_commits_ahead,
                              analyze_default_branch_always, max_commits, parent_readme, repo_key):
        """Process all branches of a single fork and return consolidated analysis"""
        
        # Get all branches for this fork
        if self.config_manager.get_boolean_setting('debug'):
            self._safe_display_loading(f"Analyzing branches for {fork_owner}/{fork_name}...")
            
        fork_branches = self.fetcher.get_fork_branches(fork_owner, fork_name)
        
        if not fork_branches:
            if self.config_manager.get_boolean_setting('debug'):
                self._safe_display_loading(f"No branches found for {fork_owner}/{fork_name}")
            return None
        
        # Debug output
        self.debug_logger.debug(f"Found {len(fork_branches)} branches for {fork_owner}/{fork_name}")
        
        # Collect branch analysis results
        branch_analyses = []
        total_commits_ahead = 0
        all_commits = []
        fork_readme = None
        
        # Process branches with prioritization
        prioritized_branches = self._prioritize_branches(
            fork_branches, fork_default_branch, max_branches_per_fork
        )
        
        # Track ALL processed branches for state saving (even if filtered to 0)
        all_processed_branches = []
        
        for branch in prioritized_branches:
            branch_name = branch['name']
            is_default = branch_name == fork_default_branch
            
            # Compare this branch with parent's default branch
            comparison = self.fetcher.compare_branch_with_parent(
                parent_owner, parent_repo, parent_default_branch, 
                fork_owner, fork_name, branch_name
            )
            
            commits_ahead = comparison.get('ahead_by', 0)
            
            # Include branch if ahead or if it's default and we always analyze default
            should_include = (
                commits_ahead >= min_commits_ahead or 
                (is_default and analyze_default_branch_always and commits_ahead > 0)
            )
            
            if should_include:
                # Use commits from comparison API (these are already the new commits vs parent)
                comparison_commits = comparison.get('commits', [])
                branch_commits = self._transform_comparison_commits(comparison_commits)
                
                # INCREMENTAL FILTERING: Only show commits newer than last processed
                # Get saved state for this specific branch
                repo_state = self.state.get(repo_key, {})
                processed_forks = repo_state.get('processed_forks', {})
                fork_name_full = f"{fork_owner}/{fork_name}"
                saved_branches = processed_forks.get(fork_name_full, {}).get('branches', {})
                last_processed_commit = saved_branches.get(branch_name, {}).get('last_ahead_commit')
                
                # DEBUG: Show exact state lookup and filtering decision
                self.debug_logger.debug(f"STATE DEBUG: {branch_name}")
                self.debug_logger.debug(f"   repo_key: {repo_key}")
                self.debug_logger.debug(f"   fork_name_full: {fork_name_full}")
                self.debug_logger.debug(f"   processed_forks keys: {list(processed_forks.keys())}")
                if fork_name_full in processed_forks:
                    fork_branches = processed_forks[fork_name_full].get('branches', {})
                    self.debug_logger.debug(f"   fork branches: {list(fork_branches.keys())}")
                    if branch_name in fork_branches:
                        branch_data = fork_branches[branch_name]
                        self.debug_logger.debug(f"   {branch_name} data: {branch_data}")
                    else:
                        self.debug_logger.debug(f"   {branch_name} NOT FOUND in fork branches")
                else:
                    self.debug_logger.debug(f"   {fork_name_full} NOT FOUND in processed_forks")
                self.debug_logger.debug(f"   final last_processed_commit: {last_processed_commit}")
                self.debug_logger.debug(f"   total commits before filtering: {len(branch_commits)}")
                self.debug_logger.debug(f"   commits_ahead from comparison: {commits_ahead}")
                
                # Filter commits to only show ones newer than last processed commit
                if last_processed_commit and branch_commits:
                    self.debug_logger.debug(f"Filtering {branch_name} - saved: {last_processed_commit}, total: {len(branch_commits)}")
                    original_count = len(branch_commits)
                    branch_commits = filter_commits_since_last_processed(branch_commits, last_processed_commit)
                    self.debug_logger.debug(f"After filtering: {len(branch_commits)} commits (was {original_count})")
                else:
                    self.debug_logger.debug(f"No filtering for {branch_name} - saved: {last_processed_commit}, commits: {len(branch_commits) if branch_commits else 0}")
                
                # Get latest commit timestamp for this specific branch
                try:
                    if self.config_manager.get_boolean_setting('debug'):
                        self._safe_display_loading(f"Fetching timestamp for {fork_owner}/{fork_name}:{branch_name}")
                    branch_timestamp = self.fetcher.get_latest_commit_timestamp(fork_owner, fork_name, branch_name)
                    if self.config_manager.get_boolean_setting('debug'):
                        self._safe_display_loading(f"Got timestamp: {branch_timestamp}")
                except Exception as e:
                    if self.config_manager.get_boolean_setting('debug'):
                        self._safe_display_loading(f"Timestamp fetch failed for {fork_owner}/{fork_name}:{branch_name} - {e}")
                    branch_timestamp = None
                
                # Check README modifications for this branch
                if self.fetcher.readme_was_modified(comparison) and fork_readme is None:
                    if self.config_manager.get_boolean_setting('debug'):
                        self._safe_display_loading(f"README modified in {branch_name}, fetching...")
                    fork_readme = self.fetcher.get_readme(fork_owner, fork_name)
                
                # Use filtered commit count for accurate AI context
                filtered_commits_count = len(branch_commits)
                
                # Always track this branch for state saving (even if 0 commits)
                # For state saving, we need the ORIGINAL commits to get the latest SHA
                original_commits = self._transform_comparison_commits(comparison_commits)
                all_processed_branches.append({
                    'branch_name': branch_name,
                    'commits_ahead': filtered_commits_count,
                    'is_default': is_default,
                    'commits': branch_commits,  # Filtered commits for AI
                    'original_commits': original_commits,  # Original commits for state
                    'original_commit_count': commits_ahead,
                    'last_commit_timestamp': branch_timestamp,
                })
                
                # Skip branch if no commits after filtering (already processed all commits)
                if filtered_commits_count == 0:
                    self.debug_logger.debug(f"SKIPPING {branch_name} - 0 commits after filtering")
                    continue
                
                # Add all branches to all_commits for main section
                all_commits.extend(branch_commits[:max_commits])
                
                branch_analyses.append({
                    'branch_name': branch_name,
                    'commits_ahead': filtered_commits_count,
                    'is_default': is_default,
                    'commits': branch_commits[:max_commits],  # Use max_commits setting
                    'last_commit_timestamp': branch_timestamp,
                })
                
                total_commits_ahead += filtered_commits_count
        
        self.debug_logger.debug(f"Final branch_analyses count: {len(branch_analyses)}")
        for ba in branch_analyses:
            self.debug_logger.debug(f"   - {ba['branch_name']}: {ba['commits_ahead']} commits")
        
        # If no non-default branches have commits, check if we should still process for default branch
        if not branch_analyses:
            # Only return None if there are no processed branches at all (including default)
            if not all_processed_branches:
                return None
            
            # Check if default branch has commits (even though we don't include it in branch_analyses)
            has_default_commits = any(
                b['is_default'] and b['commits_ahead'] > 0 
                for b in all_processed_branches
            )
            
            if not has_default_commits:
                return None
        
        # Check if this fork needs processing based on state
        fork_name_full = f"{fork_owner}/{fork_name}"
        if not self._should_process_fork_multi_branch(repo_key, fork_name_full, branch_analyses):
            if self.config_manager.get_boolean_setting('debug'):
                self._safe_display_debug(f"Skipping {fork_name_full} - no new commits across branches")
            return None
        
        # Sort all commits by most recent for AI context
        all_commits.sort(key=lambda x: x.get('committer', {}).get('date', ''), reverse=True)
        
        # Get overall fork timestamp (most recent across all branches)
        fork_timestamp = None
        if branch_analyses:
            timestamps = [b.get('last_commit_timestamp') for b in branch_analyses if b.get('last_commit_timestamp')]
            if timestamps:
                # Find most recent timestamp
                from datetime import datetime
                try:
                    most_recent = max(timestamps, key=lambda x: datetime.fromisoformat(x.replace('Z', '+00:00')))
                    fork_timestamp = most_recent
                except Exception:
                    fork_timestamp = timestamps[0]  # Fallback to first available
        
        # Return consolidated fork analysis
        return {
            'fork_name': fork_name_full,
            'fork_url': f"https://github.com/{fork_owner}/{fork_name}",
            'commits_ahead': total_commits_ahead,
            'commits': all_commits[:max_commits],  # Use max_commits setting for overall summary
            'readme': fork_readme,
            'branches': branch_analyses,  # For AI and display (only branches with commits)
            'all_processed_branches': all_processed_branches,  # For state saving (all branches)
            'total_branches_analyzed': len(branch_analyses),
            'last_commit_timestamp': fork_timestamp,
        }

    def _should_process_fork_by_state(self, repo_key, fork_full_name, fork_basic_info):
        """Quick check if fork needs processing based on lightweight state comparison"""
        if not self.config_manager.get_boolean_setting('save_state', True):
            return True
            
        repo_state = self.state.get(repo_key, {})
        processed_forks = repo_state.get('processed_forks', {})
        
        if fork_full_name not in processed_forks:
            return True  # New fork
        
        # For lightweight check, we can't compare all branches here
        # So we'll do a quick updated_at timestamp check if available
        fork_last_update = fork_basic_info.get('updated_at')
        if not fork_last_update:
            return True  # Process if we can't determine last update
        
        # Compare with our last check time
        saved_fork_state = processed_forks[fork_full_name]
        last_check = saved_fork_state.get('last_check')
        
        if not last_check:
            return True  # Process if no previous check
        
        # Quick timestamp comparison (not perfect but good enough for early filtering)
        try:
            from datetime import datetime
            fork_update_time = datetime.fromisoformat(fork_last_update.replace('Z', '+00:00'))
            last_check_time = datetime.fromisoformat(last_check)
            return fork_update_time > last_check_time
        except:
            return True  # Process if timestamp comparison fails

    def _process_fork_subset(self, forks_to_process, repo, owner, repo_name, parent_default_branch, max_branches_per_fork, min_commits_ahead, analyze_default_branch_always, max_commits, parent_readme, repo_key):
        """Process only the subset of forks that need processing"""
        ahead_forks = []
        show_costs = self.config_manager.get_show_costs_setting()
        header_displayed = False
        
        for fork in forks_to_process:
            fork_owner = fork['owner']
            fork_name = fork['name']
            fork_default_branch = fork.get('default_branch', 'main')
            
            # Process multi-branch analysis for this fork
            fork_analysis = self._process_fork_branches(
                owner, repo_name, parent_default_branch, fork_owner, fork_name, fork_default_branch,
                max_branches_per_fork, min_commits_ahead, analyze_default_branch_always,
                max_commits, parent_readme, repo_key
            )
            
            if fork_analysis:
                ahead_forks.append(fork_analysis)
                
                # Display header only once when first fork is found
                if not header_displayed:
                    self._safe_display_forks_header(repo['name'], repo.get('url'))
                    header_displayed = True
                
                # Process fork immediately for AI summary
                fork_info = fork_analysis
                # Build README sections for prompt
                parent_readme_text = parent_readme if parent_readme else "No README found in parent repository."
                
                fork_readme = fork_info.get('readme')
                fork_readme_diff = self.fetcher.generate_readme_diff(parent_readme, fork_readme)
                
                # Build fork data for AI summary (with multi-branch support)
                fork_data = {
                    'name': repo['name'],
                    'fork_name': fork_info['fork_name'],
                    'fork_url': fork_info['fork_url'],
                    'commits_ahead': fork_info['commits_ahead'],
                    'commits': fork_info['commits'],  # Multi-branch commits for summary
                    'branches': fork_info['branches'],  # Branch breakdown for display
                    'parent_readme': parent_readme_text,
                    'fork_readme_diff': fork_readme_diff
                }
                
                # Generate AI summary
                try:
                    result = self.generator.generate_summary(fork_data)
                    summary = result['summary']
                    
                    # Track cost for this fork
                    if result.get('cost_info'):
                        self.cost_tracker.add_cost(result['cost_info'])
                    
                    # Display fork analysis
                    self._safe_display_fork_summary(
                        repo['name'], 
                        fork_info['fork_name'],
                        f"https://github.com/{fork_info['fork_name']}",
                        fork_info['commits_ahead'],
                        summary,
                        fork_info['branches'],
                        fork_info.get('last_commit_timestamp')
                    )
                    
                    # Update state with this fork's analysis
                    StateManager.update_fork_state(self.state, repo_key, fork_info)
                    
                except Exception as e:
                    # Always log critical errors, not just in debug mode
                    self._safe_display_error(f"❌ Summary generation failed for {fork_info['fork_name']}: {e}")
                    if self.config_manager.get_boolean_setting('debug'):
                        import traceback
                        self._safe_display_error(f"Full traceback: {traceback.format_exc()}")
        
        return ahead_forks
    
    def _prioritize_branches(self, branches, default_branch, max_branches):
        """Prioritize branches for analysis"""
        if not branches:
            return []
        
        # Sort branches by priority:
        # 1. Default branch first
        # 2. Most recently active (simplified - just by name for now)
        # 3. Limit to max_branches
        
        sorted_branches = []
        
        # Add default branch first if it exists
        default_branch_obj = None
        for branch in branches:
            if branch['name'] == default_branch:
                default_branch_obj = branch
                break
        
        if default_branch_obj:
            sorted_branches.append(default_branch_obj)
        
        # Add other branches
        other_branches = [b for b in branches if b['name'] != default_branch]
        # Sort by name for now (in a more advanced version, we'd sort by commit date)
        other_branches.sort(key=lambda x: x['name'])
        
        sorted_branches.extend(other_branches)
        
        # Limit to max_branches
        return sorted_branches[:max_branches]
    
    def _should_process_fork_multi_branch(self, repo_key, fork_name, branch_analyses):
        """Check if multi-branch fork needs processing based on saved state"""
        save_state_enabled = self.config_manager.get_boolean_setting('save_state', True)
        return StateManager.should_process_fork_by_state(
            self.state, repo_key, fork_name, branch_analyses, save_state_enabled
        )