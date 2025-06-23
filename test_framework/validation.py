#!/usr/bin/env python3
"""
Validation Module for Test Framework
Validates command outputs, state files, and performance metrics
"""

import json
import os
import re
import time
import subprocess
import sys
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
            print(f"❌ AI response validation error: {e}")
            return False
    
    def validate_content_density(self, output: str, command_type: str) -> bool:
        """Validate output has sufficient content density (not just empty sections)"""
        try:
            if not output:
                if self.debug:
                    print(f"❌ Empty output for {command_type}")
                return False
            
            lines = output.split('\n')
            
            # Count meaningful content lines
            bullet_points = [line for line in lines if line.strip().startswith('- ')]
            branch_lines = [line for line in lines if '├─' in line or '⭐' in line]
            cost_tracking = [line for line in lines if '$<0.001' in line and 'tokens' in line]
            
            content_score = 0
            issues = []
            
            if 'forks' in command_type.lower():
                # Fork analysis should have:
                # - Fork entries (🍴)
                # - Branch trees (├─)  
                # - Cost tracking
                # - AI summaries (bullet points)
                
                fork_entries = len([line for line in lines if '🍴' in line])
                if fork_entries == 0:
                    issues.append("No fork entries found")
                else:
                    content_score += 1
                
                if len(branch_lines) == 0:
                    issues.append("No branch tree structure found")
                else:
                    content_score += 1
                    
                if len(bullet_points) < 2:
                    issues.append(f"Insufficient AI content: {len(bullet_points)} bullet points")
                else:
                    content_score += 1
                    
                min_required_score = 2  # At least 2 out of 3 elements
                
            elif 'news' in command_type.lower():
                # News should have:
                # - Summary headers (📊)
                # - AI bullet points
                # - Cost tracking
                
                summary_headers = len([line for line in lines if '📊' in line and 'Summary' in line])
                if summary_headers == 0:
                    issues.append("No summary headers found")
                else:
                    content_score += 1
                
                if len(bullet_points) < 2:
                    issues.append(f"Insufficient AI content: {len(bullet_points)} bullet points")
                else:
                    content_score += 1
                    
                min_required_score = 2  # Both elements required
            
            else:
                # Generic validation
                if len(bullet_points) == 0:
                    issues.append("No bullet point content found")
                else:
                    content_score += 1
                min_required_score = 1
            
            # Check for cost tracking (should be present in all AI-generated content)
            if len(cost_tracking) == 0:
                issues.append("No cost tracking found")
            else:
                content_score += 1
                if 'forks' not in command_type.lower():  # Only increase min requirement for non-forks
                    min_required_score += 1
            
            success = content_score >= min_required_score
            
            if self.debug:
                status = "✅" if success else "❌"
                print(f"{status} Content density validation ({command_type}): {content_score}/{min_required_score + (1 if len(cost_tracking) > 0 else 0)} elements")
                if issues:
                    print(f"   Issues: {', '.join(issues)}")
                    
            self.validation_results.append({
                'type': 'content_density_validation',
                'command_type': command_type,
                'success': success,
                'content_score': content_score,
                'min_required_score': min_required_score,
                'bullet_points': len(bullet_points),
                'branch_lines': len(branch_lines),
                'cost_tracking': len(cost_tracking),
                'issues': issues,
                'timestamp': datetime.now().isoformat()
            })
            
            return success
            
        except Exception as e:
            print(f"❌ Content density validation error: {e}")
            return False
    
    def validate_section_completeness(self, output: str, command_type: str) -> bool:
        """Validate that output sections are complete (not just headers with empty content)"""
        try:
            if not output:
                if self.debug:
                    print(f"❌ Empty output for section validation")
                return False
            
            # Split by section dividers
            sections = output.split('================================================================================')
            
            empty_sections = []
            incomplete_sections = []
            total_meaningful_sections = 0
            
            for i, section in enumerate(sections):
                section = section.strip()
                if not section:
                    continue
                    
                # Check for analysis sections
                if 'FORK ANALYSIS' in section or 'Summary' in section:
                    total_meaningful_sections += 1
                    
                    # For fork analysis, check if it has actual content beyond just headers
                    if 'FORK ANALYSIS' in section:
                        if '🍴' not in section:
                            empty_sections.append(f"Fork analysis section {i} has no fork entries")
                        elif len([line for line in section.split('\n') if line.strip().startswith('- ')]) == 0:
                            incomplete_sections.append(f"Fork analysis section {i} has no AI summary content")
                    
                    # For summary sections, check if they have content between headers
                    elif 'Summary' in section and '📊' in section:
                        lines = section.split('\n')
                        content_lines = [line for line in lines if line.strip() and not line.startswith('─') and 'Summary' not in line and '📊' not in line and not line.startswith('=')]
                        
                        # Only check summary sections that should have content (not just headers)
                        if '$<0.001' not in section and len(content_lines) == 0:
                            empty_sections.append(f"Summary section {i} is completely empty")
                        elif len(content_lines) == 1 and len(content_lines[0].strip()) < 20:
                            incomplete_sections.append(f"Summary section {i} has insufficient content ({len(content_lines)} lines)")
            
            # Special check for forks: ensure we have some content if we claim to have forks
            if 'forks' in command_type.lower():
                fork_summary_pattern = r'Forks Summary.*\((\d+)/\d+\)'
                match = re.search(fork_summary_pattern, output)
                if match:
                    fork_count = int(match.group(1))
                    if fork_count > 0 and len(empty_sections) > 0:
                        # We claim to have forks but sections are empty - this is a major failure
                        empty_sections.append(f"Claims {fork_count} forks but analysis sections are empty")
            
            success = len(empty_sections) == 0 and len(incomplete_sections) <= 1  # Allow 1 incomplete section
            
            if self.debug:
                status = "✅" if success else "❌"
                print(f"{status} Section completeness validation ({command_type}): {total_meaningful_sections} sections")
                if empty_sections:
                    print(f"   🚨 CRITICAL - Empty sections: {', '.join(empty_sections)}")
                if incomplete_sections:
                    print(f"   ⚠️  Incomplete sections: {', '.join(incomplete_sections)}")
            
            self.validation_results.append({
                'type': 'section_completeness_validation',
                'command_type': command_type,
                'success': success,
                'total_sections': total_meaningful_sections,
                'empty_sections': empty_sections,
                'incomplete_sections': incomplete_sections,
                'timestamp': datetime.now().isoformat()
            })
            
            return success
            
        except Exception as e:
            print(f"❌ Section completeness validation error: {e}")
            return False
    
    def validate_new_branch_detected(self, output: str, branch_name: str) -> bool:
        """Validate specific new branch appears in output"""
        try:
            if not output or not branch_name:
                if self.debug:
                    print(f"❌ Empty output or branch name for new branch validation")
                return False
            
            patterns = [
                f"🌿 {branch_name}",  # Branch summary header
                f"├─ {branch_name}:",  # Branch tree entry
                f"└─ {branch_name}:",  # Branch tree entry (last)
                f"⭐ {branch_name}",   # Branch star indicator
                f"{branch_name} \\(\\+\\d+\\)",  # Branch with commit count
            ]
            
            found_patterns = []
            for pattern in patterns:
                if re.search(pattern, output, re.IGNORECASE):
                    found_patterns.append(pattern)
            
            # At least one pattern should match for new branch detection
            success = len(found_patterns) > 0
            
            if self.debug:
                status = "✅" if success else "❌"
                print(f"{status} NEW branch detection: {branch_name} - {len(found_patterns)} pattern(s) found")
                if found_patterns:
                    print(f"   Found: {found_patterns}")
                else:
                    print(f"   Expected patterns: {patterns}")
            
            self.validation_results.append({
                'type': 'new_branch_validation',
                'success': success,
                'branch_name': branch_name,
                'found_patterns': found_patterns,
                'expected_patterns': patterns,
                'timestamp': datetime.now().isoformat()
            })
            
            return success
            
        except Exception as e:
            print(f"❌ NEW branch validation error: {e}")
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
    
    def validate_repository_access(self, repo_name: str, expected_url: str) -> bool:
        """
        CRITICAL VALIDATION: Ensure repository is configured and accessible.
        This is a MAJOR ERROR check that should cause system exit if failed.
        """
        try:
            if self.debug:
                print(f"🔍 CRITICAL CHECK: Validating repository access for '{repo_name}'...")
            
            # Step 1: Check config.txt has the repository
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_path = os.path.join(project_root, "config.txt")
            
            if not os.path.exists(config_path):
                if self.debug:
                    print(f"🚨 MAJOR ERROR: config.txt not found at {config_path}")
                    print("🛑 SYSTEM MUST EXIT - Repository configuration missing")
                return False
            
            # Read config and check repository is listed
            repo_found_in_config = False
            with open(config_path, 'r') as f:
                config_content = f.read()
                
            # Look for the repository in [repositories] section
            lines = config_content.split('\n')
            in_repositories_section = False
            
            for line in lines:
                line = line.strip()
                if line == '[repositories]':
                    in_repositories_section = True
                    continue
                elif line.startswith('[') and line.endswith(']'):
                    in_repositories_section = False
                    continue
                    
                if in_repositories_section and '=' in line:
                    config_name = line.split('=')[0].strip()
                    config_url = line.split('=')[1].split('#')[0].strip()  # Remove comments
                    
                    if config_name == repo_name:
                        repo_found_in_config = True
                        if config_url.lower() != expected_url.lower():
                            if self.debug:
                                print(f"🚨 MAJOR ERROR: Repository URL mismatch!")
                                print(f"   Expected: {expected_url}")
                                print(f"   Found: {config_url}")
                                print("🛑 SYSTEM MUST EXIT - Repository configuration inconsistent")
                            return False
                        break
            
            if not repo_found_in_config:
                if self.debug:
                    print(f"🚨 MAJOR ERROR: Repository '{repo_name}' not found in config.txt [repositories] section")
                    print("🛑 SYSTEM MUST EXIT - Repository not configured")
                return False
            
            # Step 2: Test GitHub API access
            try:
                # Extract owner/repo from URL
                url_parts = expected_url.replace('https://github.com/', '').split('/')
                if len(url_parts) < 2:
                    if self.debug:
                        print(f"🚨 MAJOR ERROR: Invalid GitHub URL format: {expected_url}")
                        print("🛑 SYSTEM MUST EXIT - Repository URL invalid")
                    return False
                
                owner, repo = url_parts[0], url_parts[1]
                
                # Test GitHub API access
                gh_cmd = ['gh', 'api', f'repos/{owner}/{repo}', '--jq', '.full_name']
                result = subprocess.run(gh_cmd, capture_output=True, text=True, timeout=30)
                
                if result.returncode != 0:
                    if self.debug:
                        print(f"🚨 MAJOR ERROR: GitHub API access failed for {owner}/{repo}")
                        print(f"   Command: {' '.join(gh_cmd)}")
                        print(f"   Error: {result.stderr}")
                        print("🛑 SYSTEM MUST EXIT - Repository not accessible via GitHub API")
                    return False
                
                full_name = result.stdout.strip()
                expected_full_name = f"{owner}/{repo}"
                
                if full_name.lower() != expected_full_name.lower():
                    if self.debug:
                        print(f"🚨 MAJOR ERROR: Repository name mismatch!")
                        print(f"   Expected: {expected_full_name}")
                        print(f"   API returned: {full_name}")
                        print("🛑 SYSTEM MUST EXIT - Repository identity inconsistent")
                    return False
                
            except subprocess.TimeoutExpired:
                if self.debug:
                    print(f"🚨 MAJOR ERROR: GitHub API timeout accessing {expected_url}")
                    print("🛑 SYSTEM MUST EXIT - Repository API access timed out")
                return False
            except Exception as e:
                if self.debug:
                    print(f"🚨 MAJOR ERROR: GitHub API access exception: {e}")
                    print("🛑 SYSTEM MUST EXIT - Repository API access failed")
                return False
            
            # Step 3: Test gh auth status
            try:
                auth_cmd = ['gh', 'auth', 'status']
                auth_result = subprocess.run(auth_cmd, capture_output=True, text=True, timeout=10)
                
                if auth_result.returncode != 0:
                    if self.debug:
                        print(f"🚨 MAJOR ERROR: GitHub CLI not authenticated")
                        print(f"   Command: {' '.join(auth_cmd)}")
                        print(f"   Error: {auth_result.stderr}")
                        print("🛑 SYSTEM MUST EXIT - GitHub CLI authentication required")
                    return False
                    
            except Exception as e:
                if self.debug:
                    print(f"🚨 MAJOR ERROR: GitHub auth check failed: {e}")
                    print("🛑 SYSTEM MUST EXIT - GitHub CLI authentication check failed")
                return False
            
            # All checks passed
            if self.debug:
                print(f"✅ CRITICAL CHECK PASSED: Repository '{repo_name}' is properly configured and accessible")
                print(f"   Config: Found in config.txt")
                print(f"   API: Accessible via GitHub API")
                print(f"   Auth: GitHub CLI authenticated")
            
            self.validation_results.append({
                'type': 'repository_access_validation',
                'repo_name': repo_name,
                'expected_url': expected_url,
                'success': True,
                'timestamp': datetime.now().isoformat()
            })
            
            return True
            
        except Exception as e:
            if self.debug:
                print(f"🚨 MAJOR ERROR: Repository access validation exception: {e}")
                print("🛑 SYSTEM MUST EXIT - Critical validation failed")
            
            self.validation_results.append({
                'type': 'repository_access_validation',
                'repo_name': repo_name,
                'expected_url': expected_url,
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
            
            return False

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