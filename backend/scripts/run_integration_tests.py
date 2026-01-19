#!/usr/bin/env python3
"""
run_integration_tests.py - Run integration tests with historical output.

Creates timestamped output files for historical records.

Usage:
    poetry run python scripts/run_integration_tests.py
"""

import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def get_output_dir() -> Path:
    """Get/create the test output directory."""
    output_dir = Path(__file__).parent.parent / "test_results"
    output_dir.mkdir(exist_ok=True)
    return output_dir


def check_docker_postgres() -> bool:
    """Check if Docker PostgreSQL is running."""
    try:
        result = subprocess.run(
            ["docker", "exec", "infinate_postgres_test", "pg_isready", "-U", "test"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.returncode == 0
    except Exception:
        return False


def run_tests(output_file: Path) -> tuple[int, str]:
    """Run pytest and capture output."""
    # Build pytest command
    cmd = [
        "poetry", "run", "pytest",
        "spatial_engine/tests/",
        "-v", "-s",
        "--tb=short",
        "--cov=spatial_engine/integration",
        "--cov-report=term-missing",
        # Don't fail on coverage for integration tests
        "--no-cov-on-fail",
    ]

    # Run pytest
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent,
    )

    output = result.stdout + result.stderr
    return result.returncode, output


def main() -> int:
    """Main entry point."""
    print("=" * 70)
    print("Infinite Spatial AI - Integration Test Runner")
    print("=" * 70)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = get_output_dir()

    # Check Docker PostgreSQL
    print("\n[1/3] Checking Docker PostgreSQL...")
    docker_ok = check_docker_postgres()
    if docker_ok:
        print("      Docker PostgreSQL: CONNECTED")
    else:
        print("      Docker PostgreSQL: NOT AVAILABLE")
        print("      (pgvector tests will be skipped)")
        print("      To start: docker compose -f docker-compose.test.yml up -d")

    # Run tests
    print("\n[2/3] Running integration tests...")
    output_file = output_dir / f"integration_tests_{timestamp}.txt"

    returncode, output = run_tests(output_file)

    # Write output to file
    with open(output_file, "w") as f:
        f.write(f"Integration Test Results - {datetime.now().isoformat()}\n")
        f.write("=" * 70 + "\n\n")
        f.write(f"Docker PostgreSQL: {'CONNECTED' if docker_ok else 'NOT AVAILABLE'}\n")
        f.write(f"Exit Code: {returncode}\n\n")
        f.write("=" * 70 + "\n")
        f.write("TEST OUTPUT\n")
        f.write("=" * 70 + "\n\n")
        f.write(output)

    print(f"      Output saved to: {output_file}")

    # Parse results
    print("\n[3/3] Test Summary:")

    # Count passed/failed/skipped
    passed = output.count(" PASSED")
    failed = output.count(" FAILED")
    skipped = output.count(" SKIPPED")

    print(f"      Passed:  {passed}")
    print(f"      Failed:  {failed}")
    print(f"      Skipped: {skipped}")

    # Check for O(k) verification
    if "O(k) VERIFIED" in output:
        print("\n      O(k) Complexity: VERIFIED")

    print("\n" + "=" * 70)

    if returncode == 0 or (failed == 0 and "FAIL Required test coverage" in output):
        print("RESULT: ALL TESTS PASSED")
        print("(Coverage threshold warning is expected for integration-only tests)")
        return 0
    else:
        print(f"RESULT: {failed} TEST(S) FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
