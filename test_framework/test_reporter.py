#!/usr/bin/env python3
"""
Test Reporter Module for gh-utils Testing Framework
Generates comprehensive reports with ✅/❌ indicators and detailed summaries
"""

import json
import time
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta


class TestReporter:
    """Generates comprehensive test reports with visual indicators and analytics"""
    
    def __init__(self, debug: bool = False):
        self.debug = debug
        self.report_data = {}
        self.start_time = None
        self.end_time = None
    
    def start_reporting_session(self):
        """Start a new reporting session"""
        self.start_time = datetime.now()
        self.report_data = {
            'session_start': self.start_time.isoformat(),
            'test_results': {},
            'summary': {},
            'metadata': {}
        }
        
        if self.debug:
            print("📊 Reporting session started")
    
    def add_test_results(self, test_type: str, results: List[Dict[str, Any]]):
        """Add test results for a specific test type"""
        self.report_data['test_results'][test_type] = results
        
        if self.debug:
            print(f"📋 Added {len(results)} results for {test_type}")
    
    def finalize_session(self):
        """Finalize the reporting session"""
        self.end_time = datetime.now()
        self.report_data['session_end'] = self.end_time.isoformat()
        
        if self.start_time:
            duration = self.end_time - self.start_time
            self.report_data['session_duration'] = duration.total_seconds()
        
        # Generate summary
        self.report_data['summary'] = self._generate_summary()
        
        if self.debug:
            print("📊 Reporting session finalized")
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate comprehensive summary from test results"""
        test_results = self.report_data.get('test_results', {})
        
        # Overall statistics
        total_test_types = len(test_results)
        total_scenarios = sum(len(results) for results in test_results.values())
        successful_scenarios = sum(
            len([r for r in results if r['success']]) 
            for results in test_results.values()
        )
        
        # Step statistics
        total_steps = 0
        successful_steps = 0
        
        for results in test_results.values():
            for scenario in results:
                steps = scenario.get('steps', [])
                total_steps += len(steps)
                successful_steps += len([s for s in steps if s['success']])
        
        # Performance statistics
        execution_times = []
        for results in test_results.values():
            for scenario in results:
                execution_times.append(scenario.get('execution_time', 0))
        
        avg_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0
        total_execution_time = sum(execution_times)
        
        # Test type breakdown
        test_type_breakdown = {}
        for test_type, results in test_results.items():
            successful = len([r for r in results if r['success']])
            test_type_breakdown[test_type] = {
                'total': len(results),
                'successful': successful,
                'success_rate': successful / len(results) if results else 0,
                'avg_time': sum(r.get('execution_time', 0) for r in results) / len(results) if results else 0
            }
        
        return {
            'overall': {
                'test_types': total_test_types,
                'scenarios': {
                    'total': total_scenarios,
                    'successful': successful_scenarios,
                    'success_rate': successful_scenarios / total_scenarios if total_scenarios > 0 else 0
                },
                'steps': {
                    'total': total_steps,
                    'successful': successful_steps,
                    'success_rate': successful_steps / total_steps if total_steps > 0 else 0
                }
            },
            'performance': {
                'avg_scenario_time': avg_execution_time,
                'total_execution_time': total_execution_time,
                'session_duration': self.report_data.get('session_duration', 0)
            },
            'test_type_breakdown': test_type_breakdown
        }
    
    def generate_console_report(self) -> str:
        """Generate a detailed console report with visual indicators"""
        if not self.report_data:
            return "❌ No test data available for reporting"
        
        report_lines = []
        
        # Header
        report_lines.append("=" * 80)
        report_lines.append("🧪 GH-UTILS HYBRID TESTING FRAMEWORK REPORT")
        report_lines.append("=" * 80)
        
        # Session info
        session_start = self.report_data.get('session_start', 'Unknown')
        session_duration = self.report_data.get('session_duration', 0)
        report_lines.append(f"📅 Session: {session_start}")
        report_lines.append(f"⏱️  Duration: {session_duration:.2f} seconds")
        report_lines.append("")
        
        # Overall summary
        summary = self.report_data.get('summary', {})
        overall = summary.get('overall', {})
        
        scenarios = overall.get('scenarios', {})
        steps = overall.get('steps', {})
        
        scenario_success_rate = scenarios.get('success_rate', 0) * 100
        step_success_rate = steps.get('success_rate', 0) * 100
        
        overall_status = "✅" if scenario_success_rate >= 80 else "⚠️" if scenario_success_rate >= 60 else "❌"
        
        report_lines.append("📊 OVERALL RESULTS")
        report_lines.append("-" * 40)
        report_lines.append(f"{overall_status} Success Rate: {scenario_success_rate:.1f}%")
        report_lines.append(f"🎯 Scenarios: {scenarios.get('successful', 0)}/{scenarios.get('total', 0)} passed")
        report_lines.append(f"📋 Steps: {steps.get('successful', 0)}/{steps.get('total', 0)} passed")
        report_lines.append("")
        
        # Performance summary
        performance = summary.get('performance', {})
        report_lines.append("⚡ PERFORMANCE METRICS")
        report_lines.append("-" * 40)
        report_lines.append(f"⏱️  Average scenario time: {performance.get('avg_scenario_time', 0):.2f}s")
        report_lines.append(f"🕐 Total execution time: {performance.get('total_execution_time', 0):.2f}s")
        report_lines.append("")
        
        # Test type breakdown
        test_type_breakdown = summary.get('test_type_breakdown', {})
        if test_type_breakdown:
            report_lines.append("🧪 TEST TYPE BREAKDOWN")
            report_lines.append("-" * 40)
            
            for test_type, stats in test_type_breakdown.items():
                success_rate = stats.get('success_rate', 0) * 100
                status = "✅" if success_rate >= 80 else "⚠️" if success_rate >= 60 else "❌"
                test_type_display = test_type.replace('_', ' ').title()
                
                report_lines.append(f"{status} {test_type_display}")
                report_lines.append(f"   Scenarios: {stats.get('successful', 0)}/{stats.get('total', 0)} ({success_rate:.1f}%)")
                report_lines.append(f"   Avg Time: {stats.get('avg_time', 0):.2f}s")
            
            report_lines.append("")
        
        # Detailed scenario results
        test_results = self.report_data.get('test_results', {})
        if test_results:
            report_lines.append("📋 DETAILED SCENARIO RESULTS")
            report_lines.append("-" * 40)
            
            for test_type, results in test_results.items():
                test_type_display = test_type.replace('_', ' ').title()
                report_lines.append(f"\n🔍 {test_type_display}:")
                
                for scenario in results:
                    scenario_name = scenario.get('name', 'Unknown')
                    scenario_success = scenario.get('success', False)
                    scenario_time = scenario.get('execution_time', 0)
                    steps = scenario.get('steps', [])
                    
                    status = "✅" if scenario_success else "❌"
                    passed_steps = len([s for s in steps if s['success']])
                    
                    report_lines.append(f"  {status} {scenario_name} ({scenario_time:.2f}s)")
                    report_lines.append(f"     Steps: {passed_steps}/{len(steps)} passed")
                    
                    # Show failed steps
                    if not scenario_success:
                        failed_steps = [s for s in steps if not s['success']]
                        for step in failed_steps:
                            step_name = step.get('name', 'Unknown')
                            error = step.get('error', '')
                            report_lines.append(f"     ❌ {step_name}")
                            if error:
                                report_lines.append(f"        Error: {error[:100]}...")
        
        # Recommendations
        report_lines.append("")
        report_lines.append("💡 RECOMMENDATIONS")
        report_lines.append("-" * 40)
        
        if scenario_success_rate >= 90:
            report_lines.append("✅ Excellent! All systems functioning properly.")
        elif scenario_success_rate >= 70:
            report_lines.append("⚠️  Good performance with minor issues to address.")
            report_lines.append("   - Review failed scenarios for optimization opportunities")
        else:
            report_lines.append("❌ Significant issues detected requiring attention:")
            report_lines.append("   - Review test failures and error messages")
            report_lines.append("   - Check GitHub authentication and network connectivity")
            report_lines.append("   - Verify repository configurations")
        
        # Footer
        report_lines.append("")
        report_lines.append("=" * 80)
        report_lines.append("🏁 End of Report")
        report_lines.append("=" * 80)
        
        return "\n".join(report_lines)
    
    def save_json_report(self, filename: Optional[str] = None) -> str:
        """Save detailed JSON report to file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"test_reports/test_report_{timestamp}.json"
        
        # Ensure test_reports directory exists
        import os
        os.makedirs(os.path.dirname(filename) if os.path.dirname(filename) else "test_reports", exist_ok=True)
        
        try:
            with open(filename, 'w') as f:
                json.dump(self.report_data, f, indent=2, default=str)
            
            if self.debug:
                print(f"💾 JSON report saved to {filename}")
            
            return filename
            
        except Exception as e:
            if self.debug:
                print(f"❌ Failed to save JSON report: {e}")
            return ""
    
    def generate_quick_summary(self) -> str:
        """Generate a quick one-line summary"""
        if not self.report_data or 'summary' not in self.report_data:
            return "❌ No test data available"
        
        summary = self.report_data['summary']
        scenarios = summary.get('overall', {}).get('scenarios', {})
        
        total = scenarios.get('total', 0)
        successful = scenarios.get('successful', 0)
        success_rate = scenarios.get('success_rate', 0) * 100
        
        status = "✅" if success_rate >= 80 else "⚠️" if success_rate >= 60 else "❌"
        
        return f"{status} {successful}/{total} scenarios passed ({success_rate:.1f}%)"
    
    def get_failed_scenarios(self) -> List[Dict[str, Any]]:
        """Get list of failed scenarios for debugging"""
        failed_scenarios = []
        
        test_results = self.report_data.get('test_results', {})
        for test_type, results in test_results.items():
            for scenario in results:
                if not scenario.get('success', True):
                    failed_scenarios.append({
                        'test_type': test_type,
                        'scenario_name': scenario.get('name', 'Unknown'),
                        'execution_time': scenario.get('execution_time', 0),
                        'failed_steps': [s for s in scenario.get('steps', []) if not s['success']],
                        'error_summary': self._extract_error_summary(scenario)
                    })
        
        return failed_scenarios
    
    def _extract_error_summary(self, scenario: Dict[str, Any]) -> str:
        """Extract a summary of errors from a failed scenario"""
        steps = scenario.get('steps', [])
        failed_steps = [s for s in steps if not s['success']]
        
        if not failed_steps:
            return "No specific error information available"
        
        error_messages = []
        for step in failed_steps:
            step_name = step.get('name', 'Unknown step')
            error = step.get('error', 'Unknown error')
            error_messages.append(f"{step_name}: {error[:100]}")
        
        return "; ".join(error_messages)


# Test the module functionality
if __name__ == "__main__":
    print("🧪 Testing Test Reporter")
    
    reporter = TestReporter(debug=True)
    reporter.start_reporting_session()
    
    # Add some mock test results
    mock_results = [
        {
            'name': 'test_scenario_1',
            'success': True,
            'execution_time': 15.5,
            'steps': [
                {'name': 'step1', 'success': True, 'execution_time': 5.0},
                {'name': 'step2', 'success': True, 'execution_time': 10.5}
            ]
        },
        {
            'name': 'test_scenario_2',
            'success': False,
            'execution_time': 8.2,
            'steps': [
                {'name': 'step1', 'success': True, 'execution_time': 3.0},
                {'name': 'step2', 'success': False, 'execution_time': 5.2, 'error': 'Connection timeout'}
            ]
        }
    ]
    
    reporter.add_test_results('test_type_1', mock_results)
    reporter.finalize_session()
    
    # Generate reports
    print("\n" + reporter.generate_console_report())
    print("\n📋 Quick Summary:", reporter.generate_quick_summary())
    
    failed = reporter.get_failed_scenarios()
    if failed:
        print(f"\n❌ Found {len(failed)} failed scenarios")
    
    print("\n✅ Test reporter module test complete")