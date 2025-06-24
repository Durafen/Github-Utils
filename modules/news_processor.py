from .parallel_base_processor import ParallelBaseProcessor
from .repo_utils import RepoUtils
from .commit_utils import filter_commits_since_last_processed
from .state_manager import StateManager

class NewsProcessor(ParallelBaseProcessor):
    """Processor for news summaries (commits and releases)"""
    
    def __init__(self, repositories=None, debug_override=None):
        super().__init__(template_name='summary', repositories=repositories, debug_override=debug_override)
    
    @property
    def state_type(self):
        return 'news'
    
    def _process_repository(self, repo):
        """Optimized repository processing with early-exit state validation"""
        from .url_utils import extract_repo_info
        owner, repo_name, repo_key = extract_repo_info(repo['url'], self.fetcher, include_repo_key=True)
        
        # PHASE 1: Quick repository state check (early exit optimization)
        current_main_sha = self.fetcher.get_current_main_sha(owner, repo_name)
        if not current_main_sha:
            if self.config_manager.get_boolean_setting('debug'):
                self._safe_display('error', f"Could not get main branch SHA for {repo['name']}")
            return
        
        # PHASE 2: Early exit if main branch unchanged and save_state enabled
        if self.config_manager.get_boolean_setting('save_state', True):
            if StateManager.main_branch_unchanged(self.state, repo_key, current_main_sha):
                # Quick branch discovery for selective processing
                current_branches = self.fetcher.get_branch_shas_only(owner, repo_name)
                current_branch_shas = {b['name']: b['commit']['sha'] for b in current_branches}
                
                needs_processing, new_branches, changed_branches = StateManager.needs_repository_processing(
                    self.state, repo_key, current_main_sha, current_branch_shas
                )
                
                if not needs_processing:
                    if self.config_manager.get_boolean_setting('debug'):
                        self._safe_display('display_no_updates', repo['name'])
                    return
                
                # Process only changed/new branches (selective processing)
                return self._process_selective_branches(repo, owner, repo_name, repo_key, new_branches, changed_branches, current_branch_shas)
        
        # PHASE 3: Fallback to full processing for changed main branch or no state
        return self._process_full_repository(repo, owner, repo_name, repo_key, current_main_sha)

    def _process_full_repository(self, repo, owner, repo_name, repo_key, current_main_sha):
        """Full repository processing (original logic)"""
        last_commit = self.state.get(repo_key, {}).get('last_commit')
        last_release = self.state.get(repo_key, {}).get('last_release')
        
        max_commits = self.config_manager.get_int_setting('max_commits', 10)
        max_releases = self.config_manager.get_int_setting('max_releases', 10)
        
        # Get default branch for comparison
        default_branch = self.fetcher.get_default_branch(owner, repo_name)
        
        # Adaptive commit fetching: cross-repo for forks, normal for non-forks
        is_fork, parent_owner, parent_name = self.fetcher.get_fork_info(owner, repo_name)
        
        if is_fork:
            # For forks: get commits on main that are ahead of parent (like forks module)
            all_fork_commits = self.fetcher.get_branch_commits_since_base(
                owner, repo_name, default_branch, default_branch, limit=max_commits
            )
            # Filter commits to only show ones newer than last processed commit
            commits = filter_commits_since_last_processed(all_fork_commits, last_commit)
            
            # For forks, check if we have new commits ahead of parent since last run
            has_newer_commits = len(commits) > 0
        else:
            # For non-forks: get recent commits and filter properly
            all_commits = self.fetcher.get_commits(owner, repo_name, limit=max_commits)
            # Reverse order to match compare API format (oldest first)
            all_commits.reverse()
            commits = filter_commits_since_last_processed(all_commits, last_commit)
            has_newer_commits = len(commits) > 0
        
        releases = self.fetcher.get_releases(owner, repo_name, limit=max_releases)
        has_newer_releases = RepoUtils.has_newer_releases(releases, last_release)
        
        # Individual branch analysis
        individual_branches = self._analyze_individual_branches(owner, repo_name, repo_key, default_branch)
        
        # ENHANCED: Summary generation logic - includes main branch commits OR branch updates
        needs_summary = (
            (has_newer_commits and commits) or 
            (has_newer_releases and releases) or
            (individual_branches and len(individual_branches) > 0)
        )
        
        if needs_summary:
            if self.config_manager.get_boolean_setting('debug'):
                self._safe_display('display_loading', f"Processing {repo['name']}...")
            
            show_costs = self.config_manager.get_show_costs_setting()
            version = self.fetcher.get_latest_version(owner, repo_name)
            
            # Get latest commit timestamp for headline
            try:
                last_commit_timestamp = self.fetcher.get_latest_commit_timestamp(owner, repo_name)
            except Exception:
                last_commit_timestamp = None
            
            # Check if we have main branch updates
            has_main_updates = (has_newer_commits and commits) or (has_newer_releases and releases)
            has_branch_updates = individual_branches and len(individual_branches) > 0
            
            # Process main branch summary if needed
            if has_main_updates:
                repo_data = {
                    'name': repo['name'],
                    'commits': commits if has_newer_commits else [],
                    'releases': releases if has_newer_releases else []
                }
                
                result = self.generator.generate_summary(repo_data)
                
                # Display main repository summary with commit count
                commit_count = len(commits) if has_newer_commits else 0
                self._safe_display('display_news_summary',
                    repo['name'], result['summary'], result.get('cost_info'),
                    show_costs, repo['url'], version, None, last_commit_timestamp, commit_count
                )
            elif has_branch_updates:
                # Branch-only updates: Display repository headline only (no timestamp for empty summary)
                self._safe_display('display_news_summary',
                    repo['name'], "", None,
                    False, repo['url'], version, None, None
                )
            
            # Process individual branch summaries
            for branch_data in individual_branches:
                if self.config_manager.get_boolean_setting('debug'):
                    self._safe_display('display_loading', f"Processing branch {branch_data['branch_name']}...")
                
                result = self.generator.generate_summary(branch_data)
                
                # Display individual branch summary
                self._safe_display('display_branch_summary',
                    branch_data['branch_name'], 
                    branch_data['commits_ahead'],
                    result['summary'], 
                    result.get('cost_info'),
                    show_costs,
                    branch_data.get('is_default', False),
                    branch_data.get('last_commit_timestamp')
                )
        
        # Always update state if there's any processing (summary or not)
        if (has_newer_commits and commits) or (has_newer_releases and releases) or (individual_branches and len(individual_branches) > 0):
            self._update_repository_state_with_individual_branches(
                repo_key, has_newer_commits, has_newer_releases,
                commits, releases, owner, repo_name, individual_branches
            )
        else:
            if self.config_manager.get_boolean_setting('debug'):
                self._safe_display('display_no_updates', repo['name'])

    def _analyze_individual_branches(self, owner, repo_name, repo_key, default_branch):
        """Analyze repository branches individually for separate summaries"""
        try:
            # Configuration
            max_branches = self.config_manager.get_int_setting('max_branches_per_repo', 5)
            min_commits = self.config_manager.get_int_setting('min_branch_commits', 1)
            all_branches = self.fetcher.get_repository_branches(owner, repo_name, limit=max_branches * 2)
            
            if not all_branches:
                return []
            
            # Filter non-default branches only (default branch handled separately)
            candidate_branches = [b for b in all_branches if b['name'] != default_branch]
            candidate_branches.sort(key=lambda x: x['name'])  # Consistent ordering
            candidate_branches = candidate_branches[:max_branches]
            
            individual_branch_data = []
            
            for branch in candidate_branches:
                branch_name = branch['name']
                
                # Get comparison data first (now uses adaptive logic)
                comparison = self.fetcher.get_branch_comparison(owner, repo_name, default_branch, branch_name)
                commits_ahead = comparison.get('ahead_by', 0)
                is_orphan = comparison.get('is_orphan', False)
                
                # Handle orphan branches as independent branches (like main)
                if is_orphan:
                    commits_ahead = 1  # Treat as having commits to process
                
                # Get commits for AI analysis if branch has commits ahead or is orphan
                if commits_ahead > 0:
                    max_commits = self.config_manager.get_int_setting('max_commits', 10)
                    
                    if is_orphan:
                        # For orphan branches, get commits directly (can't compare with base)
                        all_branch_commits = self.fetcher.get_commits(
                            owner, repo_name, limit=max_commits, branch=branch_name
                        )
                        # Reverse to match compare API format (oldest first)
                        all_branch_commits.reverse()
                    else:
                        all_branch_commits = self.fetcher.get_branch_commits_since_base(
                            owner, repo_name, branch_name, default_branch, limit=max_commits
                        )
                    
                    # Filter branch commits based on saved state (same logic as main branch)
                    repo_state = self.state.get(repo_key, {})
                    branch_states = repo_state.get('branches', {})
                    last_branch_commit = branch_states.get(branch_name, {}).get('last_commit')
                    
                    branch_commits = filter_commits_since_last_processed(all_branch_commits, last_branch_commit)
                else:
                    branch_commits = []
                
                # Debug actual commits fetched
                if self.config_manager.get_boolean_setting('debug'):
                    is_fork, parent_owner, parent_name = self.fetcher.get_fork_info(owner, repo_name)
                    comparison_type = "cross-repo (fork)" if is_fork else "same-repo"
                    self._safe_display('display_loading',f"Branch {branch_name}: {commits_ahead} commits ahead ({comparison_type})")
                
                if commits_ahead >= min_commits:
                    # Check if needs processing (state-based)
                    if self._should_process_branch(repo_key, branch_name, branch_commits):
                        # Use filtered commits count (new commits since last check)
                        actual_commits_count = len(branch_commits)
                        
                        # Get latest commit timestamp for this specific branch
                        try:
                            branch_timestamp = self.fetcher.get_latest_commit_timestamp(owner, repo_name, branch_name)
                        except Exception:
                            branch_timestamp = None
                        
                        # Prepare individual branch data for AI summary
                        branch_data = {
                            'name': f"{repo_name} - {branch_name} branch",
                            'branch_name': branch_name,
                            'commits_ahead': actual_commits_count,  # Use actual count
                            'commits': branch_commits,
                            'is_default': False,
                            'parent_branch': default_branch,
                            'last_commit_timestamp': branch_timestamp,
                        }
                        individual_branch_data.append(branch_data)
            
            return individual_branch_data
            
        except Exception as e:
            if self.config_manager.get_boolean_setting('debug'):
                self._safe_display('error',f"Individual branch analysis failed for {repo_name}: {e}")
            return []

    def _should_process_branch(self, repo_key, branch_name, branch_commits):
        """Check if branch needs processing based on state"""
        save_state_enabled = self.config_manager.get_boolean_setting('save_state', True)
        return StateManager.should_process_branch_by_state(
            self.state, repo_key, branch_name, branch_commits, save_state_enabled
        )

    def _should_process_fork_main(self, repo_key, fork_main_commits):
        """Check if fork's main branch needs processing (like forks module logic)"""
        if not self.config_manager.get_boolean_setting('save_state', True):
            return True
            
        if not fork_main_commits:
            return False
            
        repo_state = self.state.get(repo_key, {})
        saved_main_commit = repo_state.get('last_commit')
        
        if not saved_main_commit:
            return True  # First time processing
            
        current_latest = fork_main_commits[-1]['sha']
        return current_latest != saved_main_commit  # Has new commits ahead of parent

    def _update_repository_state_with_individual_branches(self, repo_key, has_newer_commits, has_newer_releases, commits, releases, owner, repo_name, individual_branches):
        """Update state including individual branch tracking"""
        # Update basic repository state
        if has_newer_commits or has_newer_releases:
            StateManager.update_basic_repository_state(
                self.state, repo_key, 
                commits if has_newer_commits else None,
                releases if has_newer_releases else None,
                self.fetcher, owner, repo_name
            )
        
        # Update individual branch states
        if individual_branches:
            for branch_data in individual_branches:
                StateManager.update_branch_state(
                    self.state, repo_key,
                    branch_data['branch_name'],
                    branch_data['commits'],
                    branch_data['commits_ahead']
                )

    def _process_selective_branches(self, repo, owner, repo_name, repo_key, new_branches, changed_branches, current_branch_shas):
        """Process only specific branches that have changed or are new"""
        if self.config_manager.get_boolean_setting('debug'):
            self._safe_display('display_loading',f"Processing {len(new_branches)} new, {len(changed_branches)} changed branches for {repo['name']}")
        
        # Get default branch for comparison
        default_branch = self.fetcher.get_default_branch(owner, repo_name)
        
        # Filter to only branches we care about (exclude default branch from individual analysis)
        branches_to_process = [b for b in (new_branches + changed_branches) if b != default_branch]
        
        if not branches_to_process:
            if self.config_manager.get_boolean_setting('debug'):
                self._safe_display('display_no_updates', repo['name'])
            return
        
        # Process only the subset that needs processing
        individual_branches = self._process_branch_subset(branches_to_process, owner, repo_name, repo_key, default_branch, current_branch_shas)
        
        if individual_branches:
            # Display repository headline only (no main branch summary)
            version = self.fetcher.get_latest_version(owner, repo_name)
            self._safe_display('display_news_summary',
                repo['name'], "", None, False, repo['url'], version, None, None
            )
            
            # Process individual branch summaries
            show_costs = self.config_manager.get_show_costs_setting()
            for branch_data in individual_branches:
                if self.config_manager.get_boolean_setting('debug'):
                    self._safe_display('display_loading', f"Processing branch {branch_data['branch_name']}...")
                
                result = self.generator.generate_summary(branch_data)
                
                # Display individual branch summary
                self._safe_display('display_branch_summary',
                    branch_data['branch_name'], 
                    branch_data['commits_ahead'],
                    result['summary'], 
                    result.get('cost_info'),
                    show_costs,
                    branch_data.get('is_default', False),
                    branch_data.get('last_commit_timestamp')
                )
            
            # Update state for processed branches
            for branch_data in individual_branches:
                StateManager.update_branch_state(
                    self.state, repo_key,
                    branch_data['branch_name'],
                    branch_data['commits'],
                    branch_data['commits_ahead']
                )

    def _process_branch_subset(self, branches_to_process, owner, repo_name, repo_key, default_branch, current_branch_shas):
        """Process a specific subset of branches"""
        individual_branch_data = []
        max_commits = self.config_manager.get_int_setting('max_commits', 10)
        min_commits = self.config_manager.get_int_setting('min_branch_commits', 1)
        
        for branch_name in branches_to_process:
            # Get comparison data first (now uses adaptive logic)
            comparison = self.fetcher.get_branch_comparison(owner, repo_name, default_branch, branch_name)
            commits_ahead = comparison.get('ahead_by', 0)
            
            # Get commits for AI analysis if branch has commits ahead
            if commits_ahead > 0:
                all_branch_commits = self.fetcher.get_branch_commits_since_base(
                    owner, repo_name, branch_name, default_branch, limit=max_commits
                )
                
                # Filter branch commits based on saved state
                repo_state = self.state.get(repo_key, {})
                branch_states = repo_state.get('branches', {})
                last_branch_commit = branch_states.get(branch_name, {}).get('last_commit')
                
                branch_commits = filter_commits_since_last_processed(all_branch_commits, last_branch_commit)
            else:
                branch_commits = []
            
            if commits_ahead >= min_commits and branch_commits:
                # Get latest commit timestamp for this specific branch
                try:
                    branch_timestamp = self.fetcher.get_latest_commit_timestamp(owner, repo_name, branch_name)
                except Exception:
                    branch_timestamp = None
                
                # Prepare individual branch data for AI summary
                branch_data = {
                    'name': f"{repo_name} - {branch_name} branch",
                    'branch_name': branch_name,
                    'commits_ahead': len(branch_commits),
                    'commits': branch_commits,
                    'is_default': False,
                    'parent_branch': default_branch,
                    'last_commit_timestamp': branch_timestamp,
                }
                individual_branch_data.append(branch_data)
        
        return individual_branch_data