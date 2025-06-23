#!/usr/bin/env python3
"""
Test Commit Pattern Definitions
Defines regex patterns to identify test commits created by the testing framework
"""

import re
from typing import List, Pattern

class TestCommitPatterns:
    """Centralized patterns for identifying test commits"""
    
    def __init__(self):
        # Define all test commit patterns based on the test framework code
        self.patterns = [
            # From github_operations.py: "Test commit - {datetime}"
            r'^Test commit - \d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}',
            
            # From main_test.py: "Test main branch commit - {timestamp}"
            r'^Test main branch commit - \d+$',
            
            # From main_test.py: "Test {branch_name} branch commit - {timestamp}"
            r'^Test .+ branch commit - \d+$',
            
            # From main_test.py: "Test multi-branch main commit - {timestamp}"
            r'^Test multi-branch main commit - \d+$',
            
            # From main_test.py: "Test multi-branch {branch_name} commit - {timestamp}"
            r'^Test multi-branch .+ commit - \d+$',
            
            # From test_runner.py: "Test framework commit - {timestamp}"
            r'^Test framework commit - \d+$',
            
            # Generic test patterns (catch-all for variations)
            r'^Test .* commit.*$',
            r'^.*Test framework.*$',
        ]
        
        # Compile patterns for performance
        self.compiled_patterns: List[Pattern] = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.patterns
        ]
    
    def is_test_commit(self, commit_message: str) -> bool:
        """Check if a commit message matches any test pattern"""
        commit_message = commit_message.strip()
        
        # Check each compiled pattern
        for pattern in self.compiled_patterns:
            if pattern.match(commit_message):
                return True
        
        return False
    
    def get_pattern_descriptions(self) -> List[str]:
        """Get human-readable descriptions of the patterns"""
        descriptions = [
            "Test commit with ISO datetime",
            "Test main branch commit with timestamp", 
            "Test branch commit with timestamp",
            "Test multi-branch main commit with timestamp",
            "Test multi-branch specific commit with timestamp",
            "Test framework commit with timestamp",
            "Generic test commit (catch-all)",
            "Test framework variations (catch-all)"
        ]
        return descriptions
    
    def get_raw_patterns(self) -> List[str]:
        """Get the raw regex patterns"""
        return self.patterns.copy()


def test_patterns():
    """Test the patterns against known commit messages"""
    patterns = TestCommitPatterns()
    
    # Test cases based on actual commit messages from the framework
    test_cases = [
        # Should match
        ("Test commit - 2025-06-23T12:34:56.789123", True),
        ("Test main branch commit - 1719123456", True), 
        ("Test feature branch commit - 1719123456", True),
        ("Test multi-branch main commit - 1719123456", True),
        ("Test multi-branch feature commit - 1719123456", True),
        ("Test framework commit - 1719123456", True),
        ("Test some-other commit pattern", True),
        
        # Should NOT match
        ("Regular commit message", False),
        ("feat: add new feature", False),
        ("fix: bug in component", False),
        ("docs: update readme", False),
        ("Initial commit", False),
        ("Merge pull request #123", False),
    ]
    
    print("🧪 Testing Commit Pattern Recognition:")
    print("=" * 50)
    
    all_passed = True
    for commit_msg, expected in test_cases:
        actual = patterns.is_test_commit(commit_msg)
        status = "✅" if actual == expected else "❌"
        print(f"{status} '{commit_msg}' -> {actual} (expected {expected})")
        
        if actual != expected:
            all_passed = False
    
    print(f"\n📊 Test Results: {'All tests passed' if all_passed else 'Some tests failed'}")
    return all_passed


if __name__ == "__main__":
    test_patterns()