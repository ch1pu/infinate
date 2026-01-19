#!/usr/bin/env python3
"""Run full INFINITE test suite with coverage report.

Milestone 1.9 - Test Stabilization & Full Coverage Documentation

This script runs the complete test suite and generates:
- Coverage report (HTML and terminal)
- Test results log file with timestamp
- Summary statistics

Usage:
    poetry run python scripts/run_full_test_suite.py
    poetry run python scripts/run_full_test_suite.py --quick  # Skip slow tests
    poetry run python scripts/run_full_test_suite.py --m19    # Run M1.9 tests only

Author: ch1pu
"""

import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def main() -> int:
    """Run the full test suite with coverage.

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    parser = argparse.ArgumentParser(
        description="Run INFINITE test suite with coverage"
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Skip slow and benchmark tests",
    )
    parser.add_argument(
        "--m19",
        action="store_true",
        help="Run M1.9 stability tests only",
    )
    parser.add_argument(
        "--no-coverage",
        action="store_true",
        help="Skip coverage reporting",
    )
    args = parser.parse_args()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Ensure test_results directory exists
    results_dir = Path("test_results")
    results_dir.mkdir(exist_ok=True)

    # Determine output file name
    if args.m19:
        output_file = results_dir / f"m19_tests_{timestamp}.txt"
    elif args.quick:
        output_file = results_dir / f"quick_suite_{timestamp}.txt"
    else:
        output_file = results_dir / f"full_suite_{timestamp}.txt"

    # Build pytest command
    cmd = ["poetry", "run", "pytest", "-v"]

    # Add coverage if requested
    if not args.no_coverage:
        cmd.extend([
            "--cov=spatial_engine",
            "--cov-report=html",
            "--cov-report=term-missing",
            "--cov-fail-under=90",
        ])

    # Add marker filters
    if args.m19:
        cmd.extend(["-m", "m19"])
    elif args.quick:
        cmd.extend(["-m", "not slow and not benchmark"])

    print("=" * 60)
    print("INFINITE Full Test Suite")
    print("=" * 60)
    print(f"Timestamp: {timestamp}")
    print(f"Output:    {output_file}")
    print(f"Mode:      {'M1.9 only' if args.m19 else 'Quick' if args.quick else 'Full'}")
    print(f"Coverage:  {'No' if args.no_coverage else 'Yes'}")
    print(f"Command:   {' '.join(cmd)}")
    print("=" * 60)
    print()

    # Run tests and capture output
    with open(output_file, "w") as f:
        f.write(f"INFINITE Test Suite - {timestamp}\n")
        f.write(f"Mode: {'M1.9 only' if args.m19 else 'Quick' if args.quick else 'Full'}\n")
        f.write("=" * 60 + "\n\n")

        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        f.write(result.stdout)

    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    # Extract key lines from output
    for line in result.stdout.split("\n"):
        line_lower = line.lower()
        if any(
            kw in line_lower
            for kw in ["passed", "failed", "skipped", "error", "total", "coverage"]
        ):
            print(line)

    print("=" * 60)
    print(f"Full results: {output_file}")
    if not args.no_coverage:
        print("Coverage HTML: htmlcov/index.html")
    print("=" * 60)

    # Return appropriate exit code
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
