#!/usr/bin/env python3
"""
Main Integration Test for gh-utils Hybrid Testing Framework
End-to-end test that validates all 3 core functionalities of gh-utils
"""

import sys
import os
import subprocess
import argparse
import time
from datetime import datetime

# Add current directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# Import with error handling
try:
    from test_runner import HybridTestRunner
    from test_scenarios import TestScenariosManager
    from test_reporter import TestReporter
except ImportError:
    # Try absolute imports
    import test_framework.test_runner as test_runner
    import test_framework.test_scenarios as test_scenarios
    import test_framework.test_reporter as test_reporter
    HybridTestRunner = test_runner.HybridTestRunner
    TestScenariosManager = test_scenarios.TestScenariosManager
    TestReporter = test_reporter.TestReporter


class MainTestOrchestrator:
    """Main orchestrator for the complete gh-utils testing suite"""
    
    def __init__(self, debug: bool = False, save_reports: bool = True):
        self.debug = debug
        self.save_reports = save_reports
        
        # Load settings
        self.settings = self._load_settings()
        
        # Initialize core components
        self.runner = HybridTestRunner(debug=debug)
        self.scenarios_manager = TestScenariosManager(self.runner)
        self.reporter = TestReporter(debug=debug)
        
        if self.debug:
            print("🚀 Main Test Orchestrator initialized")
            print(f"   Debug mode: {debug}")
            print(f"   Save reports: {save_reports}")
            print(f"   Delete commits after phase: {self.settings.get('delete_commits_after_phase', True)}")
    
    def _load_settings(self) -> dict:
        """Load settings from settings.txt file"""
        settings = {}
        
        try:
            import configparser
            settings_file = os.path.join(os.path.dirname(__file__), 'settings.txt')
            
            if os.path.exists(settings_file):
                config = configparser.ConfigParser()
                config.read(settings_file)
                
                if 'cleanup' in config:
                    settings['delete_commits_after_phase'] = config.getboolean('cleanup', 'delete_commits_after_phase', fallback=True)
                
                if 'display' in config:
                    settings['hide_first_run_output'] = config.getboolean('display', 'hide_first_run_output', fallback=True)
                    
                if self.debug:
                    print(f"📋 Settings loaded from {settings_file}")
            else:
                # Fallback defaults only if file doesn't exist
                settings = {
                    'delete_commits_after_phase': True,
                    'hide_first_run_output': True
                }
                if self.debug:
                    print("📋 Settings file not found, using defaults")
                    
        except Exception as e:
            # Fallback defaults only on error
            settings = {
                'delete_commits_after_phase': True,
                'hide_first_run_output': True
            }
            print(f"⚠️ Error loading settings: {e}, using defaults")
                
        return settings
    
    def validate_environment(self) -> bool:
        """Validate that the testing environment is ready"""
        print("🔍 Validating test environment...")
        
        try:
            # Check GitHub CLI authentication with elegant real-time solution
            captured_lines = []
            with subprocess.Popen(['gh', 'auth', 'status'], 
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                text=True, bufsize=1,
                                env={**os.environ, 'PYTHONUNBUFFERED': '1'}) as process:
                
                for line in iter(process.stdout.readline, ''):
                    captured_lines.append(line)
                
                return_code = process.wait()
            
            if return_code != 0:
                print("❌ GitHub CLI not authenticated. Run 'gh auth login'")
                return False
            
            # Check gh-utils script exists
            current_file = os.path.abspath(__file__)
            current_dir = os.path.dirname(current_file)
            
            # If we're in a symlinked test_framework, resolve to main project
            if 'github-utils-tests' in current_dir:
                # We're in the worktree, main project is ../github-utils
                project_root = os.path.join(os.path.dirname(os.path.dirname(current_dir)), 'github-utils')
            else:
                # We're in the main project directory
                project_root = os.path.dirname(current_dir)
                
            gh_utils_script = os.path.join(project_root, 'gh-utils.py')
            if not os.path.exists(gh_utils_script):
                print(f"❌ gh-utils.py not found at {gh_utils_script}")
                return False
            
            print("✅ Environment validation passed")
            return True
            
        except Exception as e:
            print(f"❌ Environment validation failed: {e}")
            return False
    
    def setup_test_repositories(self) -> bool:
        """Setup test repositories with correct aliases"""
        if self.debug:
            print("🔧 Setting up test repositories...")
        
        try:
            # Test repositories configuration
            test_repos = {
                # For forks analysis
                'ccusage': 'https://github.com/Durafen/ccusage',
                # For news about forks (treated as regular repo)
                'test-ccusage': 'https://github.com/Durafen/ccusage',
                # For news about regular repository
                'testing': 'https://github.com/Durafen/testing'
            }
            
            current_file = os.path.abspath(__file__)
            current_dir = os.path.dirname(current_file)
            
            # If we're in a symlinked test_framework, resolve to main project
            if 'github-utils-tests' in current_dir:
                # We're in the worktree, main project is ../github-utils
                project_root = os.path.join(os.path.dirname(os.path.dirname(current_dir)), 'github-utils')
            else:
                # We're in the main project directory
                project_root = os.path.dirname(current_dir)
                
            gh_utils_script = os.path.join(project_root, 'gh-utils.py')
            
            # Test repositories assumed to be already in config.txt
            if self.debug:
                for alias, url in test_repos.items():
                    print(f"   ℹ️ Using existing repository {alias}: {url}")
            
            return True
            
        except Exception as e:
            print(f"❌ Repository setup failed: {e}")
            return False
    
    def run_complete_test_suite(self) -> bool:
        """Run the complete test suite with all 3 test types"""
        if self.debug:
            print("\n" + "="*80)
            print("🧪 STARTING COMPLETE GH-UTILS TEST SUITE")
            print("="*80)
            print("Testing 3 core functionalities:")
            print("1. 🍴 Forks Analysis: ./gh-utils.py forks ccusage")
            print("2. 📰 News about Forks: ./gh-utils.py news test-ccusage")
            print("3. 📰 News about Regular: ./gh-utils.py news testing")
            print("="*80)
        
        # Start reporting session
        self.reporter.start_reporting_session()
        
        # Test Type 1: Forks Analysis
        print("\n\n\n\n🍴 TEST PHASE 1: FORKS ANALYSIS")
        print("=" * 60)
        
        forks_results = self._run_forks_analysis_tests()
        self.reporter.add_test_results('forks_analysis', forks_results)
        
        # Test Type 2: News about Forks (using test-ccusage alias)
        print("\n\n\n\n📰 TEST PHASE 2: NEWS ABOUT FORKS")
        print("=" * 60)
        
        news_forks_results = self._run_news_about_forks_tests()
        self.reporter.add_test_results('news_about_forks', news_forks_results)
        
        # Test Type 3: News about Regular Repository
        print("\n\n\n\n📰 TEST PHASE 3: NEWS ABOUT REGULAR REPOSITORY")
        print("=" * 60)
        
        news_regular_results = self._run_news_about_regular_tests()
        self.reporter.add_test_results('news_about_regular', news_regular_results)
        
        # Finalize reporting
        self.reporter.finalize_session()
        
        # Generate and display report
        console_report = self.reporter.generate_console_report()
        print("\n" + console_report)
        
        # Save JSON report if requested
        if self.save_reports:
            json_file = self.reporter.save_json_report()
            if json_file and self.debug:
                print(f"\n💾 Detailed report saved to: {json_file}")
        
        # Determine overall success
        summary = self.reporter.report_data.get('summary', {})
        overall_success_rate = summary.get('overall', {}).get('scenarios', {}).get('success_rate', 0)
        
        return overall_success_rate >= 0.8  # 80% success rate threshold
    
    def _run_forks_analysis_tests(self) -> list:
        """Run forks analysis test scenarios with 10-step validation cycle"""
        scenarios = [
            ('forks_10step_analysis', [
                ('Clear repository states', lambda: self._clear_all_repository_states()),
                ('Run forks analysis baseline', lambda: self.runner.test_forks_analysis('ccusage', 'forks_baseline', hide_execution_log=self.settings.get('hide_first_run_output', True))),
                ('Create main branch commit', lambda: self._create_main_commit('ccusage')),
                ('Test forks analysis after main commit', lambda: self.runner.test_forks_analysis('ccusage', 'forks_main')),
                ('Create branch commit', lambda: self._create_branch_commit_dynamic('ccusage')),
                ('Test forks analysis after branch commit', lambda: self.runner.test_forks_analysis('ccusage', 'forks_branch')),
                ('Create multi-branch commits', lambda: self._create_multi_branch_commits_dynamic('ccusage')),
                ('Test forks analysis after multi-branch commits', lambda: self.runner.test_forks_analysis('ccusage', 'forks_multi')),
                ('Create NEW branch commit', lambda: self.scenarios_manager._create_new_single_branch('ccusage') and self.scenarios_manager._create_commit_on_new_branch('ccusage')),
                ('Test forks analysis after NEW branch commit', lambda: self.runner.test_forks_analysis('ccusage', 'forks_new_branch')),
            ])
        ]
        
        results = []
        for scenario_name, steps in scenarios:
            result = self.runner.run_test_scenario(scenario_name, steps)
            results.append(result)
            time.sleep(2)
        
        # Clean up test commits at end of forks analysis phase (controlled by settings)
        if self.settings.get('delete_commits_after_phase', True):
            if self.debug:
                print("\n🧹 Cleaning up test commits after forks analysis phase...")
            cleanup_success = self.runner.github_ops.cleanup_test_commits(dry_run=False)
            if self.debug:
                status = "✅" if cleanup_success else "⚠️"
                print(f"{status} Forks analysis phase cleanup completed")
        elif self.debug:
            print("\n🔧 Skipping cleanup (delete_commits_after_phase = false)")
        
        return results
    
    def _run_news_about_forks_tests(self) -> list:
        """Run news about forks test scenarios with 10-step validation cycle"""
        scenarios = [
            ('news_forks_10step_analysis', [
                ('Run news baseline', lambda: self.runner.test_news_detection('test-ccusage', 'news_baseline', hide_execution_log=self.settings.get('hide_first_run_output', True))),
                ('Create main branch commit', lambda: self._create_main_commit('ccusage')),
                ('Test news after main commit', lambda: self.runner.test_news_detection('test-ccusage', 'news_main')),
                ('Create branch commit', lambda: self._create_branch_commit_dynamic('ccusage')),
                ('Test news after branch commit', lambda: self.runner.test_news_detection('test-ccusage', 'news_branch')),
                ('Create multi-branch commits', lambda: self._create_multi_branch_commits_dynamic('ccusage')),
                ('Test news after multi-branch commits', lambda: self.runner.test_news_detection('test-ccusage', 'news_multi')),
                ('Create NEW branch commit', lambda: self.scenarios_manager._create_new_single_branch('ccusage') and self.scenarios_manager._create_commit_on_new_branch('ccusage')),
                ('Test news after NEW branch commit', lambda: self.runner.test_news_detection('test-ccusage', 'new_branch')),
            ])
        ]
        
        results = []
        for scenario_name, steps in scenarios:
            result = self.runner.run_test_scenario(scenario_name, steps)
            results.append(result)
            time.sleep(2)
        
        # Clean up test commits at end of news about forks phase (controlled by settings)
        if self.settings.get('delete_commits_after_phase', True):
            if self.debug:
                print("\n🧹 Cleaning up test commits after news about forks phase...")
            cleanup_success = self.runner.github_ops.cleanup_test_commits(dry_run=False)
            if self.debug:
                status = "✅" if cleanup_success else "⚠️"
                print(f"{status} News about forks phase cleanup completed")
        elif self.debug:
            print("\n🔧 Skipping cleanup (delete_commits_after_phase = false)")
        
        return results
    
    def _run_news_about_regular_tests(self) -> list:
        """Run news about regular repository test scenarios with 10-step validation cycle"""
        scenarios = [
            ('news_regular_10step_analysis', [
                ('Run news baseline', lambda: self.runner.test_news_detection('testing', 'news_baseline', hide_execution_log=self.settings.get('hide_first_run_output', True))),
                ('Create main branch commit', lambda: self._create_main_commit('testing')),
                ('Test news after main commit', lambda: self.runner.test_news_detection('testing', 'news_main')),
                ('Create branch commit', lambda: self._create_branch_commit_dynamic('testing')),
                ('Test news after branch commit', lambda: self.runner.test_news_detection('testing', 'news_branch')),
                ('Create multi-branch commits', lambda: self._create_multi_branch_commits_dynamic('testing')),
                ('Test news after multi-branch commits', lambda: self.runner.test_news_detection('testing', 'news_multi')),
                ('Create NEW branch commit', lambda: self.scenarios_manager._create_new_single_branch('testing') and self.scenarios_manager._create_commit_on_new_branch('testing')),
                ('Test news after NEW branch commit', lambda: self.runner.test_news_detection('testing', 'new_branch')),
            ])
        ]
        
        results = []
        for scenario_name, steps in scenarios:
            result = self.runner.run_test_scenario(scenario_name, steps)
            results.append(result)
            time.sleep(2)
        
        # Clean up test commits at end of news about regular phase (controlled by settings)
        if self.settings.get('delete_commits_after_phase', True):
            if self.debug:
                print("\n🧹 Cleaning up test commits after news about regular phase...")
            cleanup_success = self.runner.github_ops.cleanup_test_commits(dry_run=False)
            if self.debug:
                status = "✅" if cleanup_success else "⚠️"
                print(f"{status} News about regular phase cleanup completed")
        elif self.debug:
            print("\n🔧 Skipping cleanup (delete_commits_after_phase = false)")
        
        return results
    
    # Helper methods (same as in TestScenariosManager but simplified)
    def _clear_all_repository_states(self) -> bool:
        """Clear repository states for all test repositories"""
        test_repos = ['ccusage', 'test-ccusage', 'testing']
        success = True
        
        for repo_name in test_repos:
            try:
                repo_success = self.runner.clear_repository_state(repo_name)
                if self.debug:
                    status = "✅" if repo_success else "⚠️"
                    print(f"{status} Cleared state for {repo_name}")
                # Don't fail overall if individual repo clear fails (may not have state)
            except Exception as e:
                print(f"⚠️ Failed to clear state for {repo_name}: {e}")
                # Continue with other repos
        
        return success
    
    def _create_main_commit(self, repo_name: str) -> bool:
        timestamp = int(time.time())
        message = f"Test main branch commit - {timestamp}"
        return self.runner.create_test_commit(repo_name, 'main', message)
    
    def _create_test_branch(self, repo_name: str, branch_name: str) -> bool:
        return self.runner.github_ops.create_dynamic_test_branch(repo_name, branch_name)
    
    def _create_branch_commit(self, repo_name: str, branch_name: str) -> bool:
        timestamp = int(time.time())
        message = f"Test {branch_name} branch commit - {timestamp}"
        return self.runner.create_test_commit(repo_name, branch_name, message)
    
    def _create_branch_commit_dynamic(self, repo_name: str) -> bool:
        """Create branch commit using last non-main branch, or fall back to hardcoded"""
        # Try to get last non-main branch
        branch_name = self.runner.github_ops.get_last_non_main_branch(repo_name)
        
        if not branch_name:
            # Fall back to creating test-feature branch
            branch_name = 'test-feature'
            if self.debug:
                print(f"ℹ️  No non-main branches found for {repo_name}, using {branch_name}")
            
            # Create the branch first
            if not self._create_test_branch(repo_name, branch_name):
                return False
        
        timestamp = int(time.time())
        message = f"Test {branch_name} branch commit - {timestamp}"
        success = self.runner.create_test_commit(repo_name, branch_name, message)
        
        if self.debug and success:
            print(f"✅ Created commit on {repo_name}/{branch_name}")
        
        return success
    
    def _create_multi_branch_commits(self, repo_name: str) -> bool:
        """Create commits on both main and test-feature branches"""
        timestamp = int(time.time())
        
        # Create commit on main branch
        main_success = self.runner.create_test_commit(
            repo_name, 'main', f"Test multi-branch main commit - {timestamp}"
        )
        
        # Create commit on test-feature branch
        branch_success = self.runner.create_test_commit(
            repo_name, 'test-feature', f"Test multi-branch feature commit - {timestamp}"
        )
        
        return main_success and branch_success
    
    def _create_multi_branch_commits_dynamic(self, repo_name: str) -> bool:
        """Create commits on both main and last non-main branch"""
        timestamp = int(time.time())
        
        # Create commit on main branch
        main_success = self.runner.create_test_commit(
            repo_name, 'main', f"Test multi-branch main commit - {timestamp}"
        )
        
        # Get last non-main branch or use test-feature
        branch_name = self.runner.github_ops.get_last_non_main_branch(repo_name)
        if not branch_name:
            branch_name = 'test-feature'
            # Create the branch if it doesn't exist
            self._create_test_branch(repo_name, branch_name)
        
        # Create commit on the selected branch
        branch_success = self.runner.create_test_commit(
            repo_name, branch_name, f"Test multi-branch {branch_name} commit - {timestamp}"
        )
        
        if self.debug:
            print(f"✅ Created multi-branch commits: main + {branch_name}")
        
        return main_success and branch_success
    
    def _validate_state_updated(self, repo_name: str) -> bool:
        repo_key = f"durafen/{repo_name}"
        expected_changes = {
            'last_check': None,
            'last_commit': 'regex:.+'
        }
        return self.runner.validator.validate_state_updated(repo_key, expected_changes)
    
    def _validate_branch_state_updated(self, repo_name: str, branch_name: str) -> bool:
        repo_key = f"durafen/{repo_name}"
        expected_changes = {
            'branches': None,
            'last_branch_check': None
        }
        return self.runner.validator.validate_state_updated(repo_key, expected_changes)
    
    def cleanup(self) -> bool:
        """Clean up test artifacts"""
        try:
            if self.debug:
                print("\n🧹 Cleaning up test artifacts...")
            
            success = self.runner.cleanup_test_artifacts()
            
            if self.debug:
                status = "✅" if success else "⚠️"
                print(f"{status} Cleanup completed")
            
            return success
            
        except Exception as e:
            print(f"❌ Cleanup failed: {e}")
            return False


def main():
    """Main entry point for the testing framework"""
    parser = argparse.ArgumentParser(
        description="gh-utils Hybrid Testing Framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Test Types:
  1. Forks Analysis:        ./gh-utils.py forks ccusage
  2. News about Forks:     ./gh-utils.py news test-ccusage  
  3. News about Regular:   ./gh-utils.py news testing

Examples:
  python3 test_framework/main_test.py --debug
  python3 test_framework/main_test.py --no-save-reports
        """
    )
    
    parser.add_argument('--debug', action='store_true', 
                       help='Enable debug output')
    parser.add_argument('--no-save-reports', action='store_true',
                       help='Skip saving JSON reports')
    
    args = parser.parse_args()
    
    # Initialize orchestrator
    orchestrator = MainTestOrchestrator(
        debug=args.debug,
        save_reports=not args.no_save_reports
    )
    
    print("🚀 gh-utils Hybrid Testing Framework")
    print("=" * 50)
    
    try:
        # Environment validation
        if not orchestrator.validate_environment():
            print("❌ Environment validation failed")
            return 1
        
        # Setup test environment
        if not orchestrator.runner.setup_test_environment():
            print("❌ Test environment setup failed")
            return 1
        
        if not orchestrator.setup_test_repositories():
            print("❌ Test repository setup failed")
            return 1
        
        # Run complete test suite
        success = orchestrator.run_complete_test_suite()
        
        # Cleanup
        orchestrator.cleanup()
        
        # Final status
        if success:
            print("\n🎉 All tests completed successfully!")
            return 0
        else:
            print("\n⚠️ Some tests failed. Check the report above for details.")
            return 1
            
    except KeyboardInterrupt:
        print("\n\n⚠️ Testing interrupted by user")
        orchestrator.cleanup()
        return 130
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        orchestrator.cleanup()
        return 1


if __name__ == "__main__":
    exit(main())