#!/usr/bin/env python3
"""
AI Mocking Module for Test Framework
Mocks OpenAI API and Claude CLI calls while allowing GitHub CLI to pass through
"""

import subprocess
import json
from unittest.mock import Mock, patch, MagicMock
from contextlib import contextmanager
from typing import Dict, Any, Optional


class AIMockingManager:
    """Manages AI provider mocking for testing"""
    
    def __init__(self, debug: bool = False):
        self.debug = debug
        self.mock_responses = {
            'forks_analysis': self._create_forks_response(),
            'news_main': self._create_news_main_response(),
            'news_branch': self._create_news_branch_response(),
            'news_multi': self._create_news_multi_response(),
            'default': self._create_default_response()
        }
        self.call_count = 0
        # Store original subprocess.run to avoid recursion
        self.original_subprocess_run = subprocess.run
    
    def _create_forks_response(self) -> str:
        """Mock response for forks analysis"""
        return """✅ Fork Analysis Complete

🍴 **Active Forks Detected**
- Found 3 forks with recent activity
- 2 forks ahead of parent repository
- Most active fork: 12 commits ahead

**Key Fork Insights:**
- Enhanced authentication system implementation
- Performance optimizations in core modules
- Additional testing framework additions
- New feature implementations"""
    
    def _create_news_main_response(self) -> str:
        """Mock response for main branch news"""
        return """✅ Main Branch Updates Detected

📰 **Repository Activity Summary**
- 3 new commits on main branch
- Latest activity: 2 hours ago
- Primary contributor: test automation

**Recent Changes:**
- Implemented test framework validation
- Enhanced error handling mechanisms
- Updated documentation structure
- Performance improvements"""
    
    def _create_news_branch_response(self) -> str:
        """Mock response for branch news"""
        return """✅ Branch Updates Detected

🌿 **Feature Branch Activity**
- 2 new commits on test-feature branch
- Branch ahead of main by 2 commits
- Active development in progress

**Branch Changes:**
- Feature implementation in progress
- Unit tests added for new functionality
- Code review feedback incorporated"""
    
    def _create_news_multi_response(self) -> str:
        """Mock response for multi-branch news"""
        return """✅ Multi-Branch Updates Detected

📰 **Main Branch (3 commits)**
- Core functionality improvements
- Documentation updates
- Bug fixes

🌿 **test-feature Branch (2 commits)**
- New feature development
- Testing framework enhancements

**Overall Impact:**
- Significant progress across multiple development streams
- Coordinated development effort visible"""
    
    def _create_default_response(self) -> str:
        """Default mock response"""
        return """✅ AI Analysis Complete

**Summary Generated**
- Repository analysis completed successfully
- Changes detected and summarized
- Test framework validation passed"""
    
    def _get_mock_response(self, prompt: str, scenario_hint: Optional[str] = None) -> str:
        """Get appropriate mock response based on prompt content or scenario"""
        self.call_count += 1
        
        if scenario_hint and scenario_hint in self.mock_responses:
            response = self.mock_responses[scenario_hint]
        elif 'fork' in prompt.lower():
            response = self.mock_responses['forks_analysis']
        elif 'main' in prompt.lower() and 'branch' in prompt.lower():
            response = self.mock_responses['news_main']
        elif 'feature' in prompt.lower() or 'branch' in prompt.lower():
            response = self.mock_responses['news_branch']
        else:
            response = self.mock_responses['default']
        
        if self.debug:
            print(f"🤖 AI Mock #{self.call_count}: Generated {len(response)} chars")
        
        return response
    
    def _mock_openai_response(self, prompt: str, scenario_hint: Optional[str] = None):
        """Create mock OpenAI API response"""
        content = self._get_mock_response(prompt, scenario_hint)
        
        # Mock the OpenAI response structure
        mock_choice = Mock()
        mock_choice.message.content = content
        
        mock_response = Mock()
        mock_response.choices = [mock_choice]
        mock_response.usage.prompt_tokens = len(prompt) // 4  # Rough estimation
        mock_response.usage.completion_tokens = len(content) // 4
        mock_response.usage.total_tokens = mock_response.usage.prompt_tokens + mock_response.usage.completion_tokens
        
        return mock_response
    
    def _mock_claude_subprocess(self, cmd, **kwargs):
        """Mock subprocess calls for Claude CLI while letting GitHub CLI through"""
        # Ensure proper timeout handling for GitHub CLI calls
        if cmd and len(cmd) > 0 and ('gh' in cmd[0] or 'git' in cmd[0]):
            # Add default timeout if not specified to prevent hanging
            if 'timeout' not in kwargs:
                kwargs['timeout'] = 30
            return self.original_subprocess_run(cmd, **kwargs)
        
        # Mock Claude CLI calls
        if cmd and len(cmd) > 0 and 'claude' in cmd[0]:
            prompt = kwargs.get('input', '')
            scenario_hint = getattr(self, '_current_scenario', None)
            content = self._get_mock_response(prompt, scenario_hint)
            
            # Create mock subprocess result
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = json.dumps({"type": "result", "result": content})
            mock_result.stderr = ""
            
            if self.debug:
                print(f"🤖 Claude CLI Mock: {cmd[0]} -> {len(content)} chars")
            
            return mock_result
        
        # For other commands, use original function to avoid recursion
        # Add default timeout if not specified
        if 'timeout' not in kwargs:
            kwargs['timeout'] = 30
        return self.original_subprocess_run(cmd, **kwargs)
    
    @contextmanager
    def mock_ai_providers(self, scenario_hint: Optional[str] = None):
        """Context manager for mocking both OpenAI and Claude CLI"""
        self._current_scenario = scenario_hint
        
        try:
            # Mock the openai module itself since ai_provider.py does dynamic import
            with patch.dict('sys.modules', {'openai': Mock()}) as mock_modules:
                with patch('subprocess.run', side_effect=self._mock_claude_subprocess):
                    # Get the mocked openai module
                    mock_openai_module = mock_modules['openai']
                    
                    # Setup OpenAI mock client
                    mock_client = Mock()
                    mock_openai_module.OpenAI.return_value = mock_client
                    
                    def mock_create(*args, **kwargs):
                        messages = kwargs.get('messages', [])
                        prompt = ""
                        for message in messages:
                            if message.get('role') == 'user':
                                prompt = message.get('content', '')
                                break
                        return self._mock_openai_response(prompt, scenario_hint)
                    
                    mock_client.chat.completions.create = mock_create
                    
                    if self.debug:
                        print(f"🤖 AI Mocking active (scenario: {scenario_hint})")
                    
                    yield self
                    
        except Exception as e:
            if self.debug:
                print(f"❌ AI Mocking error: {e}")
            raise
        finally:
            self._current_scenario = None
            if self.debug:
                print(f"🤖 AI Mocking complete ({self.call_count} calls)")
    
    def reset_call_count(self):
        """Reset the AI call counter"""
        self.call_count = 0
    
    def get_call_count(self) -> int:
        """Get number of AI calls made"""
        return self.call_count


# Test the module functionality
if __name__ == "__main__":
    print("🧪 Testing AI Mocking Module")
    
    mocker = AIMockingManager(debug=True)
    
    # Test OpenAI mocking
    with mocker.mock_ai_providers('news_main'):
        try:
            # This would normally fail without openai library installed
            # But our mock should handle it
            import sys
            sys.path.append('..')
            from modules.ai_provider import OpenAIProvider
            from modules.config_manager import ConfigManager
            
            # Create a minimal config for testing
            config = ConfigManager()
            config._config = {
                'openai': {'api_key': 'test-key', 'model': 'gpt-4o-mini'},
                'settings': {'timeout': '30'}
            }
            
            provider = OpenAIProvider(config)
            result = provider.generate_summary("Test prompt for main branch news")
            
            print(f"✅ OpenAI Mock Result: {result['summary'][:100]}...")
            
        except Exception as e:
            print(f"⚠️  OpenAI test skipped: {e}")
    
    print(f"✅ AI Mock test complete - {mocker.get_call_count()} calls made")