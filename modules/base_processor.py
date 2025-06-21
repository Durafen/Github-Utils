from abc import ABC, abstractmethod
from datetime import datetime

class BaseProcessor(ABC):
    """Abstract base class for repository processors"""
    
    def __init__(self, template_name='summary', repositories=None):
        """Initialize processor with components"""
        from .config_manager import ConfigManager
        from .github_fetcher import GitHubFetcher
        from .summary_generator import SummaryGenerator
        from .display import TerminalDisplay
        
        self.config_manager = ConfigManager('config.txt')
        self.repos = repositories or self.config_manager.load_repositories()
        self.state = self._load_state_if_enabled()
        
        # Initialize components with error handling
        try:
            self.fetcher = GitHubFetcher()
            self.generator = SummaryGenerator(self.config_manager, template_name)
            self.display = TerminalDisplay()
        except RuntimeError as e:
            print(f"❌ Setup Error: {e}")
            raise
    
    def _load_state_if_enabled(self):
        """Load state if save_state is enabled"""
        if self.config_manager.get_boolean_setting('save_state', 'true'):
            return self.config_manager.load_state()
        return {}
    
    def _save_state_if_enabled(self):
        """Save state if save_state is enabled"""
        if self.config_manager.get_boolean_setting('save_state', 'true'):
            try:
                self.config_manager.save_state(self.state)
                if self.config_manager.get_boolean_setting('debug'):
                    print("✅ State saved successfully")
            except Exception as e:
                print(f"⚠️  Warning: Could not save state: {e}")
    
    def execute(self):
        """Template method for command execution"""
        if not self.repos:
            self.display.display_error("No repositories configured in config.txt")
            return
            
        for repo in self.repos:
            try:
                self._process_repository(repo)
            except Exception as e:
                self.display.display_error(f"Failed to process {repo['name']}: {str(e)}")
                continue
        
        self._save_state_if_enabled()
    
    @abstractmethod
    def _process_repository(self, repo):
        """Subclass-specific repository processing logic"""
        pass