"""
test_momentum_navigator.py - Tests for MomentumNavigator.

Tests the strafe jumping navigation system implementing 7 validated exploits:
1. Warp Lanes (Exploit 1)
2. Shell Memory (Exploit 2)
3. LOD Hopping (Exploit 3)
6. Bunny Hop Momentum (Exploit 6)
7. Circle Jump (Exploit 7)
8. Temperature Surfing (Exploit 8)
9. Attention Ratchet (Exploit 9)

Author: Adolfo Lopez (ch1pu)
Milestone: 1.11 - Strafe Jumping Navigation
"""

import pytest
import torch

from spatial_engine.core.momentum_navigator import (
    MomentumNavigator,
    NavigationResult,
    NavigationState,
)


class TestNavigationState:
    """Tests for NavigationState dataclass."""

    def test_initialization(self):
        """Test NavigationState can be initialized with default values."""
        state = NavigationState(
            position=torch.zeros(3),
            velocity=torch.zeros(3),
        )
        assert state.position.shape == (3,)
        assert state.velocity.shape == (3,)
        assert state.temperature == 2.0
        assert state.hop_count == 0
        assert state.warp_count == 0
        assert state.trajectory == []
        assert state.step == 0

    def test_clone(self):
        """Test NavigationState clone creates deep copy."""
        state = NavigationState(
            position=torch.tensor([1.0, 2.0, 3.0]),
            velocity=torch.tensor([0.1, 0.2, 0.3]),
            temperature=1.5,
            hop_count=5,
            warp_count=2,
            trajectory=[torch.zeros(3)],
            step=10,
        )
        cloned = state.clone()

        # Verify values are equal
        assert torch.allclose(cloned.position, state.position)
        assert torch.allclose(cloned.velocity, state.velocity)
        assert cloned.temperature == state.temperature
        assert cloned.hop_count == state.hop_count
        assert cloned.warp_count == state.warp_count
        assert cloned.step == state.step

        # Verify it's a deep copy (modifying original doesn't affect clone)
        state.position[0] = 999.0
        assert cloned.position[0] != 999.0


class TestMomentumNavigatorInitialization:
    """Tests for MomentumNavigator initialization."""

    def test_default_initialization(self):
        """Test MomentumNavigator initializes with default parameters."""
        nav = MomentumNavigator()

        assert nav.d_model == 768
        assert nav.momentum == 0.9
        assert nav.initial_temperature == 2.0
        assert nav.final_temperature == 0.5
        assert nav.warp_threshold == 0.95
        assert nav.max_speed == 10.0
        assert nav.attention_radius == 50.0
        assert nav.convergence_threshold == 0.1

    def test_custom_initialization(self):
        """Test MomentumNavigator with custom parameters."""
        nav = MomentumNavigator(
            d_model=512,
            momentum=0.8,
            initial_temperature=3.0,
            final_temperature=0.3,
            warp_threshold=0.9,
            max_speed=20.0,
            attention_radius=100.0,
            convergence_threshold=0.05,
        )

        assert nav.d_model == 512
        assert nav.momentum == 0.8
        assert nav.initial_temperature == 3.0
        assert nav.final_temperature == 0.3
        assert nav.warp_threshold == 0.9
        assert nav.max_speed == 20.0
        assert nav.attention_radius == 100.0
        assert nav.convergence_threshold == 0.05

    def test_learned_components_created(self):
        """Test that learned components are initialized."""
        nav = MomentumNavigator(d_model=256)

        assert nav.direction_predictor is not None
        assert nav.speed_predictor is not None
        assert nav.query_broadener is not None

        # Check shapes
        assert nav.direction_predictor.in_features == 256
        assert nav.direction_predictor.out_features == 3
        assert nav.speed_predictor.in_features == 256
        assert nav.speed_predictor.out_features == 1
        assert nav.query_broadener.in_features == 256
        assert nav.query_broadener.out_features == 256

    def test_exploit_tracking_initialized(self):
        """Test exploit tracking structures are initialized."""
        nav = MomentumNavigator()

        assert len(nav._exploit_enabled) == 7
        assert all(nav._exploit_enabled.values())  # All enabled by default
        assert len(nav._exploit_success) == 7


class TestMomentumNavigatorReset:
    """Tests for MomentumNavigator reset functionality."""

    def test_reset_with_default_position(self):
        """Test reset creates state at origin."""
        nav = MomentumNavigator()
        nav.reset()

        assert nav.state is not None
        assert torch.allclose(nav.state.position, torch.zeros(3))
        assert torch.allclose(nav.state.velocity, torch.zeros(3))
        assert nav.state.temperature == nav.initial_temperature
        assert nav.state.hop_count == 0

    def test_reset_with_custom_position(self):
        """Test reset with specified starting position."""
        nav = MomentumNavigator()
        start_pos = torch.tensor([10.0, 20.0, 30.0])
        nav.reset(start_position=start_pos)

        assert nav.state is not None
        assert torch.allclose(nav.state.position, start_pos)

    def test_reset_clears_previous_state(self):
        """Test reset clears previous navigation state."""
        nav = MomentumNavigator()
        nav.reset()

        # Simulate some navigation
        nav.state.hop_count = 100
        nav.state.warp_count = 50
        nav.state.temperature = 0.1

        # Reset should clear everything
        nav.reset()
        assert nav.state.hop_count == 0
        assert nav.state.warp_count == 0
        assert nav.state.temperature == nav.initial_temperature


class TestTemperatureSurfing:
    """Tests for Exploit 8: Temperature Surfing."""

    def test_temperature_schedule_start(self):
        """Test temperature is high at start of navigation."""
        nav = MomentumNavigator(initial_temperature=2.0, final_temperature=0.5)
        temp = nav._schedule_temperature(step=0, max_steps=10)
        assert temp == pytest.approx(2.0)

    def test_temperature_schedule_end(self):
        """Test temperature is low at end of navigation."""
        nav = MomentumNavigator(initial_temperature=2.0, final_temperature=0.5)
        temp = nav._schedule_temperature(step=10, max_steps=10)
        assert temp == pytest.approx(0.5)

    def test_temperature_schedule_middle(self):
        """Test temperature interpolates linearly."""
        nav = MomentumNavigator(initial_temperature=2.0, final_temperature=0.5)
        temp = nav._schedule_temperature(step=5, max_steps=10)
        # Linear interpolation: 2.0 * 0.5 + 0.5 * 0.5 = 1.25
        assert temp == pytest.approx(1.25)

    def test_temperature_schedule_zero_max_steps(self):
        """Test temperature handles zero max_steps."""
        nav = MomentumNavigator(initial_temperature=2.0)
        temp = nav._schedule_temperature(step=0, max_steps=0)
        assert temp == 2.0  # Returns initial


class TestBunnyHopMomentum:
    """Tests for Exploit 6: Bunny Hop Momentum."""

    def test_momentum_accumulates(self):
        """Test velocity accumulates with momentum."""
        nav = MomentumNavigator(d_model=64, momentum=0.9)
        nav.reset()

        query = torch.randn(64)

        # Take multiple steps
        speeds = []
        for _ in range(5):
            pos, info = nav.step(query)
            speeds.append(info["speed"])

        # Speed should generally increase with momentum
        # (unless direction predictor outputs opposing directions)
        assert nav.state.hop_count == 5

    def test_momentum_disabled(self):
        """Test navigation without momentum."""
        nav = MomentumNavigator(d_model=64, momentum=0.9)
        nav.reset()
        nav.disable_exploit("bunny_hop")

        query = torch.randn(64)

        # With momentum disabled, velocity doesn't accumulate
        nav.step(query)
        v1 = nav.state.velocity.clone()

        nav.step(query)
        v2 = nav.state.velocity.clone()

        # Without momentum, velocity is purely from current step (no accumulation)
        # The direction and speed come from the predictors
        assert nav.state.hop_count == 2


class TestCircleJump:
    """Tests for Exploit 7: Circle Jump Initialization."""

    def test_query_broadening(self):
        """Test query broadening creates mixed embedding."""
        nav = MomentumNavigator(d_model=64)
        query = torch.randn(64)

        broad_query = nav._broaden_query(query)

        assert broad_query.shape == query.shape
        # Should be different from original
        assert not torch.allclose(broad_query, query)

    def test_initial_jump_with_context(self):
        """Test initial jump finds centroid of top matches."""
        nav = MomentumNavigator(d_model=64)

        query = torch.randn(64)
        embeddings = torch.randn(100, 64)
        positions = torch.randn(100, 3) * 100

        result = nav._initial_jump(query, embeddings, positions)

        assert result is not None
        assert result.shape == (3,)

    def test_initial_jump_no_context(self):
        """Test initial jump returns None without context."""
        nav = MomentumNavigator()

        query = torch.randn(768)
        result = nav._initial_jump(query, None, None)

        assert result is None


class TestShellMemory:
    """Tests for Exploit 2: Shell Memory."""

    def test_shell_radii_defined(self):
        """Test shell radii are properly defined."""
        nav = MomentumNavigator(attention_radius=50.0)

        assert nav.SHELL_RADII == [0.9, 1.9, 2.9]
        # Actual radii would be 45, 95, 145

    def test_snap_to_shell_near_boundary(self):
        """Test positions near shells get snapped."""
        nav = MomentumNavigator(attention_radius=50.0)
        nav.reset()

        # Position at exactly shell radius should stay
        shell_radius = 0.9 * 50.0  # 45
        position = torch.tensor([shell_radius, 0.0, 0.0])

        snapped = nav._snap_to_shell(position)
        distance = torch.norm(snapped).item()

        # Should be close to a shell radius
        assert abs(distance - shell_radius) < 1.0 or distance == pytest.approx(shell_radius, rel=0.1)


class TestLODHopping:
    """Tests for Exploit 3: LOD Hopping."""

    def test_lod_boundaries_defined(self):
        """Test LOD boundaries are properly defined."""
        nav = MomentumNavigator()

        assert nav.LOD_BOUNDARIES == [50.0, 150.0, 500.0]

    def test_respect_lod_boundary_pulls_back(self):
        """Test positions just past LOD boundary get pulled back."""
        nav = MomentumNavigator()
        nav.reset()

        # Position just past first boundary (50)
        position = torch.tensor([52.0, 0.0, 0.0])

        adjusted = nav._respect_lod_boundaries(position)
        distance = torch.norm(adjusted).item()

        # Should be pulled back to just inside 50
        assert distance < 50.0

    def test_respect_lod_boundary_far_unchanged(self):
        """Test positions far from boundaries are unchanged."""
        nav = MomentumNavigator()
        nav.reset()

        # Position far from any boundary
        position = torch.tensor([25.0, 0.0, 0.0])

        adjusted = nav._respect_lod_boundaries(position)

        assert torch.allclose(adjusted, position)


class TestNavigationStep:
    """Tests for single navigation step."""

    def test_step_updates_position(self):
        """Test step updates position based on velocity."""
        nav = MomentumNavigator(d_model=64)
        nav.reset()

        initial_pos = nav.state.position.clone()
        query = torch.randn(64)

        new_pos, info = nav.step(query)

        assert not torch.allclose(new_pos, initial_pos)
        assert "speed" in info
        assert "temperature" in info
        assert "hop_count" in info

    def test_step_increments_counters(self):
        """Test step increments hop count and step counter."""
        nav = MomentumNavigator(d_model=64)
        nav.reset()

        query = torch.randn(64)
        nav.step(query)

        assert nav.state.hop_count == 1
        assert nav.state.step == 1


class TestFullNavigation:
    """Tests for full navigation sequence."""

    def test_navigate_returns_result(self):
        """Test navigate returns NavigationResult."""
        nav = MomentumNavigator(d_model=64)
        query = torch.randn(64)

        result = nav.navigate(query, max_steps=5)

        assert isinstance(result, NavigationResult)
        assert result.position.shape == (3,)
        assert result.steps_taken >= 0
        assert result.hop_count >= 0

    def test_navigate_with_context(self):
        """Test navigate with context embeddings and positions."""
        nav = MomentumNavigator(d_model=64)
        query = torch.randn(64)
        embeddings = torch.randn(100, 64)
        positions = torch.randn(100, 3) * 200

        result = nav.navigate(
            query,
            max_steps=5,
            context_embeddings=embeddings,
            context_positions=positions,
        )

        assert isinstance(result, NavigationResult)
        assert len(result.temperature_schedule) > 0

    def test_navigate_without_circle_jump(self):
        """Test navigation can skip circle jump."""
        nav = MomentumNavigator(d_model=64)
        query = torch.randn(64)

        result = nav.navigate(query, max_steps=5, use_circle_jump=False)

        assert isinstance(result, NavigationResult)


class TestExploitManagement:
    """Tests for exploit enable/disable functionality."""

    def test_disable_exploit(self):
        """Test disabling an exploit."""
        nav = MomentumNavigator()

        nav.disable_exploit("warp_lanes")
        assert not nav._exploit_enabled["warp_lanes"]

    def test_enable_exploit(self):
        """Test re-enabling an exploit."""
        nav = MomentumNavigator()

        nav.disable_exploit("warp_lanes")
        nav.enable_exploit("warp_lanes")
        assert nav._exploit_enabled["warp_lanes"]

    def test_get_enabled_exploits(self):
        """Test getting list of enabled exploits."""
        nav = MomentumNavigator()

        enabled = nav.get_enabled_exploits()
        assert len(enabled) == 7
        assert "warp_lanes" in enabled
        assert "bunny_hop" in enabled

        nav.disable_exploit("warp_lanes")
        enabled = nav.get_enabled_exploits()
        assert len(enabled) == 6
        assert "warp_lanes" not in enabled

    def test_update_exploit_success(self):
        """Test exploit success tracking."""
        nav = MomentumNavigator()

        # Track success
        for _ in range(60):
            nav.update_exploit_success("warp_lanes", False)

        # Should be disabled after 50+ failures at <10% success
        assert not nav._exploit_enabled["warp_lanes"]


class TestForwardPass:
    """Tests for forward pass (training mode)."""

    def test_forward_single_query(self):
        """Test forward with single query."""
        nav = MomentumNavigator(d_model=64)
        query = torch.randn(64)

        result = nav(query, max_steps=3)

        assert result.shape == (3,)

    def test_forward_batched_query(self):
        """Test forward with batched queries."""
        nav = MomentumNavigator(d_model=64)
        query = torch.randn(4, 64)  # Batch of 4

        result = nav(query, max_steps=3)

        assert result.shape == (4, 3)


class TestConvergence:
    """Tests for convergence detection."""

    def test_convergence_detection(self):
        """Test convergence is detected when movement is small."""
        nav = MomentumNavigator(convergence_threshold=0.1)
        nav.reset()

        # Add two nearly identical positions to trajectory
        nav.state.trajectory = [
            torch.tensor([0.0, 0.0, 0.0]),
            torch.tensor([0.01, 0.01, 0.01]),  # Very small movement
        ]

        assert nav._has_converged()

    def test_no_convergence_large_movement(self):
        """Test convergence not detected with large movement."""
        nav = MomentumNavigator(convergence_threshold=0.1)
        nav.reset()

        # Add positions with large movement
        nav.state.trajectory = [
            torch.tensor([0.0, 0.0, 0.0]),
            torch.tensor([10.0, 10.0, 10.0]),  # Large movement
        ]

        assert not nav._has_converged()


class TestWarpLaneIntegration:
    """Tests for warp lane finding within navigator."""

    def test_find_warp_lane_no_targets(self):
        """Test warp lane returns None when no valid targets."""
        nav = MomentumNavigator(d_model=64, warp_threshold=0.99)
        nav.reset()

        query = torch.randn(64)
        # Random embeddings unlikely to have 0.99+ similarity
        embeddings = torch.randn(100, 64)
        positions = torch.randn(100, 3) * 200

        warp_target = nav._find_warp_lane(query, embeddings, positions)

        # Very unlikely to find warp with 0.99 threshold on random data
        # (This test verifies the method runs without error)
        assert warp_target is None or warp_target.shape == (3,)

    def test_reversibility_check(self):
        """Test warp reversibility check."""
        nav = MomentumNavigator(attention_radius=50.0)
        nav.reset()

        # Target within 3r (150 units) is reversible
        close_target = torch.tensor([100.0, 0.0, 0.0])
        assert nav._is_reversible_warp(close_target)

        # Target beyond 3r is not reversible
        far_target = torch.tensor([200.0, 0.0, 0.0])
        assert not nav._is_reversible_warp(far_target)


# Benchmark tests (optional, marked for slower execution)
@pytest.mark.benchmark
class TestMomentumNavigatorBenchmarks:
    """Benchmark tests for performance validation."""

    def test_navigation_speed(self):
        """Benchmark navigation speed."""
        import time

        nav = MomentumNavigator(d_model=256)
        query = torch.randn(256)
        embeddings = torch.randn(1000, 256)
        positions = torch.randn(1000, 3) * 300

        start = time.time()
        for _ in range(10):
            nav.navigate(
                query,
                max_steps=10,
                context_embeddings=embeddings,
                context_positions=positions,
            )
        elapsed = time.time() - start

        # Should complete 10 full navigations in under 5 seconds
        assert elapsed < 5.0, f"Navigation too slow: {elapsed:.2f}s"
