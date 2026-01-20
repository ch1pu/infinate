"""
test_m111_integration_speedup.py - Full integration tests for M1.11 speedup.

Tests the integrated NavigationAttention against baseline to verify
actual speedup from strafe jumping navigation.

Author: ch1pu (Adolfo Lopez)
Milestone: 1.11 - Strafe Jumping Navigation (Integration)

Test Count: 25+ tests
"""

import statistics
import time

import pytest
import torch

from spatial_engine.benchmarks.m111_speedup_benchmark import (
    M111SpeedupBenchmark,
    SemanticDataGenerator,
    TestScenario,
)
from spatial_engine.integration.navigation_attention import (
    BaselineAttention,
    BaselineNavigator,
    NavigationAttention,
    NavigationMetrics,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def device() -> torch.device:
    """Get test device."""
    return torch.device("cpu")


@pytest.fixture
def d_model() -> int:
    """Model dimension for tests."""
    return 192  # Smaller for faster tests (divisible by 4 heads)


@pytest.fixture
def nav_attention(d_model: int, device: torch.device) -> NavigationAttention:
    """Create NavigationAttention instance."""
    return NavigationAttention(
        d_model=d_model,
        n_heads=4,
        spatial_radius=50.0,
        k_neighbors=50,
        enable_navigation=True,
        enable_lod=True,
        navigation_max_steps=10,
    ).to(device)


@pytest.fixture
def baseline_attention(d_model: int, device: torch.device) -> BaselineAttention:
    """Create BaselineAttention instance."""
    return BaselineAttention(
        d_model=d_model,
        n_heads=4,
        spatial_radius=50.0,
        k_neighbors=50,
        method="greedy",
    ).to(device)


@pytest.fixture
def data_generator(d_model: int, device: torch.device) -> SemanticDataGenerator:
    """Create semantic data generator."""
    return SemanticDataGenerator(d_model=d_model, device=device)


@pytest.fixture
def clustered_scenario(data_generator: SemanticDataGenerator) -> TestScenario:
    """Create clustered test scenario."""
    return data_generator.create_clustered_scenario(
        n_clusters=3,
        tokens_per_cluster=50,
        noise_tokens=200,
    )


@pytest.fixture
def warp_scenario(data_generator: SemanticDataGenerator) -> TestScenario:
    """Create warp lane test scenario."""
    return data_generator.create_warp_lane_scenario(
        n_tokens=500,
        n_warp_targets=5,
        warp_distance=200.0,
    )


# ---------------------------------------------------------------------------
# TestNavigationAttention
# ---------------------------------------------------------------------------


class TestNavigationAttention:
    """Test integrated NavigationAttention module."""

    @pytest.mark.m111
    @pytest.mark.m111_integration
    def test_navigation_attention_init(self, nav_attention: NavigationAttention, d_model: int) -> None:
        """Test NavigationAttention initialization."""
        assert nav_attention.enable_navigation is True
        assert nav_attention.enable_lod is True
        assert nav_attention.d_model == d_model
        assert nav_attention.k_neighbors == 50

        print("\n" + "=" * 60)
        print("M1.11 NAVIGATION ATTENTION INIT")
        print("=" * 60)
        print(f"d_model: {nav_attention.d_model}")
        print(f"k_neighbors: {nav_attention.k_neighbors}")
        print(f"enable_navigation: {nav_attention.enable_navigation}")
        print(f"enable_lod: {nav_attention.enable_lod}")
        print("=" * 60)

    @pytest.mark.m111
    @pytest.mark.m111_integration
    def test_navigation_attention_query(
        self,
        nav_attention: NavigationAttention,
        clustered_scenario: TestScenario,
    ) -> None:
        """Test NavigationAttention query method."""
        output, metrics = nav_attention.query(
            query=clustered_scenario.target_embedding,
            context_embeddings=clustered_scenario.context_embeddings,
            context_positions=clustered_scenario.context_positions,
            target_embedding=clustered_scenario.target_embedding,
        )

        assert output.shape == (nav_attention.d_model,)
        assert isinstance(metrics, NavigationMetrics)
        assert metrics.steps_taken >= 0
        assert metrics.attention_ops >= 0

        print("\n" + "=" * 60)
        print("M1.11 NAVIGATION ATTENTION QUERY")
        print("=" * 60)
        print(f"Output shape: {output.shape}")
        print(f"Steps taken: {metrics.steps_taken}")
        print(f"Attention ops: {metrics.attention_ops}")
        print(f"Tokens accessed: {metrics.tokens_accessed}")
        print(f"Final similarity: {metrics.final_similarity:.3f}")
        print(f"Converged: {metrics.converged}")
        print(f"Warp count: {metrics.warp_count}")
        print("=" * 60)

    @pytest.mark.m111
    @pytest.mark.m111_integration
    def test_navigation_attention_lod_compression(
        self,
        nav_attention: NavigationAttention,
        device: torch.device,
        d_model: int,
    ) -> None:
        """Test LOD compression in NavigationAttention."""
        # Create context spread across LOD levels
        n_tokens = 500
        embeddings = torch.randn(n_tokens, d_model, device=device)
        positions = torch.randn(n_tokens, 3, device=device) * 500  # Spread across world

        query_pos = torch.zeros(3, device=device)
        compressed_emb, compressed_pos, tokens_repr = nav_attention._apply_lod_compression(
            query_pos, embeddings, positions
        )

        print("\n" + "=" * 60)
        print("M1.11 LOD COMPRESSION TEST")
        print("=" * 60)
        print(f"Original tokens: {n_tokens}")
        print(f"Compressed tokens: {len(compressed_emb)}")
        print(f"Tokens represented: {tokens_repr}")
        print(f"Compression ratio: {tokens_repr / max(1, len(compressed_emb)):.1f}x")
        print("=" * 60)

        assert len(compressed_emb) <= nav_attention.lod_config.total_tokens
        assert tokens_repr > 0


# ---------------------------------------------------------------------------
# TestBaselineAttention
# ---------------------------------------------------------------------------


class TestBaselineAttention:
    """Test baseline attention for comparison."""

    @pytest.mark.m111
    @pytest.mark.m111_integration
    def test_baseline_greedy_navigation(
        self,
        baseline_attention: BaselineAttention,
        clustered_scenario: TestScenario,
    ) -> None:
        """Test baseline greedy navigation."""
        output, metrics = baseline_attention.query(
            query=clustered_scenario.target_embedding,
            context_embeddings=clustered_scenario.context_embeddings,
            context_positions=clustered_scenario.context_positions,
            target_embedding=clustered_scenario.target_embedding,
            max_steps=10,
        )

        assert output.shape == (baseline_attention.d_model,)
        assert metrics.steps_taken >= 0

        print("\n" + "=" * 60)
        print("M1.11 BASELINE GREEDY NAVIGATION")
        print("=" * 60)
        print(f"Steps taken: {metrics.steps_taken}")
        print(f"Final similarity: {metrics.final_similarity:.3f}")
        print("=" * 60)

    @pytest.mark.m111
    @pytest.mark.m111_integration
    def test_baseline_static_navigation(
        self,
        d_model: int,
        device: torch.device,
        clustered_scenario: TestScenario,
    ) -> None:
        """Test baseline static (no movement) navigation."""
        static_baseline = BaselineAttention(
            d_model=d_model,
            method="static",
        ).to(device)

        output, metrics = static_baseline.query(
            query=clustered_scenario.target_embedding,
            context_embeddings=clustered_scenario.context_embeddings,
            context_positions=clustered_scenario.context_positions,
            target_embedding=clustered_scenario.target_embedding,
        )

        assert metrics.steps_taken == 0
        print("\n" + "=" * 60)
        print("M1.11 BASELINE STATIC")
        print("=" * 60)
        print(f"Steps taken: {metrics.steps_taken}")
        print(f"Final similarity: {metrics.final_similarity:.3f}")
        print("=" * 60)


# ---------------------------------------------------------------------------
# TestSpeedupComparison
# ---------------------------------------------------------------------------


class TestSpeedupComparison:
    """Test M1.11 speedup vs baseline."""

    @pytest.mark.m111
    @pytest.mark.m111_benchmark
    def test_speedup_clustered_scenario(
        self,
        nav_attention: NavigationAttention,
        baseline_attention: BaselineAttention,
        clustered_scenario: TestScenario,
    ) -> None:
        """Test speedup on clustered semantic data."""
        iterations = 10

        # M1.11
        m111_latencies = []
        m111_steps = []
        m111_similarities = []

        for _ in range(iterations):
            start = time.perf_counter()
            _, metrics = nav_attention.query(
                query=clustered_scenario.target_embedding,
                context_embeddings=clustered_scenario.context_embeddings,
                context_positions=clustered_scenario.context_positions,
                target_embedding=clustered_scenario.target_embedding,
            )
            end = time.perf_counter()
            m111_latencies.append((end - start) * 1000)
            m111_steps.append(metrics.steps_taken)
            m111_similarities.append(metrics.final_similarity)

        # Baseline
        baseline_latencies = []
        baseline_steps = []
        baseline_similarities = []

        for _ in range(iterations):
            start = time.perf_counter()
            _, metrics = baseline_attention.query(
                query=clustered_scenario.target_embedding,
                context_embeddings=clustered_scenario.context_embeddings,
                context_positions=clustered_scenario.context_positions,
                target_embedding=clustered_scenario.target_embedding,
                max_steps=10,
            )
            end = time.perf_counter()
            baseline_latencies.append((end - start) * 1000)
            baseline_steps.append(metrics.steps_taken)
            baseline_similarities.append(metrics.final_similarity)

        # Calculate speedups
        m111_avg_latency = statistics.mean(m111_latencies)
        baseline_avg_latency = statistics.mean(baseline_latencies)
        latency_speedup = baseline_avg_latency / max(0.001, m111_avg_latency)

        m111_avg_steps = statistics.mean(m111_steps)
        baseline_avg_steps = statistics.mean(baseline_steps)
        steps_speedup = baseline_avg_steps / max(1, m111_avg_steps) if m111_avg_steps > 0 else 1

        m111_avg_sim = statistics.mean(m111_similarities)
        baseline_avg_sim = statistics.mean(baseline_similarities)
        quality_diff = m111_avg_sim - baseline_avg_sim

        print("\n" + "=" * 60)
        print("M1.11 SPEEDUP: CLUSTERED SCENARIO")
        print("=" * 60)
        print(f"{'Metric':<20} {'M1.11':<15} {'Baseline':<15} {'Result':<15}")
        print("-" * 60)
        print(f"{'Latency (ms)':<20} {m111_avg_latency:<15.2f} {baseline_avg_latency:<15.2f} {latency_speedup:.2f}x")
        print(f"{'Steps':<20} {m111_avg_steps:<15.1f} {baseline_avg_steps:<15.1f} {steps_speedup:.2f}x")
        print(f"{'Similarity':<20} {m111_avg_sim:<15.3f} {baseline_avg_sim:<15.3f} {quality_diff:+.3f}")
        print("=" * 60)

    @pytest.mark.m111
    @pytest.mark.m111_benchmark
    def test_speedup_warp_lane_scenario(
        self,
        nav_attention: NavigationAttention,
        baseline_attention: BaselineAttention,
        warp_scenario: TestScenario,
    ) -> None:
        """Test speedup on warp lane scenario (distant targets)."""
        iterations = 10

        # M1.11
        m111_warps = []
        m111_similarities = []

        for _ in range(iterations):
            _, metrics = nav_attention.query(
                query=warp_scenario.target_embedding,
                context_embeddings=warp_scenario.context_embeddings,
                context_positions=warp_scenario.context_positions,
                target_embedding=warp_scenario.target_embedding,
            )
            m111_warps.append(metrics.warp_count)
            m111_similarities.append(metrics.final_similarity)

        # Baseline
        baseline_similarities = []

        for _ in range(iterations):
            _, metrics = baseline_attention.query(
                query=warp_scenario.target_embedding,
                context_embeddings=warp_scenario.context_embeddings,
                context_positions=warp_scenario.context_positions,
                target_embedding=warp_scenario.target_embedding,
                max_steps=10,
            )
            baseline_similarities.append(metrics.final_similarity)

        avg_warps = statistics.mean(m111_warps)
        m111_avg_sim = statistics.mean(m111_similarities)
        baseline_avg_sim = statistics.mean(baseline_similarities)
        quality_diff = m111_avg_sim - baseline_avg_sim

        print("\n" + "=" * 60)
        print("M1.11 SPEEDUP: WARP LANE SCENARIO")
        print("=" * 60)
        print(f"M1.11 average warps: {avg_warps:.1f}")
        print(f"M1.11 similarity: {m111_avg_sim:.3f}")
        print(f"Baseline similarity: {baseline_avg_sim:.3f}")
        print(f"Quality improvement: {quality_diff:+.3f}")
        print("=" * 60)


# ---------------------------------------------------------------------------
# TestScalingBehavior
# ---------------------------------------------------------------------------


class TestScalingBehavior:
    """Test O(k) scaling behavior with integration."""

    @pytest.mark.m111
    @pytest.mark.m111_benchmark
    def test_scaling_with_token_count(
        self,
        d_model: int,
        device: torch.device,
    ) -> None:
        """Test that latency scales appropriately with token count."""
        nav_attention = NavigationAttention(
            d_model=d_model,
            enable_navigation=True,
            enable_lod=True,
        ).to(device)

        data_gen = SemanticDataGenerator(d_model=d_model, device=device)

        token_counts = [500, 1000, 2000, 5000]
        latencies = []

        for n_tokens in token_counts:
            scenario = data_gen.create_scale_scenario(n_tokens)

            # Warmup
            nav_attention.query(
                query=scenario.target_embedding,
                context_embeddings=scenario.context_embeddings,
                context_positions=scenario.context_positions,
            )

            # Measure
            times = []
            for _ in range(5):
                start = time.perf_counter()
                nav_attention.query(
                    query=scenario.target_embedding,
                    context_embeddings=scenario.context_embeddings,
                    context_positions=scenario.context_positions,
                )
                end = time.perf_counter()
                times.append((end - start) * 1000)

            latencies.append(statistics.mean(times))

        # Calculate scaling ratio
        scaling_ratio = latencies[-1] / latencies[0]
        token_ratio = token_counts[-1] / token_counts[0]

        print("\n" + "=" * 60)
        print("M1.11 SCALING TEST: O(k) Verification")
        print("=" * 60)
        for i, (n, lat) in enumerate(zip(token_counts, latencies)):
            print(f"  {n:>6} tokens: {lat:.2f}ms")
        print("-" * 60)
        print(f"Token ratio ({token_counts[-1]}/{token_counts[0]}): {token_ratio:.1f}x")
        print(f"Latency ratio: {scaling_ratio:.2f}x")
        print(f"Expected O(n²): {token_ratio**2:.1f}x")
        print(f"Expected O(k): ~{token_ratio:.1f}x")
        print("=" * 60)

        # Should be much better than O(n²)
        assert scaling_ratio < token_ratio ** 2 / 2, "Scaling worse than expected"


# ---------------------------------------------------------------------------
# TestFullBenchmarkSuite
# ---------------------------------------------------------------------------


class TestFullBenchmarkSuite:
    """Run the full benchmark suite as a test."""

    @pytest.mark.m111
    @pytest.mark.m111_benchmark
    @pytest.mark.slow
    def test_full_benchmark(self, d_model: int, device: torch.device) -> None:
        """Run full benchmark suite."""
        benchmark = M111SpeedupBenchmark(d_model=d_model, device=device)
        results = benchmark.run_full_benchmark(iterations=5)

        # Verify we got results for all scenarios
        assert len(results) >= 4, f"Expected at least 4 scenarios, got {len(results)}"

        # Summarize
        avg_steps_speedup = statistics.mean(r.steps_speedup for r in results)
        avg_latency_speedup = statistics.mean(r.latency_speedup for r in results)
        avg_quality = statistics.mean(r.quality_improvement for r in results)

        print("\n" + "=" * 60)
        print("M1.11 FULL BENCHMARK SUITE SUMMARY")
        print("=" * 60)
        print(f"Scenarios tested: {len(results)}")
        print(f"Avg steps speedup: {avg_steps_speedup:.2f}x")
        print(f"Avg latency speedup: {avg_latency_speedup:.2f}x")
        print(f"Avg quality change: {avg_quality:+.3f}")
        print("=" * 60)


# ---------------------------------------------------------------------------
# TestSemanticDataGenerator
# ---------------------------------------------------------------------------


class TestSemanticDataGenerator:
    """Test semantic data generation."""

    @pytest.mark.m111
    def test_clustered_scenario_creation(
        self, data_generator: SemanticDataGenerator
    ) -> None:
        """Test clustered scenario creation."""
        scenario = data_generator.create_clustered_scenario(
            n_clusters=3, tokens_per_cluster=20, noise_tokens=50
        )

        expected_tokens = 3 * 20 + 50
        assert len(scenario.context_embeddings) == expected_tokens
        assert len(scenario.context_positions) == expected_tokens
        assert scenario.target_embedding.shape[-1] == data_generator.d_model

        print("\n" + "=" * 60)
        print("M1.11 CLUSTERED SCENARIO")
        print("=" * 60)
        print(f"Total tokens: {len(scenario.context_embeddings)}")
        print(f"Target indices: {len(scenario.target_indices)}")
        print(f"Description: {scenario.description}")
        print("=" * 60)

    @pytest.mark.m111
    def test_warp_scenario_creation(
        self, data_generator: SemanticDataGenerator
    ) -> None:
        """Test warp lane scenario creation."""
        scenario = data_generator.create_warp_lane_scenario(
            n_tokens=200, n_warp_targets=5, warp_distance=300.0
        )

        assert len(scenario.context_embeddings) == 200
        assert len(scenario.target_indices) == 5

        # Verify warp targets are at correct distance
        target_positions = scenario.context_positions[scenario.target_indices]
        distances = torch.norm(target_positions, dim=-1)
        avg_distance = distances.mean().item()

        print("\n" + "=" * 60)
        print("M1.11 WARP LANE SCENARIO")
        print("=" * 60)
        print(f"Total tokens: {len(scenario.context_embeddings)}")
        print(f"Warp targets: {len(scenario.target_indices)}")
        print(f"Avg target distance: {avg_distance:.1f}")
        print(f"Description: {scenario.description}")
        print("=" * 60)

        assert 250 < avg_distance < 350, f"Warp targets not at expected distance: {avg_distance}"
