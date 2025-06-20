import json
import os
from datetime import datetime


class ConfigManager:
    def __init__(self, config_path='config.json', state_path='state.json'):
        self.config_path = config_path
        self.state_path = state_path
    
    def load_repositories(self):
        """Load repository list from config.json"""
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
                return config.get('repositories', [])
        except FileNotFoundError:
            return []
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON in {self.config_path}")
    
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