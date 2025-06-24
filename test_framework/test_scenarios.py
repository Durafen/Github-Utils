#!/usr/bin/env python3
"""
Test Scenarios Definition for gh-utils Hybrid Testing
Defines all 3 core test types with 7-step validation cycles
"""

import time
from typing import Dict, List, Tuple, Callable, Any

# Handle imports for both relative and direct execution
try:
    from .test_runner import HybridTestRunner
except ImportError:
    from test_runner import HybridTestRunner


class TestScenariosManager:
    """Manages and defines all test scenarios for the testing framework"""
    
    def __init__(self, test_runner: HybridTestRunner):
        self.runner = test_runner
        self.debug = test_runner.debug
        self.new_branches = {}  # repo_name -> branch_name mapping for tracking dynamic branches
    
    def get_all_test_scenarios(self) -> Dict[str, List[Tuple[str, List[Tuple[str, Callable]]]]]:
        """Get all defined test scenarios organized by test type"""
        return {
            'forks_analysis': self._get_forks_analysis_scenarios(),
            'news_about_forks': self._get_news_about_forks_scenarios(),
            'news_about_regular': self._get_news_about_regular_scenarios()
        }
    
    def _get_forks_analysis_scenarios(self) -> List[Tuple[str, List[Tuple[str, Callable]]]]:
        """Test Type 1: Forks Analysis - ./gh-utils.py forks ant-javacard"""
        return [
            ('forks_basic_analysis', [
                ('Clear ant-javacard state', lambda: self.runner.clear_repository_state('ant-javacard')),
                ('Test forks analysis command', lambda: self.runner.test_forks_analysis('ant-javacard')),
                ('Validate fork detection patterns', lambda: self._validate_fork_output_patterns()),
                ('Verify performance metrics', lambda: self._validate_forks_performance()),
            ]),
            ('forks_main_branch', [
                ('Clear ant-javacard state', lambda: self.runner.clear_repository_state('ant-javacard')),
                ('Create main branch commit', lambda: self._create_main_commit('ant-javacard')),
                ('Test main branch forks detection', lambda: self.runner.test_forks_analysis('ant-javacard')),
                ('Validate main branch patterns', lambda: self._validate_fork_output_patterns()),
                ('Verify state update', lambda: self._validate_forks_performance()),
            ]),
            ('forks_multi_branch', [
                ('Clear ant-javacard state', lambda: self.runner.clear_repository_state('ant-javacard')),
                ('Create main branch commit', lambda: self._create_main_commit('ant-javacard')),
                ('Create feature branch commit', lambda: self._create_branch_commit('ant-javacard', 'test-feature')),
                ('Test multi-branch forks detection', lambda: self.runner.test_forks_analysis('ant-javacard')),
                ('Validate multi-branch patterns', lambda: self._validate_fork_output_patterns()),
                ('Verify comprehensive performance', lambda: self._validate_forks_performance()),
            ]),
            ('forks_new_branch_analysis', [
                ('Create NEW branch', lambda: self._create_new_single_branch('ant-javacard')),
                ('Create commit on NEW branch', lambda: self._create_commit_on_new_branch('ant-javacard')),
                ('Test NEW branch forks detection', lambda: self.runner.test_forks_analysis('ant-javacard')),
                ('Validate NEW branch in forks output', lambda: self._validate_new_branch_in_forks()),
            ])
        ]
    
    def _get_news_about_forks_scenarios(self) -> List[Tuple[str, List[Tuple[str, Callable]]]]:
        """Test Type 2: News About Forks - ./gh-utils.py news ant-javacard (treating fork as regular repo)"""
        return [
            ('news_forks_main_branch', [
                ('Clear ant-javacard news state', lambda: self.runner.clear_repository_state('ant-javacard')),
                ('Create main branch commit', lambda: self._create_main_commit('ant-javacard')),
                ('Test main branch news detection', lambda: self.runner.test_news_detection('ant-javacard', 'news_main')),
                ('Validate main branch patterns', lambda: self._validate_main_branch_news()),
                ('Verify state update', lambda: self._validate_state_updated('ant-javacard')),
            ]),
            ('news_forks_feature_branch', [
                ('Clear ant-javacard news state', lambda: self.runner.clear_repository_state('ant-javacard')),
                ('Create feature branch', lambda: self._create_dynamic_test_branch('ant-javacard', 'test-feature')),
                ('Create feature branch commit', lambda: self._create_branch_commit('ant-javacard', 'test-feature')),
                ('Test branch news detection', lambda: self.runner.test_news_detection('ant-javacard', 'news_branch')),
                ('Validate branch patterns', lambda: self._validate_branch_news()),
                ('Verify branch state update', lambda: self._validate_branch_state_updated('ant-javacard', 'test-feature')),
            ]),
            ('news_forks_multi_branch', [
                ('Clear ant-javacard news state', lambda: self.runner.clear_repository_state('ant-javacard')),
                ('Create main branch commit', lambda: self._create_main_commit('ant-javacard')),
                ('Create feature branch commit', lambda: self._create_branch_commit('ant-javacard', 'test-feature')),
                ('Test multi-branch news detection', lambda: self.runner.test_news_detection('ant-javacard', 'news_multi')),
                ('Validate multi-branch patterns', lambda: self._validate_multi_branch_news()),
                ('Verify comprehensive state', lambda: self._validate_comprehensive_state('ant-javacard')),
            ]),
            ('news_forks_new_branch', [
                ('Create NEW branch', lambda: self._create_new_single_branch('ant-javacard')),
                ('Create commit on NEW branch', lambda: self._create_commit_on_new_branch('ant-javacard')),
                ('Test NEW branch news detection', lambda: self.runner.test_news_detection('ant-javacard', 'new_branch')),
                ('Validate NEW branch patterns', lambda: self._validate_new_single_branch()),
            ])
        ]
    
    def _get_news_about_regular_scenarios(self) -> List[Tuple[str, List[Tuple[str, Callable]]]]:
        """Test Type 3: News About Regular Repository - ./gh-utils.py news testing"""
        return [
            ('news_regular_main_branch', [
                ('Clear testing state', lambda: self.runner.clear_repository_state('testing')),
                ('Create main branch commit', lambda: self._create_main_commit('testing')),
                ('Test main branch news detection', lambda: self.runner.test_news_detection('testing', 'news_main')),
                ('Validate main branch patterns', lambda: self._validate_main_branch_news()),
                ('Verify state update', lambda: self._validate_state_updated('testing')),
            ]),
            ('news_regular_feature_branch', [
                ('Clear testing state', lambda: self.runner.clear_repository_state('testing')),
                ('Create feature branch', lambda: self._create_dynamic_test_branch('testing', 'test-feature')),
                ('Create feature branch commit', lambda: self._create_branch_commit('testing', 'test-feature')),
                ('Test branch news detection', lambda: self.runner.test_news_detection('testing', 'news_branch')),
                ('Validate branch patterns', lambda: self._validate_branch_news()),
                ('Verify branch state update', lambda: self._validate_branch_state_updated('testing', 'test-feature')),
            ]),
            ('news_regular_multi_branch', [
                ('Clear testing state', lambda: self.runner.clear_repository_state('testing')),
                ('Create main branch commit', lambda: self._create_main_commit('testing')),
                ('Create feature branch commit', lambda: self._create_branch_commit('testing', 'test-feature')),
                ('Test multi-branch news detection', lambda: self.runner.test_news_detection('testing', 'news_multi')),
                ('Validate multi-branch patterns', lambda: self._validate_multi_branch_news()),
                ('Verify comprehensive state', lambda: self._validate_comprehensive_state('testing')),
            ]),
            ('news_regular_new_branch', [
                ('Create NEW branch', lambda: self._create_new_single_branch('testing')),
                ('Create commit on NEW branch', lambda: self._create_commit_on_new_branch('testing')),
                ('Test NEW branch news detection', lambda: self.runner.test_news_detection('testing', 'new_branch')),
                ('Validate NEW branch patterns', lambda: self._validate_new_single_branch()),
            ])
        ]
    
    # Helper methods for test steps
    
    def _create_main_commit(self, repo_name: str) -> bool:
        """Create a commit on the main branch"""
        try:
            timestamp = int(time.time())
            message = f"Test main branch commit - {timestamp}"
            success = self.runner.create_test_commit(repo_name, None, message)
            
            if self.debug and success:
                print(f"✅ Created main branch commit for {repo_name}")
            
            return success
            
        except Exception as e:
            print(f"❌ Failed to create main commit for {repo_name}: {e}")
            return False
    
    def _create_dynamic_test_branch(self, repo_name: str, branch_name: str) -> bool:
        """Create a dynamic test branch"""
        try:
            success = self.runner.github_ops.create_dynamic_test_branch(repo_name, branch_name)
            
            if self.debug and success:
                print(f"✅ Created branch {branch_name} for {repo_name}")
            
            return success
            
        except Exception as e:
            print(f"❌ Failed to create branch {branch_name} for {repo_name}: {e}")
            return False
    
    def _create_branch_commit(self, repo_name: str, branch_name: str) -> bool:
        """Create a commit on a specific branch"""
        try:
            timestamp = int(time.time())
            message = f"Test {branch_name} branch commit - {timestamp}"
            success = self.runner.create_test_commit(repo_name, branch_name, message)
            
            if self.debug and success:
                print(f"✅ Created commit on {repo_name}/{branch_name}")
            
            return success
            
        except Exception as e:
            print(f"❌ Failed to create commit on {repo_name}/{branch_name}: {e}")
            return False
    
    def _create_new_single_branch(self, repo_name: str) -> bool:
        """Create a completely new branch with unique timestamp name"""
        try:
            timestamp = int(time.time())
            branch_name = f"test-new-{timestamp}"
            
            # Store for later validation
            self.new_branches[repo_name] = branch_name
            
            success = self.runner.github_ops.create_dynamic_test_branch(repo_name, branch_name)
            
            if success:
                # Use same format as other commits - extract real GitHub path
                repo_url = self.runner.github_ops.test_repos.get(repo_name, '')
                if 'github.com/' in repo_url:
                    repo_path = repo_url.split('github.com/')[-1]
                    if repo_path.endswith('.git'):
                        repo_path = repo_path[:-4]
                    print(f"🌿 Branch: {repo_path}/{branch_name}")
                else:
                    print(f"🌿 Branch: {repo_name}/{branch_name}")
            
            return success
            
        except Exception as e:
            print(f"❌ Failed to create NEW branch for {repo_name}: {e}")
            return False
    
    def _create_commit_on_new_branch(self, repo_name: str) -> bool:
        """Create commit on the newly created branch"""
        try:
            if repo_name not in self.new_branches:
                if self.debug:
                    print(f"❌ No NEW branch found for {repo_name}")
                return False
            
            branch_name = self.new_branches[repo_name]
            timestamp = int(time.time())
            message = f"Test new branch commit - {timestamp}"
            success = self.runner.create_test_commit(repo_name, branch_name, message)
            # Note: Commit message already printed by github_operations.py
            return success
            
        except Exception as e:
            print(f"❌ Failed to create commit on NEW branch for {repo_name}: {e}")
            return False
    
    def _validate_new_single_branch(self) -> bool:
        """Validate that the NEW branch appears in output"""
        # Validation done in test_news_detection
        return True
    
    def _validate_new_branch_in_forks(self) -> bool:
        """Validate that the NEW branch appears in forks output"""
        # Validation done in test_forks_analysis
        return True
    
    # Validation helper methods
    
    def _validate_fork_output_patterns(self) -> bool:
        """Validate fork analysis output contains expected patterns"""
        # This validation is done in test_forks_analysis, so we just return True
        # The actual validation happens in the TestValidator
        return True
    
    def _validate_forks_performance(self) -> bool:
        """Validate forks analysis performance is acceptable"""
        # Performance validation is done in test_forks_analysis
        return True
    
    def _validate_main_branch_news(self) -> bool:
        """Validate main branch news output patterns"""
        # Output validation is done in test_news_detection
        return True
    
    def _validate_branch_news(self) -> bool:
        """Validate branch news output patterns"""
        # Output validation is done in test_news_detection
        return True
    
    def _validate_multi_branch_news(self) -> bool:
        """Validate multi-branch news output patterns"""
        # Output validation is done in test_news_detection
        return True
    
    def _validate_state_updated(self, repo_name: str) -> bool:
        """Validate that repository state was updated correctly"""
        try:
            repo_key = f"durafen/{repo_name}"
            expected_changes = {
                'last_check': None,  # Just check if exists
                'last_commit': 'regex:.+'  # Check if has some commit SHA
            }
            
            return self.runner.validator.validate_state_updated(repo_key, expected_changes)
            
        except Exception as e:
            print(f"❌ State validation failed for {repo_name}: {e}")
            return False
    
    def _validate_branch_state_updated(self, repo_name: str, branch_name: str) -> bool:
        """Validate that branch state was updated correctly"""
        try:
            repo_key = f"durafen/{repo_name}"
            expected_changes = {
                'branches': None,  # Check if branches section exists
                'last_branch_check': None  # Check if branch check timestamp exists
            }
            
            return self.runner.validator.validate_state_updated(repo_key, expected_changes)
            
        except Exception as e:
            print(f"❌ Branch state validation failed for {repo_name}/{branch_name}: {e}")
            return False
    
    def _validate_comprehensive_state(self, repo_name: str) -> bool:
        """Validate comprehensive state for multi-branch scenario"""
        try:
            repo_key = f"durafen/{repo_name}"
            expected_changes = {
                'last_check': None,
                'last_commit': 'regex:.+',
                'branches': None,
                'last_branch_check': None
            }
            
            return self.runner.validator.validate_state_updated(repo_key, expected_changes)
            
        except Exception as e:
            print(f"❌ Comprehensive state validation failed for {repo_name}: {e}")
            return False
    
    def run_all_scenarios(self) -> Dict[str, Any]:
        """Run all test scenarios and return comprehensive results"""
        if self.debug:
            print("🚀 Starting comprehensive test suite...")
        
        all_scenarios = self.get_all_test_scenarios()
        results = {}
        
        for test_type, scenarios in all_scenarios.items():
            if self.debug:
                print(f"\n{'='*60}")
                print(f"🧪 Test Type: {test_type.replace('_', ' ').title()}")
                print(f"{'='*60}")
            
            test_type_results = []
            
            for scenario_name, steps in scenarios:
                result = self.runner.run_test_scenario(scenario_name, steps)
                test_type_results.append(result)
                
                # Small delay between scenarios
                time.sleep(2)
            
            results[test_type] = test_type_results
        
        if self.debug:
            print(f"\n{'='*60}")
            print("🏁 All test scenarios completed")
            print(f"{'='*60}")
        
        return results
    
    def run_specific_test_type(self, test_type: str) -> List[Dict[str, Any]]:
        """Run scenarios for a specific test type"""
        all_scenarios = self.get_all_test_scenarios()
        
        if test_type not in all_scenarios:
            raise ValueError(f"Unknown test type: {test_type}. Available: {list(all_scenarios.keys())}")
        
        scenarios = all_scenarios[test_type]
        results = []
        
        if self.debug:
            print(f"🧪 Running {test_type.replace('_', ' ').title()} scenarios...")
        
        for scenario_name, steps in scenarios:
            result = self.runner.run_test_scenario(scenario_name, steps)
            results.append(result)
            
            # Small delay between scenarios
            time.sleep(2)
        
        return results


# Test the module functionality
if __name__ == "__main__":
    print("🧪 Testing Scenarios Manager")
    
    try:
        from .test_runner import HybridTestRunner
    except ImportError:
        from test_runner import HybridTestRunner
    
    runner = HybridTestRunner(debug=True)
    scenarios_manager = TestScenariosManager(runner)
    
    if runner.setup_test_environment():
        print("✅ Test environment setup successful")
        
        # Test getting scenarios
        all_scenarios = scenarios_manager.get_all_test_scenarios()
        total_scenarios = sum(len(scenarios) for scenarios in all_scenarios.values())
        
        print(f"📊 Defined {total_scenarios} test scenarios across {len(all_scenarios)} test types:")
        for test_type, scenarios in all_scenarios.items():
            print(f"   - {test_type}: {len(scenarios)} scenarios")
        
        runner.cleanup_test_artifacts()
    else:
        print("❌ Test environment setup failed")
    
    print("✅ Scenarios manager test complete")