import json
import os
import configparser
import shutil
import sys
from datetime import datetime
from .comment_preserving_parser import CommentPreservingINIParser


class ConfigManager:
    def __init__(self, config_path='config.txt', state_path='state.json'):
        # Get the directory where this script/module is located
        self.script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # If paths are relative, make them relative to script directory
        if not os.path.isabs(config_path):
            self.config_path = os.path.join(self.script_dir, config_path)
        else:
            self.config_path = config_path
            
        if not os.path.isabs(state_path):
            self.state_path = os.path.join(self.script_dir, state_path)
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
        # Handle case where default is already a boolean
        if isinstance(default, bool):
            default_str = 'true' if default else 'false'
        else:
            default_str = str(default)
        
        result = self.get_setting(key, default_str)
        
        # Handle case where result might be a boolean already
        if isinstance(result, bool):
            return result
        
        return str(result).lower() == 'true'
    
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
    
    def get_ai_timeout(self):
        """Get AI timeout setting from [ai] section, fallback to [settings] for backward compatibility"""
        config = self._load_config()
        # Try [ai] section first
        if config.has_option('ai', 'timeout'):
            value = config.get('ai', 'timeout')
            # Strip inline comments if value is a string
            if isinstance(value, str) and '#' in value:
                value = value.split('#')[0].strip()
            return int(value)
        # Fallback to [settings] section for backward compatibility
        return self.get_int_setting('timeout', 60)
    
    def get_show_costs_setting(self):
        """Get show_costs setting from [ai] section, fallback to [settings] for backward compatibility"""
        config = self._load_config()
        # Try [ai] section first
        if config.has_option('ai', 'show_costs'):
            value = config.get('ai', 'show_costs')
            # Strip inline comments if value is a string
            if isinstance(value, str) and '#' in value:
                value = value.split('#')[0].strip()
            return str(value).lower() == 'true'
        # Fallback to [settings] section for backward compatibility
        return self.get_boolean_setting('show_costs', False)
    
    def get_state_filename(self, state_type='news'):
        """Get appropriate state filename based on type"""
        script_dir = os.path.dirname(self.state_path)
        if state_type == 'forks':
            return os.path.join(script_dir, 'forks_state.json')
        elif state_type == 'news':
            return os.path.join(script_dir, 'news_state.json')
        else:
            raise ValueError(f"Unknown state_type: {state_type}")

    def load_state(self, state_type='news'):
        """Load state from appropriate file"""
        state_file = self.get_state_filename(state_type)
        
        # Check if state file already exists
        if os.path.exists(state_file):
            try:
                with open(state_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                raise ValueError(f"Invalid JSON in {state_file}")
        
        # If state file doesn't exist, check for legacy migration
        self.migrate_legacy_state()
        
        # Try loading again after potential migration
        try:
            with open(state_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON in {state_file}")
    
    def save_state(self, state_data, state_type='news'):
        """Save updated state to appropriate file"""
        state_file = self.get_state_filename(state_type)
        with open(state_file, 'w') as f:
            json.dump(state_data, f, indent=2)
    
    def migrate_legacy_state(self):
        """Safely migrate old state.json to separate news_state.json and forks_state.json"""
        legacy_file = self.state_path  # This is the original state.json path
        if not os.path.exists(legacy_file):
            return  # No migration needed
            
        try:
            # Step 1: Validate legacy state is readable and parse it
            legacy_state = self._validate_legacy_state(legacy_file)
            if not legacy_state:
                return
            
            # Step 2: Split into news and forks data
            news_state, forks_state = self._split_legacy_state(legacy_state)
            
            # Step 3: Perform atomic migration with validation
            self._create_atomic_migration(legacy_state, news_state, forks_state, legacy_file)
            
        except Exception as e:
            print(f"⚠️  Warning: Could not migrate legacy state: {e}")
            # Don't fail - just continue with empty state
    
    def _validate_legacy_state(self, legacy_file):
        """Validate legacy state file is readable and non-empty"""
        try:
            with open(legacy_file, 'r') as f:
                legacy_state = json.load(f)
            
            # If legacy state is empty, just remove it safely
            if not legacy_state:
                backup_file = f"{legacy_file}.empty_backup"
                os.rename(legacy_file, backup_file)
                print(f"✅ Removed empty legacy state file. Backup: {backup_file}")
                return None
                
            return legacy_state
        except (json.JSONDecodeError, IOError) as e:
            print(f"⚠️  Warning: Legacy state file corrupted or unreadable: {e}")
            # Create backup of corrupted file
            backup_file = f"{legacy_file}.corrupted_backup"
            os.rename(legacy_file, backup_file)
            print(f"✅ Backed up corrupted legacy state: {backup_file}")
            return None
    
    def _split_legacy_state(self, legacy_state):
        """Split legacy state into news and forks data"""
        news_state = {}
        forks_state = {}
        
        for repo_key, repo_data in legacy_state.items():
            # Extract news data
            news_data = {}
            for key in ['last_check', 'last_commit', 'last_release', 'branches', 'last_branch_check']:
                if key in repo_data:
                    news_data[key] = repo_data[key]
            if news_data:
                news_state[repo_key] = news_data
                
            # Extract forks data  
            forks_data = {}
            for key in ['last_check', 'processed_forks', 'last_fork_check']:
                if key in repo_data:
                    forks_data[key] = repo_data[key]
            if forks_data:
                forks_state[repo_key] = forks_data
        
        return news_state, forks_state
    
    def _create_atomic_migration(self, legacy_state, news_state, forks_state, legacy_file):
        """Perform atomic state file creation with validation"""
        temp_files = []
        
        try:
            # Step 1: Create temporary files
            news_temp = None
            forks_temp = None
            
            if news_state:
                news_temp = "news_state.json.tmp"
                with open(news_temp, 'w') as f:
                    json.dump(news_state, f, indent=2)
                temp_files.append(news_temp)
                
            if forks_state:
                forks_temp = "forks_state.json.tmp"
                with open(forks_temp, 'w') as f:
                    json.dump(forks_state, f, indent=2)
                temp_files.append(forks_temp)
            
            # Step 2: Validate temporary files are correct
            self._validate_migration_files(news_temp, forks_temp, news_state, forks_state)
            
            # Step 3: Atomically move temp files to final locations
            if news_temp:
                os.rename(news_temp, "news_state.json")
                temp_files.remove(news_temp)
                
            if forks_temp:
                os.rename(forks_temp, "forks_state.json")
                temp_files.remove(forks_temp)
            
            # Step 4: Only after successful migration, backup and remove original
            backup_file = f"{legacy_file}.migrated"
            os.rename(legacy_file, backup_file)
            print(f"✅ Migrated legacy state to separate files. Backup: {backup_file}")
            
        except Exception as e:
            # Rollback: clean up any temporary files
            self._rollback_migration(temp_files)
            raise e
    
    def _validate_migration_files(self, news_temp, forks_temp, expected_news, expected_forks):
        """Validate migration files are written correctly"""
        if news_temp:
            with open(news_temp, 'r') as f:
                actual_news = json.load(f)
            if actual_news != expected_news:
                raise ValueError("News state migration validation failed")
                
        if forks_temp:
            with open(forks_temp, 'r') as f:
                actual_forks = json.load(f)
            if actual_forks != expected_forks:
                raise ValueError("Forks state migration validation failed")
    
    def _rollback_migration(self, temp_files):
        """Rollback failed migration by cleaning up temp files"""
        for temp_file in temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except Exception:
                pass  # Best effort cleanup
    
    def add_repository(self, name, url):
        """Add a repository to config.txt with comment preservation"""
        try:
            # Use comment-preserving parser to maintain formatting
            parser = CommentPreservingINIParser(self.config_path)
            parser.parse_file()
            parser.add_repository(name, url)
            parser.save_file()
            
            # Clear cached config to force reload
            self._config = None
            
        except Exception as e:
            raise ValueError(f"Failed to add repository '{name}': {e}")
    
    def remove_repository(self, identifier):
        """Remove a repository by name or URL with comment preservation"""
        try:
            # Use comment-preserving parser to maintain formatting
            parser = CommentPreservingINIParser(self.config_path)
            parser.parse_file()
            
            if parser.remove_repository(identifier):
                parser.save_file()
                # Clear cached config to force reload
                self._config = None
                return True
            else:
                return False
                
        except Exception as e:
            raise ValueError(f"Failed to remove repository '{identifier}': {e}")
    
    def list_repositories(self):
        """List all configured repositories"""
        return self.load_repositories()
    
    def find_repository_by_alias(self, alias):
        """Find repository by alias name (case-insensitive)"""
        repos = self.load_repositories()
        for repo in repos:
            if repo['name'].lower() == alias.lower():
                return repo
        return None
    
    def clear_state(self, repo_name=None):
        """Clear state for a specific repository or all repositories"""
        if repo_name is None:
            # Clear all state files
            cleared = False
            for state_file in ['state.json', 'news_state.json', 'forks_state.json']:
                state_path = os.path.join(self.script_dir, state_file)
                try:
                    os.remove(state_path)
                    cleared = True
                except FileNotFoundError:
                    pass  # Already cleared
                except Exception:
                    pass
            return cleared
        else:
            # Clear state for specific repository from all state files
            cleared = False
            for state_file in ['state.json', 'news_state.json', 'forks_state.json']:
                state_path = os.path.join(self.script_dir, state_file)
                try:
                    with open(state_path, 'r') as f:
                        state = json.load(f)
                    
                    # Find the repository key (could be just name or owner/repo format)
                    repo_key_to_remove = None
                    for key in state.keys():
                        # Check if the key matches the repo name directly or contains it
                        if key == repo_name or key.split('/')[-1] == repo_name:
                            repo_key_to_remove = key
                            break
                    
                    if repo_key_to_remove:
                        del state[repo_key_to_remove]
                        with open(state_path, 'w') as f:
                            json.dump(state, f, indent=2)
                        cleared = True
                except FileNotFoundError:
                    pass  # No state file exists
                except Exception:
                    pass
            return cleared
    
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
    