from datetime import datetime
from modules.config_manager import ConfigManager
from modules.github_fetcher import GitHubFetcher
from modules.summary_generator import SummaryGenerator
from modules.display import TerminalDisplay


def main():
    # 1. Load configuration and state
    config_manager = ConfigManager()
    repos = config_manager.load_repositories()
    state = config_manager.load_state()
    
    # 2. Initialize components
    try:
        fetcher = GitHubFetcher()
        generator = SummaryGenerator()
        display = TerminalDisplay()
    except RuntimeError as e:
        print(f"❌ Setup Error: {e}")
        return
    
    # Check if we have repositories configured
    if not repos:
        display.display_error("No repositories configured in config.json")
        return
    
    # 3. Process each repository
    for repo in repos:
        try:
            display.display_loading(f"Processing {repo['name']}...")
            
            # Extract owner/repo from URL
            owner, repo_name = fetcher.extract_owner_repo(repo['url'])
            repo_key = f"{owner}/{repo_name}"
            
            # Get last checked commit
            last_commit = state.get(repo_key, {}).get('last_commit')
            
            # Fetch new data
            commits = fetcher.get_commits(owner, repo_name, since=last_commit)
            releases = fetcher.get_releases(owner, repo_name)
            
            # Filter out old releases if we have state
            if last_commit and releases:
                last_check = state.get(repo_key, {}).get('last_check')
                if last_check:
                    # Simple filtering - keep releases from last 30 days for now
                    releases = releases[:2]  # Just show latest 2 releases
            
            # Generate summary if there are updates
            if commits or releases:
                repo_data = {
                    'name': repo['name'],
                    'commits': commits,
                    'releases': releases
                }
                summary = generator.generate_summary(repo_data)
                display.display_summary(repo['name'], summary)
                
                # Update state
                latest_sha = fetcher.get_latest_commit_sha(owner, repo_name)
                state[repo_key] = {
                    'last_commit': latest_sha,
                    'last_check': datetime.now().isoformat()
                }
            else:
                display.display_no_updates(repo['name'])
                
        except Exception as e:
            display.display_error(f"Failed to process {repo['name']}: {str(e)}")
            continue
    
    # 4. Save updated state
    try:
        config_manager.save_state(state)
        print("✅ State saved successfully")
    except Exception as e:
        print(f"⚠️  Warning: Could not save state: {e}")


if __name__ == "__main__":
    main()