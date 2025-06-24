import concurrent.futures
import threading
from abc import ABC, abstractmethod
from datetime import datetime

class ParallelBaseProcessor(ABC):
    """Parallel base processor for repository processing with thread safety"""
    
    def __init__(self, template_name='summary', repositories=None):
        """Initialize processor with components (same as BaseProcessor)"""
        from .config_manager import ConfigManager
        from .github_fetcher import GitHubFetcher
        from .summary_generator import SummaryGenerator
        from .display import TerminalDisplay
        
        self.config_manager = ConfigManager('config.txt')
        self.repos = repositories or self.config_manager.load_repositories()
        self.state = self._load_state_if_enabled()
        self._state_lock = threading.Lock()
        self._repo_locks = {repo['name']: threading.Lock() for repo in self.repos}
        
        # Initialize components with error handling
        try:
            debug_logger = getattr(self, 'debug_logger', None)
            self.fetcher = GitHubFetcher(debug_logger=debug_logger)
            self.generator = SummaryGenerator(self.config_manager, template_name)
            self.display = TerminalDisplay()
        except RuntimeError as e:
            print(f"❌ Setup Error: {e}")
            raise
    
    @property
    @abstractmethod
    def state_type(self):
        """Return the state type for this processor"""
        pass
    
    def _load_state_if_enabled(self):
        """Load state if save_state is enabled"""
        if self.config_manager.get_boolean_setting('save_state', 'true'):
            return self.config_manager.load_state(self.state_type)
        return {}
    
    def _save_state_if_enabled(self):
        """Save state if save_state is enabled"""
        if self.config_manager.get_boolean_setting('save_state', 'true'):
            try:
                with self._state_lock:
                    self.config_manager.save_state(self.state, self.state_type)
                if self.config_manager.get_boolean_setting('debug'):
                    print("✅ State saved successfully")
            except Exception as e:
                print(f"⚠️  Warning: Could not save state: {e}")
        
    def execute(self):
        """Parallel repository processing with configurable workers"""
        if not self.repos:
            self.display.display_error("No repositories configured in config.txt")
            return
        
        max_workers = min(len(self.repos), self.config_manager.get_int_setting('max_workers', 4))
        repo_timeout = self.config_manager.get_int_setting('repo_timeout', 60)
        
        # Start display thread for ordered output
        from queue import Queue
        self._display_queue = Queue()
        display_thread = threading.Thread(target=self._display_worker)
        display_thread.daemon = True
        display_thread.start()
        
        # Process repositories in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_repo = {
                executor.submit(self._process_repository_safe, repo): repo 
                for repo in self.repos
            }
            
            # Wait for completion with timeout
            for future in concurrent.futures.as_completed(future_to_repo, timeout=180):
                repo = future_to_repo[future]
                try:
                    future.result(timeout=repo_timeout)
                except Exception as e:
                    self._safe_display_error(f"❌ {repo['name']}: {e}")
        
        # Signal display thread to finish and wait for all output
        self._display_queue.put(None)
        display_thread.join(timeout=10)
        
        # Final state save
        self._save_state_if_enabled()
    
    def _process_repository_safe(self, repo):
        """Thread-safe wrapper for _process_repository with per-repo locking"""
        repo_name = repo['name']
        with self._repo_locks[repo_name]:
            try:
                self._process_repository(repo)
                # Save state immediately after successful processing
                self._save_repository_state(repo)
            except Exception as e:
                self._safe_display_error(f"❌ Repository {repo_name} failed: {e}")
    
    def _display_worker(self):
        """Background thread for ordered display output"""
        while True:
            item = self._display_queue.get()
            if item is None:  # Shutdown signal
                break
            item()  # Execute display function
    
    def _save_repository_state(self, repo):
        """Save state for individual repository immediately after processing"""
        if self.config_manager.get_boolean_setting('save_state', 'true'):
            try:
                with self._state_lock:
                    self.config_manager.save_state(self.state, self.state_type)
                if self.config_manager.get_boolean_setting('debug'):
                    self._safe_display_debug(f"✅ State saved for {repo['name']}")
            except Exception as e:
                self._safe_display_error(f"⚠️  Warning: Could not save state for {repo['name']}: {e}")
    
    def _safe_display_error(self, message):
        """Thread-safe error display"""
        self._display_queue.put(lambda: print(message))
    
    def _safe_display_debug(self, message):
        """Thread-safe debug display"""
        self._display_queue.put(lambda: print(message))
    
    def _safe_display_news_summary(self, repo_name, summary, cost_info, show_costs, repo_url, version, branch_name, timestamp, commit_count=None):
        """Thread-safe news summary display"""
        self._display_queue.put(lambda: self.display.display_news_summary(
            repo_name, summary, cost_info, show_costs, repo_url, version, branch_name, timestamp, commit_count
        ))
    
    def _safe_display_branch_summary(self, branch_name, commits_ahead, summary, cost_info, show_costs, is_default, timestamp):
        """Thread-safe branch summary display"""
        self._display_queue.put(lambda: self.display.display_branch_summary(
            branch_name, commits_ahead, summary, cost_info, show_costs, is_default, timestamp
        ))
    
    def _safe_display_fork_summary(self, repo_name, fork_name, fork_url, commits_ahead, summary, branches, timestamp):
        """Thread-safe fork summary display"""
        self._display_queue.put(lambda: self.display.display_fork_summary(
            repo_name, fork_name, fork_url, commits_ahead, summary, branches, timestamp
        ))
    
    def _safe_display_loading(self, message):
        """Thread-safe loading message display"""
        self._display_queue.put(lambda: self.display.display_loading(message))
    
    def _safe_display_no_updates(self, repo_name):
        """Thread-safe no updates display"""
        self._display_queue.put(lambda: self.display.display_no_updates(repo_name))
    
    def _safe_display_forks_header(self, repo_name, repo_url):
        """Thread-safe forks header display"""
        self._display_queue.put(lambda: self.display.display_forks_header(repo_name, repo_url))
    
    def _safe_display_forks_summary(self, repo_name, active_count, total_count, cost_info, show_costs, repo_url):
        """Thread-safe forks summary display"""
        self._display_queue.put(lambda: self.display.display_forks_summary(
            repo_name, active_count, total_count, cost_info, show_costs, repo_url
        ))
    
    def _safe_display_no_active_forks(self, repo_name):
        """Thread-safe no active forks display"""
        self._display_queue.put(lambda: self.display.display_no_active_forks(repo_name))
    
    def _safe_display_no_fork_changes(self, repo_name):
        """Thread-safe no fork changes display"""
        self._display_queue.put(lambda: self.display.display_no_fork_changes(repo_name))
    
    @abstractmethod
    def _process_repository(self, repo):
        """Subclass-specific repository processing logic"""
        pass