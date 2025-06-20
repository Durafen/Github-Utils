import subprocess
import json


class SummaryGenerator:
    def __init__(self):
        self.claude_cmd = ["/Users/Duracula 1/.claude/local/claude", "-p"]
    
    def generate_summary(self, repo_data):
        """Use Claude CLI to generate summary"""
        prompt = self._build_prompt(repo_data)
        summary = self._call_claude(prompt)
        return summary
    
    def _build_prompt(self, repo_data):
        """Build prompt for Claude with commit/release info"""
        prompt = f"Summarize recent activity for {repo_data['name']} repository:\n\n"
        
        if repo_data.get('commits'):
            prompt += "Recent Commits:\n"
            for commit in repo_data['commits'][:5]:
                message = commit['commit']['message'].split('\n')[0]
                author = commit['commit']['author']['name']
                date = commit['commit']['author']['date']
                prompt += f"- {message} (by {author} on {date})\n"
            prompt += "\n"
        
        if repo_data.get('releases'):
            prompt += "Recent Releases:\n"
            for release in repo_data['releases'][:3]:
                name = release['name'] or release['tag_name']
                date = release['published_at']
                prompt += f"- {name} (published {date})\n"
            prompt += "\n"
        
        prompt += "Please provide a concise summary (2-3 sentences) of the key changes and updates."
        return prompt
    
    def _call_claude(self, prompt):
        """Execute Claude CLI with subprocess"""
        try:
            result = subprocess.run(
                self.claude_cmd + [prompt],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode != 0:
                return f"Error generating summary: {result.stderr}"
            return result.stdout.strip()
        except subprocess.TimeoutExpired:
            return "Summary generation timed out"
        except Exception as e:
            return f"Error calling Claude: {str(e)}"