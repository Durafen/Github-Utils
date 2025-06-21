import sys
import shutil
from .cost_tracker import CostTracker


def get_terminal_width():
    """Get terminal width with fallback to 80 characters"""
    try:
        return shutil.get_terminal_size().columns
    except:
        return 80

def get_separator_width(max_width=80):
    """Get width for separator lines (80 chars max)"""
    return min(get_terminal_width(), max_width)


class TerminalDisplay:
    def __init__(self):
        self.cost_tracker = CostTracker()
    
    def _get_separator_width(self, max_width=80):
        """Get terminal width, capped at max_width"""
        return get_separator_width(max_width)
    
    def display_summary(self, repo_name, summary, cost_info=None, show_costs=False, repo_url=None, version=None):
        """Display formatted summary with optional cost information and clickable title"""
        width = self._get_separator_width()
        print(f"{'='*width}")
        
        # Create clickable title if URL is provided
        if repo_url:
            clickable_name = self._create_hyperlink(repo_name, repo_url)
            title = f"📊 {clickable_name} Summary"
        else:
            title = f"📊 {repo_name} Summary"
        
        # Add version if available
        if version:
            title += f" - {version}"
            
        if show_costs and cost_info:
            cost_str = self._format_cost_info(cost_info)
            title += f" {cost_str}"
        print(title)
        print(f"{'='*width}")
        print(summary)
        print(f"{'='*width}")
    
    def _create_hyperlink(self, text, url):
        """Create ANSI hyperlink using OSC 8 escape sequence"""
        return f"\033]8;;{url}\033\\{text}\033]8;;\033\\"
    
    def _format_cost_info(self, cost_info):
        """Format cost information for display"""
        return self.cost_tracker.format_cost_info(cost_info)
    
    def display_loading(self, message):
        """Show loading message"""
        print(f"⏳ {message}")
        sys.stdout.flush()
    
    def display_error(self, error_msg):
        """Display error messages"""
        print(f"❌ Error: {error_msg}")
    
    def display_info(self, message):
        """Display informational messages"""
        print(f"ℹ️  {message}")
    
    def display_no_updates(self, repo_name):
        """Display message when no updates found"""
        print(f"✓ No new updates since last check")
    
    def display_forks_header(self, repo_name, repo_url=None):
        """Display repository header for fork analysis"""
        width = self._get_separator_width()
        print('=' * width)
        if repo_url:
            clickable_name = self._create_hyperlink(repo_name, repo_url)
            print(f"🍴 FORK ANALYSIS | {clickable_name}")
        else:
            print(f"🍴 FORK ANALYSIS | {repo_name}")
        print()

    def display_fork_summary(self, repo_name, fork_name, fork_url, commits_ahead, summary):
        """Display individual fork analysis results"""
        width = self._get_separator_width()
        print('-' * width)
        print(f"Fork: {self._create_hyperlink(fork_name, fork_url)} (+{commits_ahead})")
        print(summary)
        print()

    def display_no_active_forks(self, repo_name):
        """Display when no active forks found"""
        print(f"ℹ️  No active forks with commits ahead found for {repo_name}")
    
    def display_forks_summary(self, repo_name, active_count, total_count, total_cost_info=None, show_costs=False, repo_url=None):
        """Display repository-level fork summary with counts and costs in title format"""
        width = self._get_separator_width()
        print(f"{'='*width}")
        
        # Create clickable title if URL is provided
        if repo_url:
            clickable_name = self._create_hyperlink(repo_name, repo_url)
            title = f"📊 {clickable_name} Forks Summary"
        else:
            title = f"📊 {repo_name} Forks Summary"
        
        # Add fork counts
        title += f" - ({active_count}/{total_count}"
        
        # Add cost information if available and requested
        if show_costs and total_cost_info:
            cost_str = self._format_cost_info(total_cost_info)
            title += f" {cost_str}"
        
        title += ")"
        print(title)
        print()