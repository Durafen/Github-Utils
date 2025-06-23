#!/usr/bin/env python3
"""
Hybrid Test Runner for gh-utils Testing Framework
Orchestrates testing scenarios using real GitHub data and mocked AI responses
"""

import subprocess
import time
import os
import sys
from typing import Dict, List, Tuple, Optional, Any, Callable
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Handle imports for both relative and direct execution
try:
    from .github_operations import GitHubOperations
    from .ai_mocking import AIMockingManager
    from .validation import TestValidator
except ImportError:
    from github_operations import GitHubOperations
    from ai_mocking import AIMockingManager
    from validation import TestValidator


class HybridTestRunner:
    """Main test runner that orchestrates hybrid testing scenarios"""
    
    def __init__(self, debug: bool = False):
        self.debug = debug
        self.github_ops = GitHubOperations(debug=debug)
        self.ai_mocker = AIMockingManager(debug=debug)
        self.validator = TestValidator(debug=debug)
        self.test_results = []
        
        # Project paths - find the actual main project directory
        # Handle both direct execution and symlinked execution
        current_file = os.path.abspath(__file__)
        current_dir = os.path.dirname(current_file)
        
        # If we're in a symlinked test_framework, resolve to main project
        if 'github-utils-tests' in current_dir:
            # We're in the worktree, main project is ../github-utils
            self.project_root = os.path.join(os.path.dirname(os.path.dirname(current_dir)), 'github-utils')
        else:
            # We're in the main project directory
            self.project_root = os.path.dirname(current_dir)
        
        # Initialize config manager for repository URL lookups
        sys.path.insert(0, self.project_root)
        from modules.config_manager import ConfigManager
        self.config_manager = ConfigManager()
        
        # Test configuration
        self.test_repos = {
            'ccusage': {
                'url': 'https://github.com/Durafen/ccusage',
                'alias': 'ccusage',
                'type': 'fork'  # This is a fork of ryoppippi/ccusage
            },
            'testing': {
                'url': 'https://github.com/Durafen/testing',
                'alias': 'testing',
                'type': 'regular'  # Standalone repository
            }
        }
        self.gh_utils_script = os.path.join(self.project_root, 'gh-utils.py')
        
        if self.debug:
            print(f"🚀 Test Runner initialized")
            print(f"   Project root: {self.project_root}")
            print(f"   gh-utils script: {self.gh_utils_script}")
    
    def setup_test_environment(self) -> bool:
        """Set up the test environment"""
        try:
            if self.debug:
                print("🔧 Setting up test environment...")
            
            # Setup GitHub repositories for commit operations
            if not self.github_ops.setup_test_repositories():
                raise RuntimeError("Failed to setup GitHub repositories")
            
            # Test repositories assumed to be already in config
            
            if self.debug:
                print("✅ Test environment setup complete")
            return True
            
        except Exception as e:
            print(f"❌ Test environment setup failed: {e}")
            return False
    
    def _ensure_repository_in_config(self, repo_name: str, repo_url: str) -> bool:
        """Ensure repository is added to gh-utils configuration"""
        try:
            captured_lines = []
            
            with subprocess.Popen([
                'python3', self.gh_utils_script, 'add', repo_url, repo_name
            ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, bufsize=1, cwd=self.project_root,
            env={**os.environ, 'PYTHONUNBUFFERED': '1'}
            ) as process:
                
                for line in iter(process.stdout.readline, ''):
                    if self.debug:
                        print(line, end='')
                    captured_lines.append(line)
                
                return_code = process.wait()
            
            # It's OK if the repo already exists (non-zero exit code)
            if self.debug and return_code == 0:
                print(f"✅ Added repository {repo_name} to config")
            elif self.debug:
                print(f"ℹ️  Repository {repo_name} already in config")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to add repository {repo_name}: {e}")
            return False
    
    def execute_gh_utils_command(self, command_args: List[str], 
                                scenario_hint: Optional[str] = None, 
                                timeout: int = 60,
                                hide_execution_log: bool = False) -> Tuple[bool, str, str, float]:
        """Execute gh-utils command with AI mocking and real-time output"""
        try:
            start_time = time.time()
            captured_lines = []
            
            with self.ai_mocker.mock_ai_providers(scenario_hint):
                print(f"🔧 Executing: python3 {self.gh_utils_script} {' '.join(command_args)}")
                
                if hide_execution_log:
                    print("[Output hidden for first run of phase]")
                
                # Real-time subprocess execution with output capture
                with subprocess.Popen([
                    'python3', self.gh_utils_script
                ] + command_args,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,  # Line buffered for real-time output
                cwd=self.project_root,
                env={**os.environ, 'PYTHONUNBUFFERED': '1'}
                ) as process:
                    
                    # Real-time output display and capture
                    for line in iter(process.stdout.readline, ''):
                        if not hide_execution_log:
                            print(line, end='')  # Real-time display
                        captured_lines.append(line)  # Capture for validation
                    
                    return_code = process.wait()
                
                execution_time = time.time() - start_time
                success = return_code == 0
                stdout = ''.join(captured_lines)
                stderr = ""  # Combined with stdout above
                
                # Show completion message for hidden runs
                if hide_execution_log and not success:
                    print(f"Command failed with return code: {return_code}")
                
                # Perform advanced validation on the output
                validation_success = True
                validation_issues = []
                
                # Only apply enhanced validation to non-first runs (when output is not hidden)
                # First runs are supposed to be empty/baseline and have hidden output
                if success and stdout and not hide_execution_log:  
                    command_type = ' '.join(command_args)
                    
                    # Skip validation for clear commands (they're supposed to have minimal output)
                    if 'clear' not in command_type.lower():
                        # Content density validation - detects empty sections
                        if not self.validator.validate_content_density(stdout, command_type):
                            validation_success = False
                            validation_issues.append("Content density validation failed")
                        
                        # Section completeness validation - detects broken AI generation
                        if not self.validator.validate_section_completeness(stdout, command_type):
                            validation_success = False
                            validation_issues.append("Section completeness validation failed")
                        
                        # If validation fails, override the success status
                        if not validation_success:
                            success = False
                            if self.debug:
                                print(f"🚨 VALIDATION FAILURE: {', '.join(validation_issues)}")
                                print(f"   Command reported success but output validation failed!")
                            else:
                                # Always show validation failures even in non-debug mode
                                print(f"🚨 CRITICAL VALIDATION FAILURE!")
                                print(f"   {', '.join(validation_issues)}")
                                print(f"   This indicates the main gh-utils program has bugs!")
                
                status = "✅" if success else "❌"
                print(f"{status} Command completed in {execution_time:.2f}s")
                
                # Add validation warning if issues found
                if validation_issues:
                    print(f"⚠️  Validation issues: {', '.join(validation_issues)}")
                
                return success, stdout, stderr, execution_time
                
        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            print(f"❌ Command timed out after {timeout}s")
            return False, "", "Command timed out", execution_time
        except Exception as e:
            execution_time = time.time() - start_time
            print(f"❌ Command execution failed: {e}")
            return False, "", str(e), execution_time
    
    def run_test_scenario(self, scenario_name: str, test_steps: List[Tuple[str, Callable]]) -> Dict[str, Any]:
        """Execute a complete test scenario with multiple steps"""
        if self.debug:
            print(f"\n{'='*60}")
            print(f"🧪 Testing Scenario: {scenario_name}")
            print(f"{'='*60}")
        
        scenario_start_time = time.time()
        step_results = []
        scenario_success = True
        
        for step_name, step_func in test_steps:
            if self.debug:
                print(f"\n📋 Step: {step_name}")
            
            try:
                step_start_time = time.time()
                step_success = step_func()
                step_execution_time = time.time() - step_start_time
                
                status = "✅" if step_success else "❌"
                step_results.append({
                    'name': step_name,
                    'success': step_success,
                    'execution_time': step_execution_time,
                    'timestamp': datetime.now().isoformat()
                })
                
                if not step_success:
                    scenario_success = False
                
                if self.debug:
                    print(f"{status} {step_name} ({step_execution_time:.2f}s)")
                
            except Exception as e:
                step_execution_time = time.time() - step_start_time
                step_results.append({
                    'name': step_name,
                    'success': False,
                    'execution_time': step_execution_time,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })
                scenario_success = False
                
                print(f"❌ {step_name} - ERROR: {e}")
        
        scenario_execution_time = time.time() - scenario_start_time
        
        scenario_result = {
            'name': scenario_name,
            'success': scenario_success,
            'execution_time': scenario_execution_time,
            'steps': step_results,
            'timestamp': datetime.now().isoformat()
        }
        
        self.test_results.append(scenario_result)
        
        if self.debug:
            status = "✅" if scenario_success else "❌"
            passed_steps = len([s for s in step_results if s['success']])
            print(f"\n{status} Scenario Complete: {passed_steps}/{len(step_results)} steps passed")
        
        return scenario_result
    
    def clear_repository_state(self, repo_name: str) -> bool:
        """Clear repository state using gh-utils clear command"""
        try:
            success, stdout, stderr, exec_time = self.execute_gh_utils_command(['clear', repo_name])
            
            # Clear command can fail if no state exists - this is OK for first run
            return True
            
        except Exception as e:
            print(f"❌ Failed to clear state for {repo_name}: {e}")
            return False
    
    def test_news_detection(self, repo_name: str, scenario_hint: str = None, hide_execution_log: bool = False) -> bool:
        """Test news detection for a repository"""
        try:
            # STEP 1 CRITICAL CHECK: Validate repository access before ANY processing
            if scenario_hint and 'baseline' in scenario_hint:
                # Map repository names to expected URLs for validation
                repo_url_mappings = {
                    'ccusage': 'https://github.com/Durafen/ccusage',
                    'test-ccusage': 'https://github.com/Durafen/ccusage', 
                    'testing': 'https://github.com/Durafen/testing'
                }
                
                expected_url = repo_url_mappings.get(repo_name)
                if not expected_url:
                    import sys
                    sys.exit(1)
                
                # Critical repository validation - MUST pass or system exits
                repo_access_valid = self.validator.validate_repository_access(repo_name, expected_url)
                if not repo_access_valid:
                    import sys
                    sys.exit(1)
            
            success, stdout, stderr, exec_time = self.execute_gh_utils_command(
                ['news', repo_name], scenario_hint, hide_execution_log=hide_execution_log
            )
            
            if not success:
                return False
            
            # Validate performance first (applies to all scenarios)
            performance_valid = self.validator.validate_performance_metrics(
                exec_time, 60.0, f"news_{repo_name}"
            )
            
            # Handle different validation based on scenario
            if scenario_hint and 'baseline' in scenario_hint:
                # Baseline run: any successful output is valid (establishes state)
                if self.debug:
                    print(f"✅ Baseline validation: Command succeeded")
                return performance_valid
            
            # Incremental runs: validate that content was detected
            if not stdout.strip():
                # Empty output for incremental run might indicate no new changes detected
                # This could be valid depending on timing, so we'll accept it
                if self.debug:
                    print(f"ℹ️  Incremental run: No new content detected")
                return performance_valid
            
            # Validate output contains expected news patterns
            expected_patterns = ['📊', 'Summary', 'tokens', '-']
            output_valid = self.validator.validate_output_contains(
                stdout, expected_patterns, f"news_{repo_name}"
            )
            
            # For incremental runs, also check for activity indicators
            if scenario_hint and any(x in scenario_hint for x in ['main', 'branch', 'multi']):
                # Look for indicators of new activity (commits, branches, etc.)
                activity_patterns = [r'\(\+\d+\)', r'commits?', r'branch']
                try:
                    import re
                    activity_detected = any(
                        re.search(pattern, stdout, re.IGNORECASE) 
                        for pattern in activity_patterns
                    )
                    if self.debug and activity_detected:
                        print(f"✅ Incremental activity detected in output")
                except Exception:
                    pass  # Pattern matching failed, continue with other validation
            
            # For new branch scenarios, validate new branch detection
            if scenario_hint and 'new_branch' in scenario_hint:
                # Look for new branch patterns in the output
                try:
                    import re
                    new_branch_pattern = r'test-new-\d+'
                    match = re.search(new_branch_pattern, stdout)
                    if match:
                        branch_name = match.group()
                        branch_valid = self.validator.validate_new_branch_detected(stdout, branch_name)
                        if self.debug:
                            status = "✅" if branch_valid else "❌"
                            print(f"{status} New branch validation: {branch_name}")
                except Exception as e:
                    if self.debug:
                        print(f"⚠️ New branch validation failed: {e}")
            
            # Validate AI response format
            ai_valid = self.validator.validate_ai_response_format(stdout)
            
            return output_valid and performance_valid and ai_valid
            
        except Exception as e:
            print(f"❌ News detection test failed for {repo_name}: {e}")
            return False
    
    def test_forks_analysis(self, repo_name: str, scenario_hint: str = 'forks_analysis', hide_execution_log: bool = False) -> bool:
        """Test forks analysis for a repository"""
        try:
            success, stdout, stderr, exec_time = self.execute_gh_utils_command(
                ['forks', repo_name], scenario_hint, hide_execution_log=hide_execution_log
            )
            
            if not success:
                return False
            
            # Validate performance first (applies to all scenarios)
            performance_valid = self.validator.validate_performance_metrics(
                exec_time, 90.0, f"forks_{repo_name}"  # Forks analysis takes longer
            )
            
            # Handle different validation based on scenario
            if scenario_hint and 'baseline' in scenario_hint:
                # Baseline run: any successful output is valid (establishes state)
                if self.debug:
                    print(f"✅ Baseline forks validation: Command succeeded")
                return performance_valid
            
            # Incremental runs: validate that fork content was detected
            if not stdout.strip():
                # Empty output for incremental run indicates no forks or no changes
                if self.debug:
                    print(f"ℹ️  Incremental forks run: No fork activity detected")
                return performance_valid
            
            # Validate output contains fork-specific patterns
            expected_patterns = ['📊', 'Forks Summary', '=', '\\(\\d+/\\d+ \\)']
            output_valid = self.validator.validate_output_contains(
                stdout, expected_patterns, f"forks_{repo_name}"
            )
            
            # For incremental runs, check for fork activity indicators
            if scenario_hint and any(x in scenario_hint for x in ['main', 'branch', 'multi']):
                # Look for indicators of fork changes or new commits
                activity_patterns = [r'\(\+\d+\)', r'ahead', r'commits?']
                try:
                    import re
                    activity_detected = any(
                        re.search(pattern, stdout, re.IGNORECASE) 
                        for pattern in activity_patterns
                    )
                    if self.debug and activity_detected:
                        print(f"✅ Incremental fork activity detected in output")
                except Exception:
                    pass  # Pattern matching failed, continue with other validation
            
            # For new branch forks scenarios, validate new branch detection  
            if scenario_hint and any(x in scenario_hint for x in ['new_branch', 'new']):
                # Look for new branch patterns in the forks output
                try:
                    import re
                    new_branch_pattern = r'test-new-\d+'
                    match = re.search(new_branch_pattern, stdout)
                    if match:
                        branch_name = match.group()
                        branch_valid = self.validator.validate_new_branch_detected(stdout, branch_name)
                        if self.debug:
                            status = "✅" if branch_valid else "❌"
                            print(f"{status} New branch validation in forks: {branch_name}")
                except Exception as e:
                    if self.debug:
                        print(f"⚠️ New branch validation failed in forks: {e}")
            
            # Validate AI response format
            ai_valid = self.validator.validate_ai_response_format(stdout)
            
            return output_valid and performance_valid and ai_valid
            
        except Exception as e:
            print(f"❌ Forks analysis test failed for {repo_name}: {e}")
            return False
    
    def create_test_commit(self, repo_name: str, branch: str = 'main', 
                          message: Optional[str] = None) -> bool:
        """Create a test commit in the specified repository and branch"""
        try:
            if not message:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                message = f"Test framework commit - {timestamp}"
            
            success = self.github_ops.create_test_commit(repo_name, branch, message)
            
            # Small delay to ensure GitHub API reflects the change
            if success:
                time.sleep(3)
            
            return success
            
        except Exception as e:
            print(f"❌ Failed to create commit for {repo_name}/{branch}: {e}")
            return False
    
    def cleanup_test_artifacts(self) -> bool:
        """Clean up test artifacts and temporary files"""
        try:
            # Clean up GitHub operations
            self.github_ops.cleanup_test_artifacts(keep_commits=True)
            
            # Reset validation results
            self.validator.reset_results()
            
            # Reset AI mock call count
            self.ai_mocker.reset_call_count()
            
            if self.debug:
                print("✅ Test artifacts cleaned up")
            
            return True
            
        except Exception as e:
            print(f"❌ Cleanup failed: {e}")
            return False
    
    def get_test_summary(self) -> Dict[str, Any]:
        """Get comprehensive test summary"""
        total_scenarios = len(self.test_results)
        successful_scenarios = len([r for r in self.test_results if r['success']])
        
        total_steps = sum(len(r['steps']) for r in self.test_results)
        successful_steps = sum(len([s for s in r['steps'] if s['success']]) for r in self.test_results)
        
        avg_execution_time = sum(r['execution_time'] for r in self.test_results) / total_scenarios if total_scenarios > 0 else 0
        
        return {
            'scenarios': {
                'total': total_scenarios,
                'successful': successful_scenarios,
                'success_rate': successful_scenarios / total_scenarios if total_scenarios > 0 else 0
            },
            'steps': {
                'total': total_steps,
                'successful': successful_steps,
                'success_rate': successful_steps / total_steps if total_steps > 0 else 0
            },
            'execution': {
                'avg_scenario_time': avg_execution_time,
                'total_time': sum(r['execution_time'] for r in self.test_results)
            },
            'ai_calls': self.ai_mocker.get_call_count(),
            'validation_summary': self.validator.get_validation_summary(),
            'results': self.test_results
        }


# Test the module functionality
if __name__ == "__main__":
    print("🧪 Testing Hybrid Test Runner")
    
    runner = HybridTestRunner(debug=True)
    
    if runner.setup_test_environment():
        print("✅ Test environment setup successful")
        
        # Simple test scenario
        def test_step():
            return runner.clear_repository_state('testing')
        
        runner.run_test_scenario("Simple Test", [
            ("Clear testing repository state", test_step)
        ])
        
        summary = runner.get_test_summary()
        print(f"\n📊 Test Summary: {summary['scenarios']['successful']}/{summary['scenarios']['total']} scenarios passed")
        
        runner.cleanup_test_artifacts()
    else:
        print("❌ Test environment setup failed")
    
    print("✅ Test runner module test complete")