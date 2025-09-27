"""
Test suite for orchestrator and models functionality.
"""
from __future__ import annotations
import pytest
from unittest.mock import Mock, patch
from acemcli.models import MetricResult, SizeScore
from acemcli.orchestrator import _merge, to_ndjson, WEIGHTS


class TestModels:
    """Test cases for data models."""
    
    def test_metric_result_creation(self):
        """Test creation of MetricResult dataclass."""
        size_score: SizeScore = {
            "raspberry_pi": 0.1,
            "jetson_nano": 0.3,
            "desktop_pc": 0.8,
            "aws_server": 1.0
        }
        
        result = MetricResult(
            name="test-model",
            category="MODEL",
            net_score=0.75,
            net_score_latency=100,
            ramp_up_time=0.8,
            ramp_up_time_latency=50,
            bus_factor=0.6,
            bus_factor_latency=30,
            performance_claims=0.9,
            performance_claims_latency=80,
            license=1.0,
            license_latency=10,
            size_score=size_score,
            size_score_latency=60,
            dataset_and_code_score=0.7,
            dataset_and_code_score_latency=90,
            dataset_quality=0.85,
            dataset_quality_latency=70,
            code_quality=0.9,
            code_quality_latency=40
        )
        
        assert result.name == "test-model"
        assert result.category == "MODEL"
        assert result.net_score == 0.75
        assert result.size_score["desktop_pc"] == 0.8
    
    def test_size_score_type_definition(self):
        """Test SizeScore TypedDict structure."""
        size_score: SizeScore = {
            "raspberry_pi": 0.1,
            "jetson_nano": 0.3,
            "desktop_pc": 0.8,
            "aws_server": 1.0
        }
        
        # All required keys should be present
        assert "raspberry_pi" in size_score
        assert "jetson_nano" in size_score
        assert "desktop_pc" in size_score
        assert "aws_server" in size_score
        
        # All values should be floats between 0 and 1
        for value in size_score.values():
            assert isinstance(value, float)
            assert 0.0 <= value <= 1.0


class TestOrchestrator:
    """Test cases for orchestrator functionality."""
    
    def create_mock_metric_result(self, name: str, **kwargs) -> MetricResult:
        """Helper to create mock MetricResult with default values."""
        defaults = {
            "name": name,
            "category": "MODEL",
            "net_score": 0.0,
            "net_score_latency": 0,
            "ramp_up_time": 0.0,
            "ramp_up_time_latency": 0,
            "bus_factor": 0.0,
            "bus_factor_latency": 0,
            "performance_claims": 0.0,
            "performance_claims_latency": 0,
            "license": 0.0,
            "license_latency": 0,
            "size_score": {"raspberry_pi": 0.0, "jetson_nano": 0.0, "desktop_pc": 0.0, "aws_server": 0.0},
            "size_score_latency": 0,
            "dataset_and_code_score": 0.0,
            "dataset_and_code_score_latency": 0,
            "dataset_quality": 0.0,
            "dataset_quality_latency": 0,
            "code_quality": 0.0,
            "code_quality_latency": 0
        }
        defaults.update(kwargs)
        return MetricResult(**defaults)
    
    def test_merge_prefers_non_zero_values(self):
        """Test that _merge prefers non-zero values from the second result."""
        base = self.create_mock_metric_result(
            "test",
            ramp_up_time=0.0,
            bus_factor=0.5,
            performance_claims=0.0
        )
        
        add = self.create_mock_metric_result(
            "test",
            ramp_up_time=0.8,
            bus_factor=0.0,  # Should not override non-zero base value
            performance_claims=0.9
        )
        
        result = _merge(base, add)
        
        assert result.ramp_up_time == 0.8  # Took non-zero from add
        assert result.bus_factor == 0.5    # Kept non-zero from base
        assert result.performance_claims == 0.9  # Took non-zero from add
    
    def test_merge_updates_latencies_to_maximum(self):
        """Test that _merge takes maximum latency values."""
        base = self.create_mock_metric_result(
            "test",
            ramp_up_time_latency=100,
            bus_factor_latency=50
        )
        
        add = self.create_mock_metric_result(
            "test", 
            ramp_up_time_latency=80,   # Lower than base
            bus_factor_latency=120     # Higher than base
        )
        
        result = _merge(base, add)
        
        assert result.ramp_up_time_latency == 100  # Kept higher base value
        assert result.bus_factor_latency == 120    # Took higher add value
    
    def test_merge_handles_size_score_correctly(self):
        """Test that _merge handles SizeScore dictionaries correctly."""
        base = self.create_mock_metric_result(
            "test",
            size_score={"raspberry_pi": 0.0, "jetson_nano": 0.5, "desktop_pc": 0.8, "aws_server": 0.0}
        )
        
        add = self.create_mock_metric_result(
            "test",
            size_score={"raspberry_pi": 0.3, "jetson_nano": 0.0, "desktop_pc": 0.0, "aws_server": 0.9}
        )
        
        result = _merge(base, add)
        
        assert result.size_score["raspberry_pi"] == 0.3  # Took non-zero from add
        assert result.size_score["jetson_nano"] == 0.5   # Kept non-zero from base  
        assert result.size_score["desktop_pc"] == 0.8    # Kept non-zero from base
        assert result.size_score["aws_server"] == 0.9    # Took non-zero from add
    
    def test_to_ndjson_produces_valid_json(self):
        """Test that to_ndjson produces valid JSON output."""
        result = self.create_mock_metric_result(
            "test-model",
            category="MODEL",
            net_score=0.75,
            ramp_up_time=0.8,
            size_score={"raspberry_pi": 0.1, "jetson_nano": 0.3, "desktop_pc": 0.8, "aws_server": 1.0}
        )
        
        json_bytes = to_ndjson(result)
        
        # Should be bytes
        assert isinstance(json_bytes, bytes)
        
        # Should end with newline
        assert json_bytes.endswith(b'\n')
        
        # Should be valid JSON
        import json
        json_str = json_bytes.decode('utf-8').strip()
        parsed = json.loads(json_str)
        
        # Check key fields
        assert parsed["name"] == "test-model"
        assert parsed["category"] == "MODEL"
        assert parsed["net_score"] == 0.75
        assert parsed["ramp_up_time"] == 0.8
        assert parsed["size_score"]["desktop_pc"] == 0.8
    
    def test_to_ndjson_includes_all_required_fields(self):
        """Test that to_ndjson includes all required NDJSON fields."""
        result = self.create_mock_metric_result("test")
        json_bytes = to_ndjson(result)
        
        import json
        parsed = json.loads(json_bytes.decode('utf-8').strip())
        
        # Check all required fields from Table 1 in spec
        required_fields = [
            "name", "category", "net_score", "net_score_latency",
            "ramp_up_time", "ramp_up_time_latency",
            "bus_factor", "bus_factor_latency", 
            "performance_claims", "performance_claims_latency",
            "license", "license_latency",
            "size_score", "size_score_latency",
            "dataset_and_code_score", "dataset_and_code_score_latency",
            "dataset_quality", "dataset_quality_latency",
            "code_quality", "code_quality_latency"
        ]
        
        for field in required_fields:
            assert field in parsed, f"Missing required field: {field}"
    
    def test_weights_configuration(self):
        """Test that WEIGHTS are properly configured."""
        # Check that WEIGHTS contains expected keys
        expected_keys = [
            "ramp_up_time", "bus_factor", "performance_claims", "license",
            "size_score.desktop_pc", "dataset_and_code_score", 
            "dataset_quality", "code_quality"
        ]
        
        for key in expected_keys:
            assert key in WEIGHTS, f"Missing weight for: {key}"
        
        # Check that weights are reasonable (between 0 and 1)
        for weight in WEIGHTS.values():
            assert 0.0 <= weight <= 1.0
        
        # Check that weights sum to approximately 1.0
        total_weight = sum(WEIGHTS.values())
        assert abs(total_weight - 1.0) < 0.01, f"Weights sum to {total_weight}, expected ~1.0"


def test_orchestrator_weights_sum_to_one():
    """Test that orchestrator weights sum to 1.0."""
    total = sum(WEIGHTS.values())
    assert abs(total - 1.0) < 0.01, f"Weights sum to {total}, should be close to 1.0"


def test_orchestrator_weights_are_reasonable():
    """Test that all weights are reasonable values."""
    for metric_name, weight in WEIGHTS.items():
        assert 0.0 < weight < 1.0, f"Weight for {metric_name} is {weight}, should be between 0 and 1"
        assert weight >= 0.05, f"Weight for {metric_name} is very low: {weight}"
