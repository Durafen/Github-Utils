import sys
import shutil
from datetime import datetime, timezone
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

def format_time_ago(timestamp_str):
    """Format timestamp as 'X hours/days/months ago'"""
    if not timestamp_str:
        return ""
    
    try:
        # Parse GitHub timestamp (ISO 8601 format)
        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        
        # Calculate time difference
        diff = now - timestamp
        total_seconds = diff.total_seconds()
        
        # Calculate time units
        hours = total_seconds / 3600
        days = total_seconds / (3600 * 24)
        months = days / 30.44  # Average month length
        
        # Format based on requirements
        if hours < 24:
            return f"{int(hours)}h ago"
        elif days < 365:
            return f"{int(days)}d ago"
        else:
            return f"{int(months)}mo ago"
            
    except Exception:
        return ""


class TerminalDisplay:
    def __init__(self):
        self.cost_tracker = CostTracker()
    
    def _get_separator_width(self, max_width=80):
        """Get terminal width, capped at max_width"""
        return get_separator_width(max_width)
    
    def display_summary(self, repo_name, summary, cost_info=None, show_costs=False, repo_url=None, version=None, last_commit_timestamp=None):
        """Display formatted summary with optional cost information and clickable title"""
        title = self._build_base_title(repo_name, repo_url)
        title = self._add_version_to_title(title, version)
        title = self._add_timestamp_to_title(title, last_commit_timestamp)
        title = self._add_cost_to_title(title, cost_info, show_costs)
        self._print_summary_section(title, summary)
    
    def _create_hyperlink(self, text, url):
        """Create ANSI hyperlink using OSC 8 escape sequence"""
        return f"\033]8;;{url}\033\\{text}\033]8;;\033\\"
    
    def _format_cost_info(self, cost_info):
        """Format cost information for display"""
        return self.cost_tracker.format_cost_info(cost_info)
    
    def _build_base_title(self, repo_name, repo_url, title_prefix="📊", title_suffix="Summary"):
        """Build base title with clickable hyperlink if URL provided"""
        if repo_url:
            clickable_name = self._create_hyperlink(repo_name, repo_url)
            return f"{title_prefix} {clickable_name} {title_suffix}"
        else:
            return f"{title_prefix} {repo_name} {title_suffix}"
    
    def _add_version_to_title(self, title, version):
        """Add version information to title if available"""
        if version:
            title += f" - {version}"
        return title
    
    def _add_timestamp_to_title(self, title, last_commit_timestamp):
        """Add timestamp information to title if available"""
        if last_commit_timestamp:
            time_ago = format_time_ago(last_commit_timestamp)
            if time_ago:
                title += f" ({time_ago})"
        return title
    
    def _add_cost_to_title(self, title, cost_info, show_costs):
        """Add cost information to title if available and requested"""
        if show_costs and cost_info:
            cost_str = self._format_cost_info(cost_info)
            title += f" {cost_str}"
        return title
    
    def _print_summary_section(self, title, summary):
        """Print formatted summary section with separators"""
        width = self._get_separator_width()
        print(f"{'-'*width}")
        print(title)
        print(f"{'-'*width}")
        print(summary)
    
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
    
    def display_forks_header(self, repo_name, repo_url=None, last_commit_timestamp=None):
        """Display repository header for fork analysis"""
        header = self._build_base_title(repo_name, repo_url, "FORK ANALYSIS |", "")
        width = self._get_separator_width()
        print('=' * width)
        print(header)
        print()

    def display_fork_summary(self, repo_name, fork_name, fork_url, commits_ahead, summary, branches=None, last_commit_timestamp=None):
        """Display individual fork analysis results with optional multi-branch information"""
        width = self._get_separator_width()
        print('-' * width)
        
        # Show basic fork info with total commits ahead
        fork_title = f"🍴 {self._create_hyperlink(fork_name, fork_url)} (+{commits_ahead})"
        
        # Add timestamp if available
        if last_commit_timestamp:
            time_ago = format_time_ago(last_commit_timestamp)
            if time_ago:
                fork_title += f" ({time_ago})"
        
        print(fork_title)
        print('-' * width)
        
        # Show branch breakdown if available
        if branches:
            print("Branches:")
            for branch in branches:
                branch_name = branch['branch_name']
                branch_commits = branch['commits_ahead']
                is_default = branch.get('is_default', False)
                default_marker = " ⭐" if is_default else ""
                
                # Add timestamp for this branch if available
                branch_timestamp = branch.get('last_commit_timestamp')
                time_str = ""
                if branch_timestamp:
                    time_ago = format_time_ago(branch_timestamp)
                    if time_ago:
                        time_str = f" ({time_ago})"
                
                print(f"  ├─ {branch_name}:{default_marker} (+{branch_commits}){time_str}")
            print()
        
        print(summary)
        print()

    def display_no_active_forks(self, repo_name):
        """Display when no active forks found"""
        print(f"ℹ️  No active forks with commits ahead found for {repo_name}")
    
    def display_forks_summary(self, repo_name, active_count, total_count, total_cost_info=None, show_costs=False, repo_url=None, last_commit_timestamp=None):
        """Display repository-level fork summary with counts and costs in title format"""
        title = self._build_base_title(repo_name, repo_url, "📊", "Forks Summary")
        title += f" - ({active_count}/{total_count}"
        title = self._add_cost_to_title(title, total_cost_info, show_costs)
        title += ")"
        
        width = self._get_separator_width()
        print(f"{'='*width}")
        print(title)
        print()

    def display_news_summary(self, repo_name, summary, cost_info=None, show_costs=False, repo_url=None, version=None, branch_analysis=None, last_commit_timestamp=None, commits_count=None):
        """Enhanced news summary display with branch information"""
        title = self._build_base_title(repo_name, repo_url)
        title = self._add_version_to_title(title, version)
        
        # Add commit count if provided (new commits since last check)
        if commits_count and commits_count > 0:
            title += f" (+{commits_count})"
        
        # Add branch count indicator
        if branch_analysis and branch_analysis.get('has_updates'):
            branch_count = len(branch_analysis['branches'])
            title += f" [+{branch_count} branches]"
        
        title = self._add_timestamp_to_title(title, last_commit_timestamp)
        title = self._add_cost_to_title(title, cost_info, show_costs)
        
        # Print title with separators
        width = self._get_separator_width()
        print(f"{'-'*width}")
        print(title)
        
        # Display branch breakdown (matches fork display pattern)
        if branch_analysis and branch_analysis.get('has_updates'):
            print(f"Branches:")
            
            for i, branch in enumerate(branch_analysis['branches']):
                branch_name = branch['branch_name']
                commits_ahead = branch['commits_ahead']
                is_default = branch.get('is_default', False)
                
                # Visual indicators (match fork display)
                default_marker = " ⭐" if is_default else ""
                prefix = "├─" if i < len(branch_analysis['branches']) - 1 else "└─"
                
                print(f"  {prefix} {branch_name}: +{commits_ahead} commits{default_marker}")
            print()
        
        print(f"{'-'*width}")
        print(summary)
        print()

    def display_branch_summary(self, branch_name, commits_ahead, summary, cost_info=None, show_costs=False, is_default=False, last_commit_timestamp=None):
        """Display individual branch summary with separate section"""
        # Skip empty branches - only print if has actual summary content
        if not summary or not summary.strip():
            return
            
        # Create branch title
        if is_default:
            title = f"🌿 Main Branch ({branch_name}): +{commits_ahead} new commits"
        else:
            title = f"🌿 {branch_name} (+{commits_ahead})"
            title = self._add_timestamp_to_title(title, last_commit_timestamp)
            
        title = self._add_cost_to_title(title, cost_info, show_costs)
        self._print_summary_section(title, summary)
        print()  # Add spacing after branch summary