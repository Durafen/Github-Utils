import os
from .ai_provider import create_ai_provider
from .prompt_manager import PromptManager
from .display import get_terminal_width


class SummaryGenerator:
    def __init__(self, config_manager, template_name='summary'):
        self.config_manager = config_manager
        self.ai_provider = create_ai_provider(config_manager)
        self.prompt_manager = PromptManager(template_name)
    
    def generate_summary(self, repo_data):
        """Generate summary using configured AI provider"""
        prompt = self._build_prompt(repo_data)
        result = self.ai_provider.generate_summary(prompt)
        return result
    
    def _build_prompt(self, repo_data):
        """Build prompt using PromptManager"""
        debug_mode = self.config_manager.get_boolean_setting('debug')
        
        # Check if this is a fork analysis or regular summary
        if 'fork_name' in repo_data:
            # Fork analysis prompt
            commits_section = self._build_commits_section(repo_data.get('commits', []))
            
            prompt = self.prompt_manager.build_prompt(
                repo_name=repo_data['name'],
                fork_name=repo_data['fork_name'],
                fork_url=repo_data['fork_url'],
                commits_ahead=repo_data['commits_ahead'],
                commits_section=commits_section,
                parent_readme=repo_data.get('parent_readme', 'No README found'),
                fork_readme_section=repo_data.get('fork_readme_section', 'No README changes')
            )
        else:
            # Regular news summary prompt
            commits_section = self._build_commits_section(repo_data.get('commits', []))
            releases_section = self._build_releases_section(repo_data.get('releases', []))
            
            prompt = self.prompt_manager.build_prompt(
                repo_name=repo_data['name'],
                commits_section=commits_section,
                releases_section=releases_section
            )
        
        # Show summary of prompt content in debug mode (headlines only)
        if debug_mode:
            from .debug_logger import DebugLogger
            debug_logger = DebugLogger(self.config_manager)
            debug_logger.debug("Prompt summary:")
            if repo_data.get('commits'):
                max_commits = self.config_manager.get_int_setting('max_commits', 10)
                debug_logger.debug(f"  Commits ({len(repo_data['commits'][:max_commits])}):")
                for commit in repo_data['commits'][:max_commits]:
                    headline = commit['commit']['message'].split('\n')[0]
                    debug_logger.debug(f"    - {headline}")
            if repo_data.get('releases'):
                max_releases = self.config_manager.get_int_setting('max_releases', 10)
                debug_logger.debug(f"  Releases ({len(repo_data['releases'][:max_releases])}):")
                for release in repo_data['releases'][:max_releases]:
                    name = release['name'] or release['tag_name']
                    debug_logger.debug(f"    - {name}")
            debug_logger.debug(f"  Total prompt length: {len(prompt)} characters")
            debug_logger.debug("="*min(50, get_terminal_width()))
        
        return prompt
    
    def _build_commits_section(self, commits):
        """Build commits section for prompt"""
        max_commits = self.config_manager.get_int_setting('max_commits', 10)
        commits_section = ""
        
        if commits:
            commits_section = "Recent Commits:\n"
            for commit in commits[:max_commits]:
                full_message = commit['commit']['message']
                headline = full_message.split('\n')[0]  # Extract headline
                author = commit['commit']['author']['name']
                date = commit['commit']['author']['date']
                
                # Include both headline and full message
                commits_section += f"- {headline} (by {author} on {date})\n"
                if len(full_message.split('\n')) > 1:
                    # Add full message if it has more than just the headline
                    body = '\n'.join(full_message.split('\n')[1:]).strip()
                    if body:
                        formatted_body = body.replace('\n', '\n  ')
                        commits_section += f"  Full message: {formatted_body}\n"
        
        return commits_section
    
    def _build_releases_section(self, releases):
        """Build releases section for prompt"""
        max_releases = self.config_manager.get_int_setting('max_releases', 10)
        releases_section = ""
        
        if releases:
            releases_section = "Recent Releases:\n"
            for release in releases[:max_releases]:
                name = release['name'] or release['tag_name']
                date = release['published_at']
                release_notes = release.get('body', '').strip()
                
                if release_notes:
                    # Format multi-line release notes with proper indentation
                    formatted_notes = release_notes.replace('\n', '\n  ')
                    releases_section += f"- {name} (published {date})\n  Release Notes: {formatted_notes}\n"
                else:
                    releases_section += f"- {name} (published {date})\n"
        
        return releases_section
    
