"""Shared utilities for repository state management"""

from datetime import datetime

class StateManager:
    """Utility for managing repository state updates"""
    
    @staticmethod
    def update_basic_repository_state(state, repo_key, commits=None, releases=None, fetcher=None, owner=None, repo_name=None):
        """
        Update basic repository state with commits and releases
        
        Args:
            state: The state dictionary to update
            repo_key: Repository key (owner/repo format)
            commits: List of commits (newest first)
            releases: List of releases (newest first)
            fetcher: GitHubFetcher instance (optional, for getting latest commit SHA)
            owner: Repository owner (required if fetcher provided)
            repo_name: Repository name (required if fetcher provided)
        """
        updated_state = state.get(repo_key, {})
        updated_state['last_check'] = datetime.now().isoformat()
        
        # Update commit state
        if commits:
            if fetcher and owner and repo_name:
                # Use fetcher to get the actual latest commit SHA
                latest_sha = fetcher.get_latest_commit_sha(owner, repo_name)
                updated_state['last_commit'] = latest_sha
            else:
                # Use the latest commit from provided list
                updated_state['last_commit'] = commits[-1]['sha']
        
        # Update release state
        if releases:
            latest_release_id = releases[0]['id']
            updated_state['last_release'] = str(latest_release_id)
        
        state[repo_key] = updated_state
    
    @staticmethod
    def update_branch_state(state, repo_key, branch_name, branch_commits, commits_ahead):
        """
        Update state for a specific branch
        
        Args:
            state: The state dictionary to update
            repo_key: Repository key (owner/repo format)
            branch_name: Name of the branch
            branch_commits: List of commits for this branch
            commits_ahead: Number of commits ahead
        """
        current_state = state.get(repo_key, {})
        
        if 'branches' not in current_state:
            current_state['branches'] = {}
        
        # Update branch-specific state
        current_state['branches'][branch_name] = {
            'last_commit': branch_commits[-1]['sha'] if branch_commits else None,
            'commits_ahead': commits_ahead,
            'last_check': datetime.now().isoformat()
        }
        
        current_state['last_branch_check'] = datetime.now().isoformat()
        state[repo_key] = current_state
    
    @staticmethod
    def update_fork_state(state, repo_key, fork_info):
        """
        Update state for fork analysis with multi-branch support
        
        Args:
            state: The state dictionary to update
            repo_key: Repository key (owner/repo format)
            fork_info: Fork information dictionary containing:
                - fork_name: Full fork name (owner/repo)
                - branches: List of branch analysis results
                - all_processed_branches: All branches processed (for state saving)
        """
        updated_state = state.get(repo_key, {})
        
        # Initialize fork tracking section
        if 'processed_forks' not in updated_state:
            updated_state['processed_forks'] = {}
        
        # Update fork-specific state
        fork_key = fork_info['fork_name']
        
        # Multi-branch state format - save ALL processed branches
        branch_states = {}
        branches_to_save = fork_info.get('all_processed_branches', fork_info['branches'])
        
        for branch_analysis in branches_to_save:
            branch_name = branch_analysis['branch_name']
            branch_commits = branch_analysis['commits']
            
            # For state saving, use original_commits to get the latest SHA even when filtered to 0
            original_commits = branch_analysis.get('original_commits', branch_commits)
            latest_commit_sha = None
            if original_commits:
                latest_commit_sha = original_commits[-1]['sha']
            elif branch_commits:
                latest_commit_sha = branch_commits[-1]['sha']
            
            branch_states[branch_name] = {
                'last_ahead_commit': latest_commit_sha,
                'commits_ahead': branch_analysis['commits_ahead'],
                'last_check': datetime.now().isoformat()
            }
        
        updated_state['processed_forks'][fork_key] = {
            'branches': branch_states,
            'default_branch': next((b['branch_name'] for b in fork_info['branches'] if b.get('is_default')), 'main'),
            'total_commits_ahead': fork_info['commits_ahead'],
            'last_check': datetime.now().isoformat()
        }
        
        # Update general fork check timestamp
        updated_state['last_fork_check'] = datetime.now().isoformat()
        state[repo_key] = updated_state
    
    @staticmethod
    def should_process_fork_by_state(state, repo_key, fork_name, branch_analyses, save_state_enabled=True):
        """
        Check if multi-branch fork needs processing based on saved state
        
        Args:
            state: The state dictionary to check
            repo_key: Repository key (owner/repo format)
            fork_name: Full fork name (owner/repo)
            branch_analyses: List of branch analysis results
            save_state_enabled: Whether state saving is enabled
            
        Returns:
            bool: True if fork needs processing
        """
        if not save_state_enabled:
            return True
            
        repo_state = state.get(repo_key, {})
        processed_forks = repo_state.get('processed_forks', {})
        
        if fork_name not in processed_forks:
            return True
        
        # Check if any branch has new commits
        fork_state = processed_forks[fork_name]
        saved_branches = fork_state.get('branches', {})
        
        for branch_analysis in branch_analyses:
            branch_name = branch_analysis['branch_name']
            current_commits = branch_analysis['commits']
            
            if not current_commits:
                continue
                
            current_latest_commit = current_commits[-1]['sha']
            saved_latest_commit = saved_branches.get(branch_name, {}).get('last_ahead_commit')
            
            if current_latest_commit != saved_latest_commit:
                return True
        
        return False
    
    @staticmethod
    def should_process_branch_by_state(state, repo_key, branch_name, branch_commits, save_state_enabled=True):
        """
        Check if branch needs processing based on state
        
        Args:
            state: The state dictionary to check
            repo_key: Repository key (owner/repo format)
            branch_name: Name of the branch
            branch_commits: List of commits for this branch
            save_state_enabled: Whether state saving is enabled
            
        Returns:
            bool: True if branch needs processing
        """
        if not save_state_enabled:
            return True
            
        if not branch_commits:
            return False
            
        repo_state = state.get(repo_key, {})
        branch_states = repo_state.get('branches', {})
        
        if branch_name not in branch_states:
            return True  # New branch
            
        current_latest = branch_commits[-1]['sha']
        saved_latest = branch_states[branch_name].get('last_commit')
        
        return current_latest != saved_latest  # Has new commits

    @staticmethod
    def needs_repository_processing(state, repo_key, current_main_sha, current_branch_shas):
        """
        Determine if repository needs any processing based on state comparison
        
        Args:
            state: The state dictionary to check
            repo_key: Repository key (owner/repo format)  
            current_main_sha: Current main branch SHA
            current_branch_shas: Dictionary of branch_name -> sha
            
        Returns:
            tuple: (needs_processing: bool, new_branches: list, changed_branches: list)
        """
        repo_state = state.get(repo_key, {})
        
        # Check main branch first
        saved_main_sha = repo_state.get('last_commit')
        main_changed = saved_main_sha != current_main_sha
        
        # Check branches
        saved_branches = repo_state.get('branches', {})
        new_branches = []
        changed_branches = []
        
        # Find new and changed branches
        for branch_name, current_sha in current_branch_shas.items():
            if branch_name not in saved_branches:
                new_branches.append(branch_name)
            else:
                saved_sha = saved_branches[branch_name].get('last_commit')
                if saved_sha != current_sha:
                    changed_branches.append(branch_name)
        
        needs_processing = main_changed or new_branches or changed_branches
        return needs_processing, new_branches, changed_branches

    @staticmethod  
    def get_stale_branches(state, repo_key, current_branch_shas):
        """
        Find branches that exist in state but not in current repo (deleted branches)
        
        Args:
            state: The state dictionary to check
            repo_key: Repository key (owner/repo format)
            current_branch_shas: Dictionary of current branch_name -> sha
            
        Returns:
            list: Names of stale branches to clean up
        """
        repo_state = state.get(repo_key, {})
        saved_branches = repo_state.get('branches', {})
        current_branch_names = set(current_branch_shas.keys())
        saved_branch_names = set(saved_branches.keys())
        
        stale_branches = saved_branch_names - current_branch_names
        return list(stale_branches)

    @staticmethod
    def bulk_branch_state_check(state, repo_key, branch_sha_map):
        """
        Check multiple branches at once for changes
        
        Args:
            state: The state dictionary to check
            repo_key: Repository key (owner/repo format)
            branch_sha_map: Dictionary of branch_name -> sha
            
        Returns:
            dict: Map of branch_name -> needs_processing (bool)
        """
        repo_state = state.get(repo_key, {})
        saved_branches = repo_state.get('branches', {})
        
        processing_map = {}
        for branch_name, current_sha in branch_sha_map.items():
            if branch_name not in saved_branches:
                processing_map[branch_name] = True  # New branch
            else:
                saved_sha = saved_branches[branch_name].get('last_commit')
                processing_map[branch_name] = (saved_sha != current_sha)
        
        return processing_map

    @staticmethod
    def main_branch_unchanged(state, repo_key, current_main_sha):
        """
        Quick check if main branch is unchanged
        
        Args:
            state: The state dictionary to check
            repo_key: Repository key (owner/repo format)
            current_main_sha: Current main branch SHA
            
        Returns:
            bool: True if main branch hasn't changed
        """
        repo_state = state.get(repo_key, {})
        saved_main_sha = repo_state.get('last_commit')
        return saved_main_sha == current_main_sha

    @staticmethod
    def clean_stale_branches(state, repo_key, stale_branch_names):
        """
        Remove stale branches from state
        
        Args:
            state: The state dictionary to update
            repo_key: Repository key (owner/repo format)
            stale_branch_names: List of branch names to remove
        """
        repo_state = state.get(repo_key, {})
        if 'branches' not in repo_state:
            return
            
        for branch_name in stale_branch_names:
            if branch_name in repo_state['branches']:
                del repo_state['branches'][branch_name]
        
        state[repo_key] = repo_state