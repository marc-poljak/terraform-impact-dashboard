#!/usr/bin/env python3
"""
Test runner for comprehensive TFE integration test suite

This script runs all TFE-related tests including unit tests, integration tests,
and security tests to verify the complete TFE functionality.
"""

import subprocess
import sys
import os
from pathlib import Path


def run_test_suite(test_path, description):
    """Run a test suite and return results"""
    print(f"\n{'='*60}")
    print(f"Running {description}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run([
            sys.executable, '-m', 'pytest', 
            test_path, 
            '-v', 
            '--tb=short',
            '--disable-warnings'
        ], capture_output=True, text=True, cwd=Path(__file__).parent.parent)
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        return result.returncode == 0
    except Exception as e:
        print(f"Error running tests: {e}")
        return False


def main():
    """Run comprehensive TFE test suite"""
    print("🧪 TFE Integration Comprehensive Test Suite")
    print("=" * 60)
    
    # Test suites to run
    test_suites = [
        # Unit Tests
        ("tests/unit/test_tfe_client.py", "TFE Client Unit Tests"),
        ("tests/unit/test_credential_manager.py", "Credential Manager Unit Tests"),
        ("tests/unit/test_tfe_input_component.py", "TFE Input Component Unit Tests"),
        ("tests/unit/test_tfe_error_handler.py", "TFE Error Handler Unit Tests"),
        ("tests/unit/test_tfe_security_comprehensive.py", "TFE Security Unit Tests"),
        
        # Integration Tests
        ("tests/integration/test_tfe_upload_integration.py", "TFE Upload Integration Tests"),
        ("tests/integration/test_tfe_complete_workflow.py", "TFE Complete Workflow Tests"),
        ("tests/integration/test_security_integration.py", "Security Integration Tests"),
    ]
    
    # Track results
    results = {}
    total_suites = len(test_suites)
    passed_suites = 0
    
    # Run each test suite
    for test_path, description in test_suites:
        success = run_test_suite(test_path, description)
        results[description] = success
        if success:
            passed_suites += 1
    
    # Print summary
    print(f"\n{'='*60}")
    print("📊 TEST SUITE SUMMARY")
    print(f"{'='*60}")
    
    for description, success in results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status} - {description}")
    
    print(f"\n📈 Overall Results: {passed_suites}/{total_suites} test suites passed")
    
    if passed_suites == total_suites:
        print("🎉 All TFE integration tests passed!")
        return 0
    else:
        print("⚠️  Some test suites failed. Please review the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())