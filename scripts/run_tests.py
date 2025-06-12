"""
Run tests for the Spendlot Receipt Tracker backend.
"""
import subprocess
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run_tests():
    """Run all tests."""
    print("Running tests for Spendlot Receipt Tracker...")
    
    # Run pytest with coverage
    cmd = [
        "python", "-m", "pytest",
        "tests/",
        "-v",
        "--cov=app",
        "--cov-report=html",
        "--cov-report=term-missing",
        "--cov-fail-under=80"
    ]
    
    try:
        result = subprocess.run(cmd, check=True)
        print("All tests passed!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Tests failed with exit code {e.returncode}")
        return False


def run_linting():
    """Run code linting."""
    print("Running code linting...")
    
    # Run flake8
    try:
        subprocess.run(["flake8", "app/", "tests/"], check=True)
        print("Linting passed!")
        return True
    except subprocess.CalledProcessError:
        print("Linting failed!")
        return False


def run_type_checking():
    """Run type checking with mypy."""
    print("Running type checking...")
    
    try:
        subprocess.run(["mypy", "app/"], check=True)
        print("Type checking passed!")
        return True
    except subprocess.CalledProcessError:
        print("Type checking failed!")
        return False


def main():
    """Main function."""
    success = True
    
    # Run linting
    if not run_linting():
        success = False
    
    # Run type checking
    if not run_type_checking():
        success = False
    
    # Run tests
    if not run_tests():
        success = False
    
    if success:
        print("\n✅ All checks passed!")
        sys.exit(0)
    else:
        print("\n❌ Some checks failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
