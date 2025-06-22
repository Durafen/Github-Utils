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
            
            # Build branches section for multi-branch analysis
            branches_section = self._build_branches_section(repo_data.get('branches', []))
            
            prompt = self.prompt_manager.build_prompt(
                repo_name=repo_data['name'],
                fork_name=repo_data['fork_name'],
                fork_url=repo_data['fork_url'],
                commits_ahead=repo_data['commits_ahead'],
                total_branches_analyzed=repo_data.get('total_branches_analyzed', 1),
                commits_section=commits_section,
                branches_section=branches_section,
                parent_readme=repo_data.get('parent_readme', 'No README found'),
                fork_readme_diff=repo_data.get('fork_readme_diff', 'No README changes'),
                bullet_count=self.config_manager.get_setting('branch_summary_bullets', '2-5')
            )
        else:
            # Regular news summary prompt
            commits_section = self._build_commits_section(repo_data.get('commits', []))
            releases_section = self._build_releases_section(repo_data.get('releases', []))
            
            # NEW: Branch analysis section for news
            branch_analysis = repo_data.get('branch_analysis')
            if branch_analysis and branch_analysis.get('has_updates'):
                branches_section = self._build_news_branches_section(branch_analysis)
            else:
                branches_section = ""
            
            # Determine bullet count based on summary type and config
            is_branch_summary = 'branch_name' in repo_data
            if is_branch_summary:
                bullet_count = self.config_manager.get_setting('branch_summary_bullets', '2-5')
            else:
                bullet_count = self.config_manager.get_setting('main_summary_bullets', '5-10')
            
            prompt = self.prompt_manager.build_prompt(
                repo_name=repo_data['name'],
                commits_section=commits_section,
                releases_section=releases_section,
                branches_section=branches_section,
                bullet_count=bullet_count
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
        
        # Save full prompt to debug file (works independently of debug mode)
        from .debug_logger import DebugLogger
        debug_logger = DebugLogger(self.config_manager)
        prompt_type = "fork_summary" if 'fork_name' in repo_data else "summary"
        debug_logger.debug_full_prompt(prompt, repo_data['name'], prompt_type)
        
        return prompt
    
    def _build_commits_section(self, commits):
        """Build commits section for prompt"""
        max_commits = self.config_manager.get_int_setting('max_commits', 10)
        commits_section = ""
        
        if commits:
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
    
    def _build_branches_section(self, branches):
        """Build branches section for multi-branch fork analysis"""
        if not branches:
            return ""
        
        max_commits = self.config_manager.get_int_setting('max_commits', 10)
        branches_section = "Branch Analysis:\n"
        
        for branch_analysis in branches:
            branch_name = branch_analysis['branch_name']
            commits_ahead = branch_analysis['commits_ahead']
            is_default = branch_analysis['is_default']
            branch_commits = branch_analysis['commits']
            
            default_marker = " [DEFAULT]" if is_default else ""
            branches_section += f"- {branch_name} ({commits_ahead} commits ahead){default_marker}\n"
            
            # Include commits for this branch (show all branches for complete context)
            if branch_commits:
                for commit in branch_commits[:max_commits]:
                    full_message = commit['commit']['message']
                    headline = full_message.split('\n')[0]  # Extract headline
                    author = commit['commit']['author']['name']
                    date = commit['commit']['author']['date']
                    
                    # Include both headline and full message
                    branches_section += f"  * {headline} (by {author} on {date})\n"
                    if len(full_message.split('\n')) > 1:
                        # Add full message if it has more than just the headline
                        body = '\n'.join(full_message.split('\n')[1:]).strip()
                        if body:
                            formatted_body = body.replace('\n', '\n    ')  # Extra indentation for branch commits
                            branches_section += f"    Full message: {formatted_body}\n"
        
        return branches_section
    
    def _build_news_branches_section(self, branch_analysis):
        """Build branch analysis section for news prompt"""
        if not branch_analysis or not branch_analysis.get('branches'):
            return ""
        
        section = "BRANCH ANALYSIS:\n"
        section += f"Default branch: {branch_analysis.get('default_branch', 'main')}\n"
        section += f"Branches analyzed: {branch_analysis.get('total_analyzed', 0)}\n\n"
        
        for branch in branch_analysis['branches']:
            branch_name = branch['branch_name']
            commits_ahead = branch['commits_ahead']
            commits = branch.get('commits', [])
            
            section += f"Branch '{branch_name}' (+{commits_ahead} commits ahead):\n"
            
            # Include recent commits for context
            for commit in commits[:3]:  # Limit to 3 commits per branch
                message = commit.get('message', '').split('\n')[0][:80]  # First line, max 80 chars
                author = commit.get('author', 'Unknown')
                section += f"  - {message} (by {author})\n"
            
            section += "\n"
        
        return section
    
