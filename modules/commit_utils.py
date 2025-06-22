"""Shared utilities for commit processing and filtering"""

def filter_commits_since_last_processed(commits, last_processed_commit):
    """
    Filter commits to only include those newer than last processed commit.
    
    Args:
        commits: List of commit objects with 'sha' field
        last_processed_commit: SHA of last processed commit
        
    Returns:
        List of commits newer than last_processed_commit
    """
    if not last_processed_commit or not commits:
        return commits
    
    # Find index of last processed commit
    last_commit_index = None
    for i, commit in enumerate(commits):
        if commit['sha'].startswith(last_processed_commit):
            last_commit_index = i
            break
    
    # If last commit found, take commits after it (newer commits)
    if last_commit_index is not None:
        return commits[last_commit_index + 1:]
    
    # If last commit not found, all commits are new
    return commits