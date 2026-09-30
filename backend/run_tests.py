"""
Quick test runner script with detailed output.
"""

import sys
import subprocess

def run_tests():
    """Run pytest with recommended options."""
    print("=" * 70)
    print("TulaPramaan - Running Test Suite")
    print("=" * 70)
    print()
    
    # Run pytest
    result = subprocess.run([
        sys.executable, "-m", "pytest",
        "tests/",
        "-v",                      # Verbose
        "--tb=short",              # Short traceback format
        "--color=yes",             # Colored output
        "-ra",                     # Show summary of all test outcomes
        "--cov=services",          # Coverage for services
        "--cov=models",            # Coverage for models
        "--cov-report=term",       # Terminal coverage report
        "--cov-report=html",       # HTML coverage report
    ])
    
    print()
    print("=" * 70)
    if result.returncode == 0:
        print("✓ All tests passed!")
    else:
        print("✗ Some tests failed")
    print("=" * 70)
    print()
    print("Coverage report generated in: htmlcov/index.html")
    
    return result.returncode

if __name__ == "__main__":
    sys.exit(run_tests())
