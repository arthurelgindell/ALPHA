#!/usr/bin/env python3
"""
Model Registry System
Tracks video generation models, benchmarks, and progressive updates
"""

import json
import time
import hashlib
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict, field
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ModelMetadata:
    """Metadata for a video generation model"""
    name: str
    version: str
    parameters: str  # e.g., "14B", "8.3B"
    architecture: str  # e.g., "MoE", "DiT"
    license: str  # e.g., "Apache 2.0"
    source: str  # HuggingFace repo or URL
    file_size_gb: float
    quality_score: float  # VBench or similar benchmark
    performance: Dict[str, str]  # e.g., {"720p_5s": "3-5min"}
    active: bool = False
    added_date: str = field(default_factory=lambda: datetime.now().isoformat())
    last_benchmarked: Optional[str] = None


@dataclass
class BenchmarkResult:
    """Benchmark result for a model"""
    model_name: str
    model_version: str
    test_name: str
    resolution: str  # e.g., "720p"
    duration: int  # seconds
    generation_time: float  # seconds
    quality_score: float  # 0-100
    prompt: str
    output_path: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    hardware: str = "Mac Studio 768GB"


class ModelRegistry:
    """
    Registry system for video generation models

    Tracks models, benchmarks, and facilitates progressive updates
    """

    def __init__(self, registry_path: str = "/Users/arthurdell/ARTHUR/video-generation/configs/model_registry.json"):
        """
        Initialize model registry

        Args:
            registry_path: Path to registry JSON file
        """
        self.registry_path = Path(registry_path)
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)

        self.models: Dict[str, ModelMetadata] = {}
        self.benchmarks: List[BenchmarkResult] = []

        self.load()
        logger.info(f"Model Registry initialized: {len(self.models)} models")

    def load(self):
        """Load registry from disk"""
        if self.registry_path.exists():
            data = json.loads(self.registry_path.read_text())

            # Load models
            for model_dict in data.get("models", []):
                model = ModelMetadata(**model_dict)
                self.models[model.name] = model

            # Load benchmarks
            for bench_dict in data.get("benchmarks", []):
                benchmark = BenchmarkResult(**bench_dict)
                self.benchmarks.append(benchmark)

            logger.info(f"Loaded registry: {len(self.models)} models, {len(self.benchmarks)} benchmarks")
        else:
            logger.info("No existing registry found, starting fresh")
            self._initialize_default_models()

    def save(self):
        """Save registry to disk"""
        data = {
            "models": [asdict(model) for model in self.models.values()],
            "benchmarks": [asdict(bench) for bench in self.benchmarks],
            "last_updated": datetime.now().isoformat()
        }

        self.registry_path.write_text(json.dumps(data, indent=2))
        logger.info(f"Registry saved: {self.registry_path}")

    def _initialize_default_models(self):
        """Initialize registry with known SOTA models"""
        # Wan 2.2 A14B (VBench #1)
        self.add_model(ModelMetadata(
            name="wan_2_2_a14b",
            version="1.0",
            parameters="14B MoE",
            architecture="MoE (Mixture-of-Experts)",
            license="Apache 2.0",
            source="Wan-AI/Wan2.2-T2V-A14B",
            file_size_gb=30.0,
            quality_score=84.7,  # VBench
            performance={"720p_5s": "3-5min", "720p_30s": "15-20min"},
            active=True
        ))

        # HunyuanVideo 1.5
        self.add_model(ModelMetadata(
            name="hunyuanvideo_1_5",
            version="1.5",
            parameters="8.3B",
            architecture="SSTA (Spatial-Temporal Self-Attention)",
            license="Apache 2.0",
            source="tencent/HunyuanVideo-1.5",
            file_size_gb=20.0,
            quality_score=82.0,
            performance={"720p_5s": "10-15min"},
            active=False  # Experimental
        ))

        # Mochi 1
        self.add_model(ModelMetadata(
            name="mochi_1",
            version="1.0",
            parameters="10B",
            architecture="AsymmDiT (Asymmetric Diffusion Transformer)",
            license="Apache 2.0",
            source="genmoai/mochi-1",
            file_size_gb=40.0,
            quality_score=80.0,
            performance={"720p_5s": "5-8min"},
            active=False  # Limited Mac support
        ))

        self.save()
        logger.info("Initialized default models")

    def add_model(self, model: ModelMetadata):
        """
        Add new model to registry

        Args:
            model: Model metadata
        """
        self.models[model.name] = model
        self.save()
        logger.info(f"Added model: {model.name} v{model.version}")

    def get_model(self, name: str) -> Optional[ModelMetadata]:
        """Get model by name"""
        return self.models.get(name)

    def get_active_model(self) -> Optional[ModelMetadata]:
        """Get currently active production model"""
        for model in self.models.values():
            if model.active:
                return model
        return None

    def set_active(self, name: str):
        """
        Set model as active (production)

        Args:
            name: Model name
        """
        # Deactivate all models
        for model in self.models.values():
            model.active = False

        # Activate specified model
        if name in self.models:
            self.models[name].active = True
            self.save()
            logger.info(f"Activated model: {name}")
        else:
            logger.error(f"Model not found: {name}")

    def add_benchmark(self, benchmark: BenchmarkResult):
        """
        Add benchmark result

        Args:
            benchmark: Benchmark result
        """
        self.benchmarks.append(benchmark)

        # Update model's last_benchmarked timestamp
        if benchmark.model_name in self.models:
            self.models[benchmark.model_name].last_benchmarked = benchmark.timestamp

        self.save()
        logger.info(f"Added benchmark: {benchmark.model_name} - {benchmark.test_name}")

    def get_benchmarks(self, model_name: Optional[str] = None) -> List[BenchmarkResult]:
        """
        Get benchmarks, optionally filtered by model

        Args:
            model_name: Optional model name filter

        Returns:
            List of benchmark results
        """
        if model_name:
            return [b for b in self.benchmarks if b.model_name == model_name]
        return self.benchmarks

    def compare_models(self, model_a: str, model_b: str) -> Dict:
        """
        Compare two models across benchmarks

        Args:
            model_a: First model name
            model_b: Second model name

        Returns:
            Comparison results
        """
        benchmarks_a = self.get_benchmarks(model_a)
        benchmarks_b = self.get_benchmarks(model_b)

        if not benchmarks_a or not benchmarks_b:
            logger.warning("One or both models have no benchmarks")
            return {}

        # Calculate averages
        avg_time_a = sum(b.generation_time for b in benchmarks_a) / len(benchmarks_a)
        avg_time_b = sum(b.generation_time for b in benchmarks_b) / len(benchmarks_b)

        avg_quality_a = sum(b.quality_score for b in benchmarks_a) / len(benchmarks_a)
        avg_quality_b = sum(b.quality_score for b in benchmarks_b) / len(benchmarks_b)

        comparison = {
            "model_a": {
                "name": model_a,
                "avg_generation_time": avg_time_a,
                "avg_quality_score": avg_quality_a,
                "benchmark_count": len(benchmarks_a)
            },
            "model_b": {
                "name": model_b,
                "avg_generation_time": avg_time_b,
                "avg_quality_score": avg_quality_b,
                "benchmark_count": len(benchmarks_b)
            },
            "winner": {
                "speed": model_a if avg_time_a < avg_time_b else model_b,
                "quality": model_a if avg_quality_a > avg_quality_b else model_b
            }
        }

        return comparison

    def list_models(self, active_only: bool = False) -> List[ModelMetadata]:
        """
        List all models

        Args:
            active_only: Only return active models

        Returns:
            List of model metadata
        """
        models = list(self.models.values())

        if active_only:
            models = [m for m in models if m.active]

        # Sort by quality score descending
        models.sort(key=lambda m: m.quality_score, reverse=True)

        return models

    def generate_report(self) -> str:
        """
        Generate human-readable registry report

        Returns:
            Report string
        """
        report = []
        report.append("="*60)
        report.append("MODEL REGISTRY REPORT")
        report.append("="*60)
        report.append("")

        # Active model
        active = self.get_active_model()
        if active:
            report.append(f"🏆 ACTIVE MODEL: {active.name} v{active.version}")
            report.append(f"   Quality: {active.quality_score} (VBench)")
            report.append(f"   Architecture: {active.architecture}")
            report.append("")

        # All models
        report.append("ALL MODELS:")
        report.append("")
        for model in self.list_models():
            status = "🟢 ACTIVE" if model.active else "⚪ INACTIVE"
            report.append(f"{status} {model.name} v{model.version}")
            report.append(f"   Parameters: {model.parameters}")
            report.append(f"   Quality: {model.quality_score}")
            report.append(f"   License: {model.license}")
            report.append(f"   Performance: {model.performance}")

            # Benchmark count
            bench_count = len(self.get_benchmarks(model.name))
            report.append(f"   Benchmarks: {bench_count}")
            report.append("")

        # Recent benchmarks
        recent_benchmarks = sorted(
            self.benchmarks,
            key=lambda b: b.timestamp,
            reverse=True
        )[:5]

        if recent_benchmarks:
            report.append("RECENT BENCHMARKS:")
            report.append("")
            for bench in recent_benchmarks:
                report.append(f"  • {bench.model_name} - {bench.test_name}")
                report.append(f"    {bench.resolution} {bench.duration}s → {bench.generation_time:.1f}s")
                report.append(f"    Quality: {bench.quality_score}/100")
                report.append("")

        report.append("="*60)

        return "\n".join(report)


def example_usage():
    """Example: Model registry usage"""
    registry = ModelRegistry()

    # List all models
    logger.info("\n" + registry.generate_report())

    # Get active model
    active = registry.get_active_model()
    if active:
        logger.info(f"Active model: {active.name}")

    # Add benchmark
    benchmark = BenchmarkResult(
        model_name="wan_2_2_a14b",
        model_version="1.0",
        test_name="Standard benchmark",
        resolution="720p",
        duration=5,
        generation_time=240.5,  # 4 minutes
        quality_score=85.0,
        prompt="A cinematic shot of a cyberpunk city",
        output_path="/Users/arthurdell/ARTHUR/videos/raw/test_video.mp4"
    )
    registry.add_benchmark(benchmark)

    logger.info("Benchmark added")


if __name__ == "__main__":
    example_usage()
