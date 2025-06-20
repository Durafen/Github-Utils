import sys


class TerminalDisplay:
    def __init__(self):
        pass
    
    def display_summary(self, repo_name, summary):
        """Display formatted summary with simple formatting"""
        print(f"\n{'='*60}")
        print(f"📊 {repo_name} Summary")
        print(f"{'='*60}")
        print(summary)
        print(f"{'='*60}\n")
    
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
        print(f"✓ {repo_name}: No new updates since last check")