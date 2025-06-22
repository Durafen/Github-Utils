#!/usr/bin/env python3
import sys
from modules.news_processor import NewsProcessor
from modules.forks_processor import ForksProcessor
from modules.config_manager import ConfigManager


def is_github_url(arg):
    """Check if argument is a GitHub URL"""
    return arg.startswith(('https://github.com/', 'http://github.com/', 'github.com/'))


def create_temp_repository(url):
    """Create temporary repository structure from URL"""
    try:
        from modules.github_fetcher import GitHubFetcher
        fetcher = GitHubFetcher()
        owner, repo_name = fetcher.extract_owner_repo(url)
        
        return {
            'name': repo_name,
            'url': url
        }
    except Exception:
        # Fallback: extract name from URL manually
        repo_name = url.rstrip('/').split('/')[-1] if '/' in url else url
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
        try:
            from modules.github_fetcher import GitHubFetcher
            fetcher = GitHubFetcher()
            owner, repo_name = fetcher.extract_owner_repo(url)
            name = repo_name
        except:
            name = url.rstrip('/').split('/')[-1] if '/' in url else url
    
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
                from modules.github_fetcher import GitHubFetcher
                fetcher = GitHubFetcher()
                owner, repo_name = fetcher.extract_owner_repo(repo['url'])
                repo_key = f"{owner}/{repo_name}"
                
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
            print(f"✅ Cleared state for repository: {repo_name}")
            print("Next run will treat this repository as first-time and show all recent activity")
        else:
            print(f"❌ Repository state not found: {repo_name}")
            print("Repository may not exist in state or state file doesn't exist")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Error clearing repository state: {e}")
        sys.exit(1)


def news_command():
    """News command using new processor architecture"""
    try:
        processor = NewsProcessor()
        processor.execute()
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


def main():
    """Main entry point with command routing"""
    processors = {
        'news': NewsProcessor,
        'forks': ForksProcessor,
    }
    
    command = sys.argv[1].lower() if len(sys.argv) > 1 else 'news'
    
    # Check for URL-based processing
    if is_github_url(command):
        # Case 1: ./gh-utils.py <url> [processor_type]
        # Default to 'news' if no processor type specified
        processor_type = sys.argv[2].lower() if len(sys.argv) > 2 else 'news'
        
        if processor_type in processors:
            try:
                temp_repo = create_temp_repository(command)
                processor = processors[processor_type](repositories=[temp_repo])
                processor.execute()
                return
            except Exception as e:
                print(f"❌ Error processing URL: {e}")
                sys.exit(1)
        else:
            print(f"Unknown processor type: {processor_type}")
            print(f"Available processors: {', '.join(processors.keys())}")
            sys.exit(1)
    
    # Check for processor with URL as second argument
    elif command in processors and len(sys.argv) > 2 and is_github_url(sys.argv[2]):
        # Case 2: ./gh-utils.py news <url> OR ./gh-utils.py forks <url>
        try:
            temp_repo = create_temp_repository(sys.argv[2])
            processor = processors[command](repositories=[temp_repo])
            processor.execute()
            return
        except Exception as e:
            print(f"❌ Error processing URL: {e}")
            sys.exit(1)
    
    # Standard command processing
    elif command in processors:
        try:
            processor = processors[command]()
            processor.execute()
        except Exception as e:
            print(f"❌ Error: {e}")
            sys.exit(1)
    elif command == "add":
        add_command()
    elif command == "remove":
        remove_command()
    elif command == "list":
        list_command()
    elif command == "clear":
        clear_command()
    else:
        print(f"Unknown command: {command}")
        print("Usage:")
        print("  ./gh-utils.py [news]           - Show repository news (default)")
        print("  ./gh-utils.py forks            - Analyze repository forks")
        print("  ./gh-utils.py <url> [news]     - Process single URL for news (default)")
        print("  ./gh-utils.py <url> forks      - Process single URL for forks")
        print("  ./gh-utils.py news <url>       - Process single URL for news")
        print("  ./gh-utils.py forks <url>      - Process single URL for forks")
        print("  ./gh-utils.py add <url> [name] - Add repository")
        print("  ./gh-utils.py remove <name>    - Remove repository")
        print("  ./gh-utils.py list             - List repositories")
        print("  ./gh-utils.py clear <name>     - Clear repository state")
        sys.exit(1)


if __name__ == "__main__":
    main()