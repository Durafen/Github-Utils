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
            'default': self._create_mock_response()
        }
        self.call_count = 0
        # Store original subprocess.run to avoid recursion
        self.original_subprocess_run = subprocess.run
    
    def _create_mock_response(self) -> str:
        """Single mock response for all scenarios"""
        return "Changes detected and summarized by AI mocking"
    
    def _get_mock_response(self, prompt: str, scenario_hint: Optional[str] = None) -> str:
        """Get the single mock response"""
        self.call_count += 1
        
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
                kwargs['timeout'] = 900
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
            kwargs['timeout'] = 900
        return self.original_subprocess_run(cmd, **kwargs)
    
    @contextmanager
    def mock_ai_providers(self, scenario_hint: Optional[str] = None):
        """Context manager for mocking both OpenAI and Claude CLI using environment variables"""
        import os
        
        # Store original environment values to restore later
        original_test_mode = os.environ.get('GH_UTILS_TEST_MODE')
        original_test_scenario = os.environ.get('GH_UTILS_TEST_SCENARIO')
        
        try:
            # Set environment variables for test mode
            os.environ['GH_UTILS_TEST_MODE'] = '1'
            if scenario_hint:
                os.environ['GH_UTILS_TEST_SCENARIO'] = scenario_hint
            else:
                os.environ['GH_UTILS_TEST_SCENARIO'] = 'default'
            
            if self.debug:
                print(f"🤖 AI Mocking active (scenario: {scenario_hint})")
            
            # Reset call count for this mocking session
            self.call_count = 0
            
            yield self
                    
        except Exception as e:
            if self.debug:
                print(f"❌ AI Mocking error: {e}")
            raise
        finally:
            # Restore original environment variables
            if original_test_mode is not None:
                os.environ['GH_UTILS_TEST_MODE'] = original_test_mode
            else:
                os.environ.pop('GH_UTILS_TEST_MODE', None)
            
            if original_test_scenario is not None:
                os.environ['GH_UTILS_TEST_SCENARIO'] = original_test_scenario
            else:
                os.environ.pop('GH_UTILS_TEST_SCENARIO', None)
            
            if self.debug:
                print(f"🤖 AI Mocking complete")
    
    def reset_call_count(self):
        """Reset the AI call counter"""
        self.call_count = 0
    
    def get_call_count(self) -> int:
        """Get number of AI calls made"""
        return self.call_count
    
    def _get_subprocess_call_count(self) -> int:
        """Get call count from subprocess environment variable"""
        import os
        try:
            return int(os.environ.get('GH_UTILS_AI_CALL_COUNT', '0'))
        except ValueError:
            return 0
    
    
    @staticmethod
    def get_test_mode_response(prompt: str = "") -> dict:
        """Get mock response if in test mode, None otherwise"""
        import os
        
        if os.environ.get('GH_UTILS_TEST_MODE') != '1':
            return None
        
        # Note: Call count tracking removed as it doesn't work reliably across process boundaries
        
        scenario = os.environ.get('GH_UTILS_TEST_SCENARIO', 'default')
        
        # Always use the single mock response
        content = "Changes detected and summarized by AI mocking"
        
        return {
            'summary': content,
            'cost_info': {
                'input_tokens': len(prompt) // 4,
                'output_tokens': len(content) // 4,
                'total_tokens': (len(prompt) + len(content)) // 4,
                'estimated_cost': 0.001,
                'provider': 'AI Mock (test mode)'
            }
        }


# Test the module functionality
if __name__ == "__main__":
    print("🧪 Testing AI Mocking Module")
    
    mocker = AIMockingManager(debug=True)
    
    # Test OpenAI mocking
    with mocker.mock_ai_providers('default'):
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