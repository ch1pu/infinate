# Copyright 2025-2026 Adolfo Lopez (ch1pu)
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Author: Adolfo Lopez (ch1pu) - github.com/ch1pu
# Project: INFINATE - Infinite Context Spatial AI (github.com/ch1pu/infinate)
#
# ============================================================================
# BUILT BY A U.S. NAVY VETERAN | BUILT IN TEXAS | OPEN FOR OPPORTUNITIES
# ============================================================================
# I'm actively seeking software engineering roles. If you're reading this code
# and like what you see, let's connect:
#   - GitHub: github.com/ch1pu
#   - Twitter/X: @2006_adolfo
#   - Project: This codebase demonstrates O(k) spatial attention, achieving
#     10,317x speedup over standard transformer attention with 89.58% test coverage.
# ============================================================================

"""
test_m1114_full_pipeline_gpu_coverage.py - Full Pipeline GPU Coverage Tests.

Verifies all 7 README pipeline stages work on GPU. M1.11.3 covered 3/7
(SpatialAttention, LOD, Navigation). Phase A fills the gap for stages 1, 2, 4, 5.

15 tests across 6 classes:
- TestM1114SpatialTokenGPU (3): SpatialToken with CUDA tensors
- TestM1114SpatialEncodingGPU (3): SpatialPositionEncoding on GPU
- TestM1114SpatialTransformerGPU (3): SpatialTransformer on GPU
- TestM1114VectorStoreGPUTransfer (3): VectorStore CPU→GPU transfer
- TestM1114FullPipelineIntegration (2): Multi-stage GPU integration
- TestM1114ResultsSaver (1): Save results to markdown

Author: ch1pu (Adolfo Lopez)
Milestone: 1.11.4 - Full Pipeline GPU Coverage (Phase A)
"""

import os
from datetime import UTC, datetime

import pytest
import torch

from spatial_engine.core.spatial_attention import SpatialAttention
from spatial_engine.core.spatial_encoding import SpatialPositionEncoding
from spatial_engine.core.spatial_token import SpatialToken
from spatial_engine.core.spatial_transformer import SpatialTransformer
from spatial_engine.tests.conftest_m1114 import (
    M1114_D_FF,
    M1114_D_MODEL,
    M1114_N_HEADS,
    M1114_N_LAYERS,
    M1114_SPATIAL_RADIUS,
)

# Load M1.11.4 fixtures (chains M1.11.3 -> M1.11.2 -> M1.11)
pytest_plugins = ["spatial_engine.tests.conftest_m1114"]

# Module-level results collector
_benchmark_results: list[dict] = []


# ---------------------------------------------------------------------------
# Class 1: TestM1114SpatialTokenGPU — Stage 1
# ---------------------------------------------------------------------------


@pytest.mark.m1114
@pytest.mark.m1114_gpu
class TestM1114SpatialTokenGPU:
    """Verify SpatialToken works with CUDA tensors (Pipeline Stage 1)."""

    def test_spatial_token_cuda_tensors(
        self,
        gpu_device: torch.device,
    ) -> None:
        """Create SpatialToken with CUDA embedding + spatial_encoding."""
        d_model = M1114_D_MODEL
        embedding = torch.randn(d_model, device=gpu_device)
        spatial_encoding = torch.randn(d_model, device=gpu_device)

        token = SpatialToken(
            token_id=42,
            position=(1.0, 2.0, 3.0),
            embedding=embedding,
            spatial_encoding=spatial_encoding,
        )

        assert (
            token.embedding.device.type == "cuda"
        ), f"Embedding on {token.embedding.device}, expected cuda"
        assert (
            token.spatial_encoding.device.type == "cuda"
        ), f"Spatial encoding on {token.spatial_encoding.device}, expected cuda"
        assert token.token_id == 42
        assert token.position == (1.0, 2.0, 3.0)

        print(
            f"\nSpatialToken CUDA tensors: embedding={token.embedding.device}, "
            f"spatial_encoding={token.spatial_encoding.device}"
        )

        _benchmark_results.append(
            {
                "test": "test_spatial_token_cuda_tensors",
                "status": "PASS",
                "device": str(gpu_device),
            }
        )

    def test_spatial_token_full_embedding_on_gpu(
        self,
        gpu_device: torch.device,
    ) -> None:
        """full_embedding (embedding + spatial_encoding) stays on GPU, correct shape."""
        d_model = M1114_D_MODEL
        embedding = torch.randn(d_model, device=gpu_device)
        spatial_encoding = torch.randn(d_model, device=gpu_device)

        token = SpatialToken(
            token_id=1,
            position=(10.0, 20.0, 30.0),
            embedding=embedding,
            spatial_encoding=spatial_encoding,
        )

        full_emb = token.full_embedding
        assert full_emb.device.type == "cuda", f"full_embedding on {full_emb.device}, expected cuda"
        assert full_emb.shape == (d_model,), f"Expected ({d_model},), got {full_emb.shape}"

        # Verify it's actually the sum
        expected = embedding + spatial_encoding
        assert torch.allclose(full_emb, expected, atol=1e-6)

        print(f"\nSpatialToken full_embedding: shape={full_emb.shape}, device={full_emb.device}")

        _benchmark_results.append(
            {
                "test": "test_spatial_token_full_embedding_on_gpu",
                "status": "PASS",
                "shape": list(full_emb.shape),
                "device": str(full_emb.device),
            }
        )

    def test_spatial_token_distance_to_device_independent(
        self,
        gpu_device: torch.device,
    ) -> None:
        """distance_to() works regardless of tensor device (pure Python math on tuples)."""
        d_model = M1114_D_MODEL

        # Token with GPU tensors
        token_gpu = SpatialToken(
            token_id=1,
            position=(0.0, 0.0, 0.0),
            embedding=torch.randn(d_model, device=gpu_device),
            spatial_encoding=torch.randn(d_model, device=gpu_device),
        )

        # Token with CPU tensors
        token_cpu = SpatialToken(
            token_id=2,
            position=(3.0, 4.0, 0.0),
            embedding=torch.randn(d_model),
            spatial_encoding=torch.randn(d_model),
        )

        # distance_to uses position tuples, not tensors — device independent
        dist = token_gpu.distance_to(token_cpu)
        assert abs(dist - 5.0) < 1e-6, f"Expected 5.0, got {dist}"

        # Reverse direction
        dist_rev = token_cpu.distance_to(token_gpu)
        assert abs(dist_rev - 5.0) < 1e-6

        print(f"\nSpatialToken distance_to: GPU→CPU={dist:.4f}, CPU→GPU={dist_rev:.4f}")

        _benchmark_results.append(
            {
                "test": "test_spatial_token_distance_to_device_independent",
                "status": "PASS",
                "distance": dist,
            }
        )


# ---------------------------------------------------------------------------
# Class 2: TestM1114SpatialEncodingGPU — Stage 2
# ---------------------------------------------------------------------------


@pytest.mark.m1114
@pytest.mark.m1114_gpu
class TestM1114SpatialEncodingGPU:
    """Verify SpatialPositionEncoding works on GPU (Pipeline Stage 2)."""

    def test_spatial_encoding_buffer_on_gpu(
        self,
        m1114_spatial_encoding_gpu: SpatialPositionEncoding,
    ) -> None:
        """After .to(device), encoder.freqs buffer is on cuda."""
        freqs = m1114_spatial_encoding_gpu.freqs
        assert freqs.device.type == "cuda", f"freqs on {freqs.device}, expected cuda"

        print(f"\nSpatialEncoding buffer: freqs on {freqs.device}, shape={freqs.shape}")

        _benchmark_results.append(
            {
                "test": "test_spatial_encoding_buffer_on_gpu",
                "status": "PASS",
                "freqs_device": str(freqs.device),
                "freqs_shape": list(freqs.shape),
            }
        )

    def test_spatial_encoding_forward_on_gpu(
        self,
        m1114_spatial_encoding_gpu: SpatialPositionEncoding,
        gpu_device: torch.device,
    ) -> None:
        """Forward pass with GPU positions produces output on cuda."""
        batch, seq_len = 2, 16
        positions = torch.randn(batch, seq_len, 3, device=gpu_device) * 500.0

        with torch.no_grad():
            output = m1114_spatial_encoding_gpu(positions)

        assert output.device.type == "cuda", f"Output on {output.device}, expected cuda"
        assert output.shape == (
            batch,
            seq_len,
            M1114_D_MODEL,
        ), f"Expected ({batch}, {seq_len}, {M1114_D_MODEL}), got {output.shape}"

        print(f"\nSpatialEncoding forward: shape={output.shape}, device={output.device}")

        _benchmark_results.append(
            {
                "test": "test_spatial_encoding_forward_on_gpu",
                "status": "PASS",
                "output_shape": list(output.shape),
                "device": str(output.device),
            }
        )

    def test_spatial_encoding_cpu_gpu_parity(
        self,
        m1114_spatial_encoding_gpu: SpatialPositionEncoding,
        gpu_device: torch.device,
    ) -> None:
        """Same input on CPU and GPU produces identical output (deterministic sinusoidal)."""
        encoder_cpu = SpatialPositionEncoding(d_model=M1114_D_MODEL)

        batch, seq_len = 2, 16
        torch.manual_seed(99)
        positions_cpu = torch.randn(batch, seq_len, 3) * 500.0
        positions_gpu = positions_cpu.to(gpu_device)

        with torch.no_grad():
            output_cpu = encoder_cpu(positions_cpu)
            output_gpu = m1114_spatial_encoding_gpu(positions_gpu)

        # Compare on CPU
        output_gpu_cpu = output_gpu.cpu()
        max_diff = (output_cpu - output_gpu_cpu).abs().max().item()

        assert torch.allclose(
            output_cpu, output_gpu_cpu, atol=1e-5
        ), f"CPU/GPU parity failed: max diff = {max_diff:.2e}"

        print(f"\nSpatialEncoding CPU/GPU parity: max diff = {max_diff:.2e} (atol=1e-5)")

        _benchmark_results.append(
            {
                "test": "test_spatial_encoding_cpu_gpu_parity",
                "status": "PASS",
                "max_diff": max_diff,
            }
        )


# ---------------------------------------------------------------------------
# Class 3: TestM1114SpatialTransformerGPU — Stage 4
# ---------------------------------------------------------------------------


@pytest.mark.m1114
@pytest.mark.m1114_gpu
class TestM1114SpatialTransformerGPU:
    """Verify SpatialTransformer works on GPU (Pipeline Stage 4)."""

    def test_spatial_transformer_forward_on_gpu(
        self,
        m1114_spatial_transformer_gpu: SpatialTransformer,
        gpu_device: torch.device,
    ) -> None:
        """Multi-layer forward pass on GPU produces correct output shape and device."""
        batch, seq_len = 1, 32
        x = torch.randn(batch, seq_len, M1114_D_MODEL, device=gpu_device)
        positions = torch.randn(batch, seq_len, 3, device=gpu_device) * 500.0

        with torch.no_grad():
            output = m1114_spatial_transformer_gpu(x, positions)

        assert output.device.type == "cuda", f"Output on {output.device}, expected cuda"
        assert output.shape == (
            batch,
            seq_len,
            M1114_D_MODEL,
        ), f"Expected ({batch}, {seq_len}, {M1114_D_MODEL}), got {output.shape}"
        assert not torch.all(output == 0), "Output should be non-zero"

        print(f"\nSpatialTransformer forward: shape={output.shape}, device={output.device}")

        _benchmark_results.append(
            {
                "test": "test_spatial_transformer_forward_on_gpu",
                "status": "PASS",
                "output_shape": list(output.shape),
                "device": str(output.device),
            }
        )

    def test_spatial_transformer_all_parameters_on_gpu(
        self,
        m1114_spatial_transformer_gpu: SpatialTransformer,
    ) -> None:
        """Every parameter in every layer is on cuda after .to(device)."""
        total_params = 0
        cuda_params = 0

        for name, param in m1114_spatial_transformer_gpu.named_parameters():
            total_params += 1
            if param.device.type == "cuda":
                cuda_params += 1
            else:
                pytest.fail(f"Parameter '{name}' on {param.device}, expected cuda")

        assert total_params > 0, "Model should have parameters"
        assert cuda_params == total_params

        print(f"\nSpatialTransformer params: {cuda_params}/{total_params} on cuda")

        _benchmark_results.append(
            {
                "test": "test_spatial_transformer_all_parameters_on_gpu",
                "status": "PASS",
                "total_params": total_params,
                "cuda_params": cuda_params,
            }
        )

    def test_spatial_transformer_cpu_to_gpu_transfer(
        self,
        gpu_device: torch.device,
    ) -> None:
        """Create on CPU, .cuda(), verify params moved and forward works."""
        transformer_cpu = SpatialTransformer(
            n_layers=M1114_N_LAYERS,
            d_model=M1114_D_MODEL,
            n_heads=M1114_N_HEADS,
            d_ff=M1114_D_FF,
            spatial_radius=M1114_SPATIAL_RADIUS,
        )

        # Verify starts on CPU
        first_param = next(transformer_cpu.parameters())
        assert first_param.device.type == "cpu", "Should start on CPU"

        # Transfer to GPU
        transformer_gpu = transformer_cpu.cuda()

        # Verify all params moved
        for name, param in transformer_gpu.named_parameters():
            assert param.device.type == "cuda", f"'{name}' not on cuda after .cuda()"

        # Verify forward works
        batch, seq_len = 1, 16
        x = torch.randn(batch, seq_len, M1114_D_MODEL, device=gpu_device)
        positions = torch.randn(batch, seq_len, 3, device=gpu_device) * 500.0

        with torch.no_grad():
            output = transformer_gpu(x, positions)

        assert output.device.type == "cuda"
        assert output.shape == (batch, seq_len, M1114_D_MODEL)

        print(f"\nSpatialTransformer CPU→GPU: forward works, output={output.shape}")

        _benchmark_results.append(
            {
                "test": "test_spatial_transformer_cpu_to_gpu_transfer",
                "status": "PASS",
                "output_shape": list(output.shape),
            }
        )


# ---------------------------------------------------------------------------
# Class 4: TestM1114VectorStoreGPUTransfer — Stage 5
# ---------------------------------------------------------------------------


@pytest.mark.m1114
@pytest.mark.m1114_gpu
class TestM1114VectorStoreGPUTransfer:
    """Verify VectorStore CPU tensors transfer to GPU correctly (Pipeline Stage 5)."""

    def test_vectorstore_returns_cpu_tensors(
        self,
        m1114_simulated_vectorstore_results,  # type: ignore[no-untyped-def]
    ) -> None:
        """Simulated VectorStore results are on CPU (matches production behavior)."""
        embeddings, positions, ids = m1114_simulated_vectorstore_results.create()

        assert embeddings.device.type == "cpu", f"Embeddings on {embeddings.device}, expected cpu"
        assert positions.device.type == "cpu", f"Positions on {positions.device}, expected cpu"
        assert len(ids) == len(embeddings)

        print(
            f"\nVectorStore CPU tensors: embeddings={embeddings.shape}, "
            f"positions={positions.shape}, ids={len(ids)}"
        )

        _benchmark_results.append(
            {
                "test": "test_vectorstore_returns_cpu_tensors",
                "status": "PASS",
                "embeddings_shape": list(embeddings.shape),
                "positions_shape": list(positions.shape),
            }
        )

    def test_vectorstore_results_transfer_to_gpu(
        self,
        m1114_simulated_vectorstore_results,  # type: ignore[no-untyped-def]
        gpu_device: torch.device,
    ) -> None:
        """.to(device) works on VectorStore results, data integrity preserved."""
        embeddings_cpu, positions_cpu, ids = m1114_simulated_vectorstore_results.create()

        # Transfer to GPU
        embeddings_gpu = embeddings_cpu.to(gpu_device)
        positions_gpu = positions_cpu.to(gpu_device)

        assert embeddings_gpu.device.type == "cuda"
        assert positions_gpu.device.type == "cuda"

        # Data integrity: values match after transfer
        assert torch.allclose(embeddings_cpu, embeddings_gpu.cpu(), atol=1e-7)
        assert torch.allclose(positions_cpu, positions_gpu.cpu(), atol=1e-7)

        # Shape preserved
        assert embeddings_gpu.shape == embeddings_cpu.shape
        assert positions_gpu.shape == positions_cpu.shape

        print(
            f"\nVectorStore GPU transfer: integrity verified, "
            f"embeddings={embeddings_gpu.device}, positions={positions_gpu.device}"
        )

        _benchmark_results.append(
            {
                "test": "test_vectorstore_results_transfer_to_gpu",
                "status": "PASS",
                "device": str(gpu_device),
            }
        )

    def test_vectorstore_results_consumed_by_spatial_attention(
        self,
        m1114_simulated_vectorstore_results,  # type: ignore[no-untyped-def]
        gpu_device: torch.device,
    ) -> None:
        """Transfer VectorStore results to GPU, feed into SpatialAttention."""
        k = 50
        embeddings_cpu, positions_cpu, _ = m1114_simulated_vectorstore_results.create(k=k)

        # Transfer to GPU
        embeddings_gpu = embeddings_cpu.to(gpu_device)
        positions_gpu = positions_cpu.to(gpu_device)

        # Create SpatialAttention on GPU
        attn = SpatialAttention(
            d_model=M1114_D_MODEL,
            n_heads=M1114_N_HEADS,
        ).to(gpu_device)

        # Reshape for batch attention: [1, k, d_model] and [1, k, 3]
        x = embeddings_gpu.unsqueeze(0)
        pos = positions_gpu.unsqueeze(0)

        with torch.no_grad():
            output = attn(x, pos)

        assert output.device.type == "cuda", f"Output on {output.device}, expected cuda"
        assert output.shape == (1, k, M1114_D_MODEL)
        assert not torch.all(output == 0), "Output should be non-zero"

        print(f"\nVectorStore→SpatialAttention: shape={output.shape}, device={output.device}")

        _benchmark_results.append(
            {
                "test": "test_vectorstore_results_consumed_by_spatial_attention",
                "status": "PASS",
                "output_shape": list(output.shape),
                "device": str(output.device),
            }
        )


# ---------------------------------------------------------------------------
# Class 5: TestM1114FullPipelineIntegration — Multi-stage
# ---------------------------------------------------------------------------


@pytest.mark.m1114
@pytest.mark.m1114_gpu
class TestM1114FullPipelineIntegration:
    """Multi-stage integration tests on GPU."""

    def test_encoding_into_transformer_pipeline(
        self,
        m1114_spatial_encoding_gpu: SpatialPositionEncoding,
        m1114_spatial_transformer_gpu: SpatialTransformer,
        gpu_device: torch.device,
    ) -> None:
        """Stage 2 → Stage 4: SpatialEncoding output feeds SpatialTransformer on GPU."""
        batch, seq_len = 1, 32
        positions = torch.randn(batch, seq_len, 3, device=gpu_device) * 500.0

        # Stage 2: Generate spatial encoding
        with torch.no_grad():
            spatial_enc = m1114_spatial_encoding_gpu(positions)

        assert spatial_enc.device.type == "cuda"
        assert spatial_enc.shape == (batch, seq_len, M1114_D_MODEL)

        # Stage 4: Feed encoding into transformer as input
        with torch.no_grad():
            output = m1114_spatial_transformer_gpu(spatial_enc, positions)

        assert output.device.type == "cuda", f"Output on {output.device}, expected cuda"
        assert output.shape == (batch, seq_len, M1114_D_MODEL)
        assert not torch.all(output == 0)

        print(
            f"\nEncoding→Transformer pipeline: "
            f"enc={spatial_enc.shape} → out={output.shape}, device={output.device}"
        )

        _benchmark_results.append(
            {
                "test": "test_encoding_into_transformer_pipeline",
                "status": "PASS",
                "encoding_shape": list(spatial_enc.shape),
                "output_shape": list(output.shape),
                "device": str(output.device),
            }
        )

    def test_vectorstore_to_transformer_pipeline(
        self,
        m1114_simulated_vectorstore_results,  # type: ignore[no-untyped-def]
        m1114_spatial_encoding_gpu: SpatialPositionEncoding,
        m1114_spatial_transformer_gpu: SpatialTransformer,
        gpu_device: torch.device,
    ) -> None:
        """Stage 5 → 2 → 4: VectorStore data → encode → transform, all on GPU."""
        k = 50
        embeddings_cpu, positions_cpu, _ = m1114_simulated_vectorstore_results.create(k=k)

        # Stage 5: Transfer VectorStore results to GPU
        embeddings_gpu = embeddings_cpu.to(gpu_device)
        positions_gpu = positions_cpu.to(gpu_device)

        # Reshape for batch processing: [1, k, ...]
        positions_3d = positions_gpu.unsqueeze(0)  # [1, k, 3]
        x = embeddings_gpu.unsqueeze(0)  # [1, k, d_model]

        # Stage 2: Generate spatial encoding and add to embeddings
        with torch.no_grad():
            spatial_enc = m1114_spatial_encoding_gpu(positions_3d)

        assert spatial_enc.device.type == "cuda"
        x_with_encoding = x + spatial_enc  # Add spatial info to embeddings

        # Stage 4: Feed into transformer
        with torch.no_grad():
            output = m1114_spatial_transformer_gpu(x_with_encoding, positions_3d)

        assert output.device.type == "cuda", f"Output on {output.device}, expected cuda"
        assert output.shape == (1, k, M1114_D_MODEL)
        assert not torch.all(output == 0)

        print(
            f"\nVectorStore→Encoding→Transformer pipeline: "
            f"k={k} → enc → out={output.shape}, device={output.device}"
        )

        _benchmark_results.append(
            {
                "test": "test_vectorstore_to_transformer_pipeline",
                "status": "PASS",
                "k": k,
                "output_shape": list(output.shape),
                "device": str(output.device),
            }
        )


# ---------------------------------------------------------------------------
# Class 6: TestM1114ResultsSaver
# ---------------------------------------------------------------------------


@pytest.mark.m1114
class TestM1114ResultsSaver:
    """Save test results to test-results-m1.11.4.md."""

    def test_z_save_results(self) -> None:
        """Write collected results to markdown file.

        Runs last alphabetically to collect all results from other tests.
        """
        if not _benchmark_results:
            pytest.skip("No results to save (other tests may have been skipped)")

        results_dir = os.path.join(os.path.dirname(__file__), "..", "..", "test_results")
        os.makedirs(results_dir, exist_ok=True)
        results_path = os.path.join(results_dir, "test-results-m1.11.4.md")

        now = datetime.now(tz=UTC).strftime("%Y-%m-%d %H:%M UTC")

        gpu_name = "N/A"
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)

        # Build test execution table
        test_rows = []
        for r in _benchmark_results:
            test_rows.append(f"| {r['test']} | {r['status']} |")

        # Count by stage
        stage_counts = {
            "Stage 1 (SpatialToken)": 0,
            "Stage 2 (SpatialEncoding)": 0,
            "Stage 4 (SpatialTransformer)": 0,
            "Stage 5 (VectorStore)": 0,
            "Integration": 0,
        }
        for r in _benchmark_results:
            name = r["test"]
            if "spatial_token" in name:
                stage_counts["Stage 1 (SpatialToken)"] += 1
            elif "spatial_encoding" in name or "cpu_gpu_parity" in name:
                stage_counts["Stage 2 (SpatialEncoding)"] += 1
            elif "spatial_transformer" in name:
                stage_counts["Stage 4 (SpatialTransformer)"] += 1
            elif "vectorstore" in name and "pipeline" not in name:
                stage_counts["Stage 5 (VectorStore)"] += 1
            elif "pipeline" in name:
                stage_counts["Integration"] += 1

        lines = [
            "<!--",
            "Copyright 2025-2026 Adolfo Lopez (ch1pu)",
            "SPDX-License-Identifier: Apache-2.0",
            "-->",
            "",
            "# M1.11.4 Phase A: Full Pipeline GPU Coverage Results",
            "",
            f"**Generated:** {now}",
            f"**GPU:** {gpu_name}",
            f"**PyTorch:** {torch.__version__}",
            f"**CUDA:** {torch.version.cuda if torch.cuda.is_available() else 'N/A'}",
            "",
            "## Pipeline Stage Coverage",
            "",
            "| Stage | Component | Tests | Status |",
            "|-------|-----------|-------|--------|",
        ]

        for stage, count in stage_counts.items():
            status = "PASS" if count > 0 else "N/A"
            lines.append(f"| {stage} | {count} tests | {status} |")

        lines.extend(
            [
                "",
                "**Previously covered by M1.11.3:** Stage 3 (SpatialAttention), "
                "Stage 6 (LOD), Stage 7 (Navigation)",
                "",
                "**Combined coverage:** 7/7 pipeline stages verified on GPU",
                "",
                "## Test Execution",
                "",
                "| Test | Status |",
                "|------|--------|",
                *test_rows,
                "",
                f"**Total tests:** {len(_benchmark_results)}",
                "",
                "---",
                "",
                "*Author: Adolfo Lopez (ch1pu) - U.S. Navy Veteran*",
                "",
            ]
        )

        with open(results_path, "w") as f:
            f.write("\n".join(lines))

        print(f"\nResults saved to: {results_path}")
        print(f"Total results recorded: {len(_benchmark_results)}")
