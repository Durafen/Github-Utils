import concurrent.futures
import threading
from datetime import datetime

class ParallelBaseProcessor:
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
    def state_type(self):
        """Return the state type for this processor (override in subclasses)"""
        raise NotImplementedError("Subclasses must implement state_type property")
    
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
        
        # Initialize display lock for thread-safe output
        self._display_lock = threading.Lock()
        
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
                    self._safe_display('error', f"❌ {repo['name']}: {e}")
        
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
                self._safe_display('error', f"❌ Repository {repo_name} failed: {e}")
    
    def _safe_display(self, method_name, *args, **kwargs):
        """Generic thread-safe display wrapper"""
        with self._display_lock:
            if hasattr(self.display, method_name):
                method = getattr(self.display, method_name)
                method(*args, **kwargs)
            elif method_name in ['error', 'debug']:
                # Handle print-based methods
                print(*args)
            else:
                raise AttributeError(f"Display method '{method_name}' not found")
    
    def _save_repository_state(self, repo):
        """Save state for individual repository immediately after processing"""
        if self.config_manager.get_boolean_setting('save_state', 'true'):
            try:
                with self._state_lock:
                    self.config_manager.save_state(self.state, self.state_type)
                if self.config_manager.get_boolean_setting('debug'):
                    self._safe_display('debug', f"✅ State saved for {repo['name']}")
            except Exception as e:
                self._safe_display('error', f"⚠️  Warning: Could not save state for {repo['name']}: {e}")
    
    
    def _process_repository(self, repo):
        """Subclass-specific repository processing logic (override in subclasses)"""
        raise NotImplementedError("Subclasses must implement _process_repository method")