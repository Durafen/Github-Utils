#!/usr/bin/env python3
import sys
from modules.news_processor import NewsProcessor
from modules.forks_processor import ForksProcessor
from modules.config_manager import ConfigManager


def is_github_url(arg):
    """Check if argument is a GitHub URL"""
    return arg.startswith(('https://github.com/', 'http://github.com/', 'github.com/'))


def extract_repo_info(url, fetcher=None, include_repo_key=False):
    """Extract owner and repo name from GitHub URL - consolidated utility function"""
    from modules.url_utils import extract_repo_info as _extract_repo_info
    return _extract_repo_info(url, fetcher, include_repo_key)


def create_temp_repository(url):
    """Create temporary repository structure from URL"""
    owner, repo_name = extract_repo_info(url)
    return {
        'name': repo_name,
        'url': url
    }


def add_command():
    """Add a repository to config"""
    if len(sys.argv) < 3:
        print("Usage: ./gh-utils.py add <github_url> [name]")
        print("Example: ./gh-utils.py add https://github.com/owner/repo [custom-name]")
        sys.exit(1)
    
    url = sys.argv[2]
    
    # Extract name from URL if not provided
    if len(sys.argv) > 3:
        name = sys.argv[3]
    else:
        # Extract repo name from URL
        owner, repo_name = extract_repo_info(url)
        name = repo_name
    
    try:
        config_manager = ConfigManager()
        config_manager.add_repository(name, url)
        print(f"✅ Added repository: {name} -> {url}")
    except Exception as e:
        print(f"❌ Error adding repository: {e}")
        sys.exit(1)


def remove_command():
    """Remove a repository from config"""
    if len(sys.argv) < 3:
        print("Usage: ./gh-utils.py remove <name_or_url>")
        print("Example: ./gh-utils.py remove repo-name")
        print("Example: ./gh-utils.py remove https://github.com/owner/repo")
        sys.exit(1)
    
    identifier = sys.argv[2]
    
    try:
        config_manager = ConfigManager()
        if config_manager.remove_repository(identifier):
            print(f"✅ Removed repository: {identifier}")
        else:
            print(f"❌ Repository not found: {identifier}")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Error removing repository: {e}")
        sys.exit(1)


def list_command():
    """List all configured repositories with last commit info"""
    try:
        config_manager = ConfigManager()
        repos = config_manager.list_repositories()
        
        if not repos:
            print("No repositories configured")
            return
        
        # Load state to get last commit info
        state = config_manager.load_state() if config_manager.get_boolean_setting('save_state', 'true') else {}
        
        print("Configured repositories:")
        for repo in repos:
            try:
                # Extract owner/repo for state key
                owner, repo_name = extract_repo_info(repo['url'])
                repo_key = f"{owner}/{repo_name}" if owner else repo_name
                
                # Get last commit info
                last_commit = state.get(repo_key, {}).get('last_commit', 'Not tracked')
                last_check = state.get(repo_key, {}).get('last_check', 'Never')
                
                if last_check != 'Never':
                    # Format the datetime nicely
                    try:
                        from datetime import datetime
                        check_time = datetime.fromisoformat(last_check)
                        last_check = check_time.strftime('%Y-%m-%d %H:%M')
                    except:
                        pass
                
                print(f"  {repo['name']} -> {repo['url']}")
                print(f"    Last commit: {last_commit[:8] if last_commit != 'Not tracked' else last_commit}")
                print(f"    Last check:  {last_check}")
                
            except Exception:
                # Fallback to simple display if parsing fails
                print(f"  {repo['name']} -> {repo['url']}")
                print(f"    Status: Unable to parse")
                
    except Exception as e:
        print(f"❌ Error listing repositories: {e}")
        sys.exit(1)


def clear_command():
    """Clear state for a specific repository"""
    if len(sys.argv) < 3:
        print("Usage: ./gh-utils.py clear <repo_name>")
        print("Example: ./gh-utils.py clear ccusage")
        print("This will reset tracking for the repository (next run will show all recent activity)")
        sys.exit(1)
    
    repo_name = sys.argv[2]
    
    try:
        config_manager = ConfigManager()
        if config_manager.clear_state(repo_name):
            print(f"Cleared state for repository: {repo_name}")
            print("Next run will treat this repository as first-time and show all recent activity")
        else:
            print(f"No state to clear for: {repo_name}")
            print("Repository already has clean state")
    except Exception as e:
        print(f"❌ Error clearing repository state: {e}")
        sys.exit(1)


def resolve_repository_argument(arg):
    """
    Unified repository resolution: URL or alias
    Returns: list of repositories to process
    """
    if is_github_url(arg):
        # URL case - create temp repository
        return [create_temp_repository(arg)]
    else:
        # Alias case - find in config
        config_manager = ConfigManager()
        repo = config_manager.find_repository_by_alias(arg)
        if repo:
            return [repo]
        else:
            print(f"❌ Repository alias '{arg}' not found")
            print("Use './gh-utils.py list' to see configured repositories")
            sys.exit(1)


def execute_processor(processor_type, repositories=None, debug_override=None):
    """Execute a processor with error handling"""
    processors = {
        'news': NewsProcessor,
        'forks': ForksProcessor,
    }
    
    if processor_type not in processors:
        print(f"Unknown processor type: {processor_type}")
        print(f"Available processors: {', '.join(processors.keys())}")
        sys.exit(1)
    
    try:
        if repositories:
            processor = processors[processor_type](repositories=repositories, debug_override=debug_override)
        else:
            processor = processors[processor_type](debug_override=debug_override)
        processor.execute()
    except Exception as e:
        if repositories:
            repo_name = repositories[0].get('name', 'unknown') if repositories else 'unknown'
            print(f"❌ Error processing repository '{repo_name}': {e}")
        else:
            print(f"❌ Error: {e}")
        sys.exit(1)


def handle_repo_with_processor(repo_arg, processor_type='news', debug_override=None):
    """Handle repository argument with optional processor type"""
    repositories = resolve_repository_argument(repo_arg)
    execute_processor(processor_type, repositories, debug_override)


def handle_alias_or_url_command(command, debug_override):
    """Handle commands that might be repository aliases or URLs"""
    # Check if it's a URL
    if is_github_url(command):
        processor_type = sys.argv[2].lower() if len(sys.argv) > 2 else 'news'
        handle_repo_with_processor(command, processor_type, debug_override)
        return True
    
    # Check if it's a valid alias (but not a known command)
    if command not in ['news', 'forks', 'add', 'remove', 'list', 'clear']:
        config_manager = ConfigManager()
        if config_manager.find_repository_by_alias(command):
            processor_type = sys.argv[2].lower() if len(sys.argv) > 2 else 'news'
            handle_repo_with_processor(command, processor_type, debug_override)
            return True
    
    return False


def show_help():
    """Display help information"""
    print("Usage:")
    print("  ./gh-utils.py [news] [--debug]       - Show repository news (default)")
    print("  ./gh-utils.py forks [--debug]        - Analyze repository forks")
    print("  ./gh-utils.py <repo> [news] [--debug] - Process repository by URL/alias for news (default)")
    print("  ./gh-utils.py <repo> forks [--debug] - Process repository by URL/alias for forks")
    print("  ./gh-utils.py news <repo> [--debug] - Process repository by URL/alias for news")
    print("  ./gh-utils.py forks <repo> [--debug] - Process repository by URL/alias for forks")
    print("  ./gh-utils.py add <url> [name]      - Add repository")
    print("  ./gh-utils.py remove <name>         - Remove repository")
    print("  ./gh-utils.py list                  - List repositories")
    print("  ./gh-utils.py clear <name>          - Clear repository state")
    print("")
    print("Options:")
    print("  --debug                             - Enable debug mode (overrides config.txt setting)")
    print("")
    print("Examples:")
    print("  ./gh-utils.py news ccusage           - Process 'ccusage' alias for news")
    print("  ./gh-utils.py forks ccusage          - Process 'ccusage' alias for forks")
    print("  ./gh-utils.py ccusage                - Process 'ccusage' alias for news (default)")
    print("  ./gh-utils.py ccusage forks          - Process 'ccusage' alias for forks")
    print("  ./gh-utils.py news --debug           - Process all repositories with debug output")
    print("  ./gh-utils.py forks ccusage --debug  - Process 'ccusage' for forks with debug output")


def news_command():
    """News command using new processor architecture"""
    try:
        processor = NewsProcessor()
        processor.execute()
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


def main():
    """Main entry point with simplified command routing"""
    # Check for --debug flag and remove it from arguments
    debug_override = '--debug' in sys.argv
    if debug_override:
        sys.argv = [arg for arg in sys.argv if arg != '--debug']
    
    command = sys.argv[1].lower() if len(sys.argv) > 1 else 'news'
    
    # Handle repository aliases and URLs (e.g., ./gh-utils.py <repo> [processor])
    if handle_alias_or_url_command(command, debug_override):
        return
    
    # Handle processor commands (e.g., ./gh-utils.py news [repo])
    if command in ['news', 'forks']:
        if len(sys.argv) > 2:
            # Process specific repository: ./gh-utils.py news <repo>
            handle_repo_with_processor(sys.argv[2], command, debug_override)
        else:
            # Process all repositories: ./gh-utils.py news
            execute_processor(command, debug_override=debug_override)
        return
    
    # Handle management commands
    command_handlers = {
        'add': add_command,
        'remove': remove_command,
        'list': list_command,
        'clear': clear_command,
    }
    
    if command in command_handlers:
        command_handlers[command]()
    else:
        print(f"Unknown command: {command}")
        show_help()
        sys.exit(1)


if __name__ == "__main__":
    main()