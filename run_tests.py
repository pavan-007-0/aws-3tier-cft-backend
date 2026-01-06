#!/usr/bin/env python3
"""
Test runner for backend tests with coverage reporting
"""
import unittest
import sys
import os
from io import StringIO

def run_tests_with_coverage():
    """Run tests with coverage reporting"""
    try:
        import coverage
        
        # Initialize coverage
        cov = coverage.Coverage()
        cov.start()
        
        # Discover and run tests
        loader = unittest.TestLoader()
        start_dir = '.'
        suite = loader.discover(start_dir, pattern='test_*.py')
        
        # Run tests
        stream = StringIO()
        runner = unittest.TextTestRunner(stream=stream, verbosity=2)
        result = runner.run(suite)
        
        # Stop coverage
        cov.stop()
        cov.save()
        
        # Print test results
        print("=" * 70)
        print("TEST RESULTS")
        print("=" * 70)
        print(stream.getvalue())
        
        # Print coverage report
        print("=" * 70)
        print("COVERAGE REPORT")
        print("=" * 70)
        cov.report(show_missing=True)
        
        # Generate HTML coverage report
        try:
            cov.html_report(directory='htmlcov')
            print(f"\nHTML coverage report generated in 'htmlcov' directory")
        except Exception as e:
            print(f"Could not generate HTML report: {e}")
        
        # Return exit code based on test results
        return 0 if result.wasSuccessful() else 1
        
    except ImportError:
        print("Coverage package not installed. Running tests without coverage...")
        return run_tests_without_coverage()

def run_tests_without_coverage():
    """Run tests without coverage reporting"""
    loader = unittest.TestLoader()
    start_dir = '.'
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return 0 if result.wasSuccessful() else 1

def install_coverage():
    """Install coverage package if not available"""
    try:
        import subprocess
        print("Installing coverage package...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'coverage'])
        print("Coverage package installed successfully!")
        return True
    except subprocess.CalledProcessError:
        print("Failed to install coverage package")
        return False

def main():
    """Main test runner function"""
    print("🧪 Running Backend Tests")
    print("=" * 70)
    
    # Check if we're in a virtual environment
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("⚠️  Warning: Not running in a virtual environment")
        print("   Consider activating your virtual environment first")
        print()
    
    # Try to install coverage if not available
    try:
        import coverage
    except ImportError:
        print("Coverage package not found. Attempting to install...")
        if not install_coverage():
            print("Continuing without coverage...")
    
    # Set environment variables for testing
    os.environ['FLASK_ENV'] = 'testing'
    os.environ['JWT_SECRET_KEY'] = 'test-secret-key'
    os.environ['SECRET_KEY'] = 'test-secret'
    
    # Run tests
    exit_code = run_tests_with_coverage()
    
    if exit_code == 0:
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Some tests failed!")
    
    return exit_code

if __name__ == '__main__':
    sys.exit(main())