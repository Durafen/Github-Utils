"""URL parsing utilities - consolidated extract_repo_info functionality"""

def extract_repo_info(url, fetcher=None, include_repo_key=False):
    """Extract owner and repo name from GitHub URL - consolidated utility function
    
    Args:
        url: GitHub URL to parse
        fetcher: Optional GitHubFetcher instance (created if not provided)
        include_repo_key: If True, returns (owner, repo_name, repo_key), otherwise (owner, repo_name)
    
    Returns:
        tuple: (owner, repo_name) or (owner, repo_name, repo_key) based on include_repo_key
    """
    try:
        if fetcher is None:
            from .github_fetcher import GitHubFetcher
            fetcher = GitHubFetcher()
        
        owner, repo_name = fetcher.extract_owner_repo(url)
        
        if include_repo_key:
            repo_key = f"{owner}/{repo_name}".lower() if owner else repo_name.lower()
            return owner, repo_name, repo_key
        else:
            return owner, repo_name
            
    except Exception:
        # Fallback: extract name from URL manually
        repo_name = url.rstrip('/').split('/')[-1] if '/' in url else url
        
        if include_repo_key:
            repo_key = repo_name.lower()
            return None, repo_name, repo_key
        else:
            return None, repo_name