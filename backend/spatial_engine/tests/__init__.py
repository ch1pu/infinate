"""
tests - Integration test suite for spatial_engine.

Contains integration tests and benchmarks that verify SpatialTransformer
and VectorStore systems work together end-to-end, maintaining O(k) complexity.

Author: ch1pu
Milestone: 1.7 - Integration Testing

Test Modules:
    test_integration_core: Core integration tests (17 tests)
    test_integration_benchmarks: Performance benchmarks (6 tests)

Usage:
    ```bash
    # Run all integration tests
    poetry run pytest spatial_engine/tests/ -v

    # Run benchmarks only
    poetry run pytest spatial_engine/tests/ -v -m benchmark

    # Run with coverage
    poetry run pytest spatial_engine/tests/ -v --cov=spatial_engine/integration
    ```
"""
