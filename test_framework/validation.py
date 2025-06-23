#!/usr/bin/env python3
"""
Validation Module for Test Framework
Validates command outputs, state files, and performance metrics
"""

import json
import os
import re
import time
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta


class TestValidator:
    """Handles validation of test results and outputs"""
    
    def __init__(self, debug: bool = False):
        self.debug = debug
        self.validation_results = []
    
    def validate_command_success(self, result: Any, command_name: str = "command") -> bool:
        """Validate command executed successfully (exit code 0)"""
        try:
            if hasattr(result, 'returncode'):
                success = result.returncode == 0
            elif isinstance(result, tuple) and len(result) >= 1:
                success = result[0]  # (success, stdout, stderr) format
            else:
                success = bool(result)
            
            if self.debug:
                status = "✅" if success else "❌"
                print(f"{status} Command success validation: {command_name}")
            
            self.validation_results.append({
                'type': 'command_success',
                'command': command_name,
                'success': success,
                'timestamp': datetime.now().isoformat()
            })
            
            return success
            
        except Exception as e:
            if self.debug:
                print(f"❌ Command validation error: {e}")
            return False
    
    def validate_output_contains(self, output: str, expected_patterns: List[str], 
                               validation_name: str = "output") -> bool:
        """Validate output contains expected content patterns"""
        try:
            if not output:
                if self.debug:
                    print(f"❌ Empty output for {validation_name}")
                return False
            
            found_patterns = []
            missing_patterns = []
            
            for pattern in expected_patterns:
                if re.search(pattern, output, re.IGNORECASE):
                    found_patterns.append(pattern)
                else:
                    missing_patterns.append(pattern)
            
            success = len(missing_patterns) == 0
            
            if self.debug:
                status = "✅" if success else "❌"
                print(f"{status} Output validation ({validation_name}): {len(found_patterns)}/{len(expected_patterns)} patterns found")
                if missing_patterns and self.debug:
                    print(f"   Missing patterns: {missing_patterns}")
            
            self.validation_results.append({
                'type': 'output_validation',
                'name': validation_name,
                'success': success,
                'found_patterns': found_patterns,
                'missing_patterns': missing_patterns,
                'output_length': len(output),
                'timestamp': datetime.now().isoformat()
            })
            
            return success
            
        except Exception as e:
            if self.debug:
                print(f"❌ Output validation error: {e}")
            return False
    
    def validate_state_updated(self, repo_key: str, expected_changes: Dict[str, Any],
                             state_file: str = "news_state.json") -> bool:
        """Validate state file was updated correctly"""
        try:
            state_path = state_file
            if not os.path.isabs(state_path):
                # Assume relative to project root
                project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                state_path = os.path.join(project_root, state_file)
            
            if not os.path.exists(state_path):
                if self.debug:
                    print(f"❌ State file not found: {state_path}")
                return False
            
            with open(state_path, 'r') as f:
                state_data = json.load(f)
            
            if repo_key not in state_data:
                if self.debug:
                    print(f"❌ Repository key '{repo_key}' not found in state")
                return False
            
            repo_state = state_data[repo_key]
            validation_results = []
            
            for key, expected_value in expected_changes.items():
                if key in repo_state:
                    if expected_value is None:
                        # Just check if key exists
                        validation_results.append(True)
                    elif isinstance(expected_value, str) and expected_value.startswith('regex:'):
                        # Regex validation
                        pattern = expected_value[6:]  # Remove 'regex:' prefix
                        actual_value = str(repo_state[key])
                        validation_results.append(bool(re.search(pattern, actual_value)))
                    else:
                        # Direct comparison
                        validation_results.append(repo_state[key] == expected_value)
                else:
                    validation_results.append(False)
                    if self.debug:
                        print(f"❌ Expected key '{key}' not found in repo state")
            
            success = all(validation_results)
            
            if self.debug:
                status = "✅" if success else "❌"
                print(f"{status} State validation: {repo_key} - {len([r for r in validation_results if r])}/{len(validation_results)} checks passed")
            
            self.validation_results.append({
                'type': 'state_validation',
                'repo_key': repo_key,
                'success': success,
                'checked_keys': list(expected_changes.keys()),
                'passed_checks': len([r for r in validation_results if r]),
                'total_checks': len(validation_results),
                'timestamp': datetime.now().isoformat()
            })
            
            return success
            
        except Exception as e:
            if self.debug:
                print(f"❌ State validation error: {e}")
            return False
    
    def validate_performance_metrics(self, execution_time: float, max_time: float,
                                   operation_name: str = "operation") -> bool:
        """Validate operation completed within acceptable time"""
        try:
            success = execution_time <= max_time
            
            if self.debug:
                status = "✅" if success else "❌"
                print(f"{status} Performance validation ({operation_name}): {execution_time:.2f}s <= {max_time}s")
            
            self.validation_results.append({
                'type': 'performance_validation',
                'operation': operation_name,
                'success': success,
                'execution_time': execution_time,
                'max_time': max_time,
                'timestamp': datetime.now().isoformat()
            })
            
            return success
            
        except Exception as e:
            if self.debug:
                print(f"❌ Performance validation error: {e}")
            return False
    
    def validate_state_cleared(self, repo_key: str, state_file: str = "news_state.json") -> bool:
        """Validate that repository state was cleared properly"""
        try:
            state_path = state_file
            if not os.path.isabs(state_path):
                project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                state_path = os.path.join(project_root, state_file)
            
            # If state file doesn't exist, consider it cleared
            if not os.path.exists(state_path):
                if self.debug:
                    print(f"✅ State cleared: {state_file} doesn't exist")
                return True
            
            with open(state_path, 'r') as f:
                state_data = json.load(f)
            
            # Check if repo_key is absent or has minimal state
            repo_not_in_state = repo_key not in state_data
            
            success = repo_not_in_state
            
            if self.debug:
                status = "✅" if success else "❌"
                print(f"{status} State clear validation: {repo_key} {'not found' if repo_not_in_state else 'still present'}")
            
            self.validation_results.append({
                'type': 'state_clear_validation',
                'repo_key': repo_key,
                'success': success,
                'repo_in_state': not repo_not_in_state,
                'timestamp': datetime.now().isoformat()
            })
            
            return success
            
        except Exception as e:
            if self.debug:
                print(f"❌ State clear validation error: {e}")
            return False
    
    def validate_ai_response_format(self, response: str, min_length: int = 50) -> bool:
        """Validate AI response has reasonable format and content"""
        try:
            if not response or len(response.strip()) < min_length:
                if self.debug:
                    print(f"❌ AI response too short: {len(response)} chars")
                return False
            
            # Check for common AI response indicators
            indicators = [
                r'📊|🌿|🍴|\+\d+|\$<',  # Emoji indicators and gh-utils specific patterns
                r'Summary|tokens|commit|branch',  # Common gh-utils output words
                r'Added|Enhanced|Improved|Fixed|-',  # AI-generated bullet points
            ]
            
            found_indicators = 0
            for pattern in indicators:
                if re.search(pattern, response, re.IGNORECASE):
                    found_indicators += 1
            
            success = found_indicators >= 2  # At least 2 indicators present
            
            if self.debug:
                status = "✅" if success else "❌"
                print(f"{status} AI response validation: {len(response)} chars, {found_indicators} indicators")
            
            self.validation_results.append({
                'type': 'ai_response_validation',
                'success': success,
                'response_length': len(response),
                'indicators_found': found_indicators,
                'timestamp': datetime.now().isoformat()
            })
            
            return success
            
        except Exception as e:
            if self.debug:
                print(f"❌ AI response validation error: {e}")
            return False
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """Get summary of all validation results"""
        total_validations = len(self.validation_results)
        successful_validations = len([r for r in self.validation_results if r['success']])
        
        by_type = {}
        for result in self.validation_results:
            result_type = result['type']
            if result_type not in by_type:
                by_type[result_type] = {'total': 0, 'successful': 0}
            by_type[result_type]['total'] += 1
            if result['success']:
                by_type[result_type]['successful'] += 1
        
        return {
            'total_validations': total_validations,
            'successful_validations': successful_validations,
            'success_rate': successful_validations / total_validations if total_validations > 0 else 0,
            'by_type': by_type,
            'results': self.validation_results
        }
    
    def reset_results(self):
        """Reset validation results"""
        self.validation_results.clear()


# Test the module functionality
if __name__ == "__main__":
    print("🧪 Testing Validation Module")
    
    validator = TestValidator(debug=True)
    
    # Test command success validation
    validator.validate_command_success(True, "test_command")
    
    # Test output validation
    test_output = "📊 ccusage Summary (+11) (0h ago) ($<0.001, 772 tokens)\n- Added offline flag support to blocks command"
    validator.validate_output_contains(
        test_output, 
        ["📊", "Summary", "tokens", "-"], 
        "test_output"
    )
    
    # Test AI response validation
    test_ai_response = "📊 ccusage Summary (+11) (0h ago) ($<0.001, 772 tokens)\n- Added offline flag support to blocks command\n- Enhanced multi-directory support"
    validator.validate_ai_response_format(test_ai_response)
    
    # Get summary
    summary = validator.get_validation_summary()
    print(f"\n📊 Validation Summary: {summary['successful_validations']}/{summary['total_validations']} passed")
    print("✅ Validation module test complete")