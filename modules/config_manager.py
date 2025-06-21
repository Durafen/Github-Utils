import json
import os
import configparser
import shutil
import sys
from datetime import datetime


class ConfigManager:
    def __init__(self, config_path='config.txt', state_path='state.json'):
        # Get the directory where this script/module is located
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # If paths are relative, make them relative to script directory
        if not os.path.isabs(config_path):
            self.config_path = os.path.join(script_dir, config_path)
        else:
            self.config_path = config_path
            
        if not os.path.isabs(state_path):
            self.state_path = os.path.join(script_dir, state_path)
        else:
            self.state_path = state_path
            
        self._config = None
    
    def _load_config(self):
        """Load INI config file"""
        if self._config is None:
            self._config = configparser.ConfigParser()
            try:
                self._config.read(self.config_path)
            except Exception as e:
                raise ValueError(f"Error reading config file {self.config_path}: {e}")
        return self._config
    
    def load_repositories(self):
        """Load repository list from config.txt"""
        try:
            config = self._load_config()
            repos = []
            if 'repositories' in config:
                for name, url in config['repositories'].items():
                    repos.append({'name': name, 'url': url})
            return repos
        except FileNotFoundError:
            return []
    
    def get_claude_cli_path(self):
        """Get Claude CLI path from environment or config"""
        # Check environment variable first
        cli_path = os.getenv('CLAUDE_CLI_PATH')
        if cli_path:
            return os.path.expanduser(cli_path)
        
        # Fallback to config file
        try:
            config = self._load_config()
            path = config.get('claude', 'claude_cli_path', fallback='claude')
            # Expand ~ to home directory
            return os.path.expanduser(path)
        except:
            return 'claude'
    
    def get_setting(self, key, default=None):
        """Get a setting value"""
        config = self._load_config()
        value = config.get('settings', key, fallback=default)
        
        # Strip inline comments if value is a string
        if isinstance(value, str) and '#' in value:
            value = value.split('#')[0].strip()
        
        return value
    
    def get_boolean_setting(self, key, default='false'):
        """Get a boolean setting value (converts 'true'/'false' strings to bool)"""
        return self.get_setting(key, default).lower() == 'true'
    
    def get_int_setting(self, key, default):
        """Get an integer setting value"""
        return int(self.get_setting(key, str(default)))
    
    def get_ai_provider(self):
        """Get AI provider from config (claude or openai)"""
        config = self._load_config()
        return config.get('ai', 'provider', fallback='claude')
    
    def get_ai_model(self):
        """Get AI model from config"""
        config = self._load_config()
        provider = self.get_ai_provider()
        
        # Try provider-specific section first, then fall back to ai section
        if provider == 'openai':
            return config.get('openai', 'model', fallback=config.get('ai', 'model', fallback=None))
        elif provider == 'claude':
            return config.get('claude', 'model', fallback=config.get('ai', 'model', fallback=None))
        else:
            return config.get('ai', 'model', fallback=None)
    
    def get_openai_api_key(self):
        """Get OpenAI API key from environment or config"""
        # Check environment variable first
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            return api_key
        
        # Fallback to config file
        config = self._load_config()
        return config.get('openai', 'api_key', fallback=None)
    
    def load_state(self):
        """Load last checked commits from state.json"""
        try:
            with open(self.state_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON in {self.state_path}")
    
    def save_state(self, state_data):
        """Save updated state back to state.json"""
        with open(self.state_path, 'w') as f:
            json.dump(state_data, f, indent=2)
    
    def add_repository(self, name, url):
        """Add a repository to config.txt"""
        config = self._load_config()
        
        # Ensure repositories section exists
        if 'repositories' not in config:
            config.add_section('repositories')
        
        # Add the repository
        config.set('repositories', name, url)
        
        # Save the updated config
        self._save_config(config)
    
    def remove_repository(self, identifier):
        """Remove a repository by name or URL"""
        config = self._load_config()
        
        if 'repositories' not in config:
            return False
        
        # Try to remove by name first
        if config.has_option('repositories', identifier):
            config.remove_option('repositories', identifier)
            self._save_config(config)
            return True
        
        # Try to remove by URL
        for name, url in config.items('repositories'):
            if url == identifier:
                config.remove_option('repositories', name)
                self._save_config(config)
                return True
        
        return False
    
    def list_repositories(self):
        """List all configured repositories"""
        return self.load_repositories()
    
    def clear_state(self, repo_name=None):
        """Clear state for a specific repository or all repositories"""
        if repo_name is None:
            # Clear entire state file
            try:
                os.remove(self.state_path)
                return True
            except FileNotFoundError:
                return False  # Already cleared
            except Exception:
                return False
        else:
            # Clear state for specific repository
            try:
                state = self.load_state()
                
                # Find the repository key (could be just name or owner/repo format)
                repo_key_to_remove = None
                for key in state.keys():
                    # Check if the key matches the repo name directly or contains it
                    if key == repo_name or key.split('/')[-1] == repo_name:
                        repo_key_to_remove = key
                        break
                
                if repo_key_to_remove:
                    del state[repo_key_to_remove]
                    self.save_state(state)
                    return True
                else:
                    return False  # Repository not found in state
            except FileNotFoundError:
                return False  # No state file exists
            except Exception:
                return False
    
    def setup_first_run(self):
        """Handle first-run configuration setup"""
        if not os.path.exists(self.config_path):
            script_dir = os.path.dirname(self.config_path)
            config_example_path = os.path.join(script_dir, 'config.example.txt')
            
            if os.path.exists(config_example_path):
                shutil.copy(config_example_path, self.config_path)
                print("📋 Created config.txt from config.example.txt")
                print("⚠️  Please edit config.txt with your actual settings before running")
                print("⚠️  Add your OpenAI API key or Claude CLI path")
                sys.exit(0)
            else:
                print("❌ No config.txt or config.example.txt found")
                print("📋 Please create config.txt with your settings")
                sys.exit(1)
    
    def _save_config(self, config):
        """Save configuration back to file"""
        with open(self.config_path, 'w') as f:
            config.write(f)