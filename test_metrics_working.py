#!/usr/bin/env python3
"""
Quick test script to verify metrics are working correctly.
Tests both Dataset & Code Score and Performance Claims metrics.
"""

import sys
import os
import time

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from acemcli.metrics.dataset_code_score import DatasetAndCodeScoreMetric
from acemcli.metrics.performance_claims import PerformanceClaimsMetric
from acemcli.models import MetricResult

def test_dataset_code_score():
    """Test Dataset & Code Score metric."""
    print("🧪 Testing Dataset & Code Score Metric...")
    
    metric = DatasetAndCodeScoreMetric()
    
    # Test supports method
    assert metric.supports("https://huggingface.co/google/gemma-3-270m", "MODEL") == True
    assert metric.supports("https://huggingface.co/datasets/squad", "DATASET") == True  
    assert metric.supports("https://github.com/example/repo", "MODEL") == False
    print("✅ supports() method working correctly")
    
    # Test compute method (this will fail gracefully with score=0.0 for non-existent model)
    try:
        result = metric.compute("https://huggingface.co/test/nonexistent-model", "MODEL")
        
        # Verify return type
        assert isinstance(result, MetricResult), f"Expected MetricResult, got {type(result)}"
        
        # Verify score is in valid range
        assert 0.0 <= result.dataset_and_code_score <= 1.0, f"Score {result.dataset_and_code_score} not in [0,1]"
        
        # Verify latency is positive integer
        assert isinstance(result.dataset_and_code_score_latency, int), "Latency should be int"
        assert result.dataset_and_code_score_latency >= 0, "Latency should be non-negative"
        
        print(f"✅ compute() method working - Score: {result.dataset_and_code_score:.3f}, Latency: {result.dataset_and_code_score_latency}ms")
        
    except Exception as e:
        print(f"❌ compute() method failed: {e}")
        return False
    
    return True

def test_performance_claims():
    """Test Performance Claims metric."""
    print("\n🧪 Testing Performance Claims Metric...")
    
    metric = PerformanceClaimsMetric()
    
    # Test supports method
    assert metric.supports("https://huggingface.co/google/gemma-3-270m", "MODEL") == True
    assert metric.supports("https://huggingface.co/datasets/squad", "DATASET") == False
    assert metric.supports("https://github.com/example/repo", "MODEL") == False
    print("✅ supports() method working correctly")
    
    # Test compute method
    try:
        result = metric.compute("https://huggingface.co/test/nonexistent-model", "MODEL")
        
        # Verify return type
        assert isinstance(result, MetricResult), f"Expected MetricResult, got {type(result)}"
        
        # Verify score is in valid range
        assert 0.0 <= result.performance_claims <= 1.0, f"Score {result.performance_claims} not in [0,1]"
        
        # Verify latency is positive integer
        assert isinstance(result.performance_claims_latency, int), "Latency should be int"
        assert result.performance_claims_latency >= 0, "Latency should be non-negative"
        
        print(f"✅ compute() method working - Score: {result.performance_claims:.3f}, Latency: {result.performance_claims_latency}ms")
        
    except Exception as e:
        print(f"❌ compute() method failed: {e}")
        return False
    
    return True

def test_metric_registration():
    """Test that metrics are properly registered."""
    print("\n🧪 Testing Metric Registration...")
    
    from acemcli.metrics.base import all_metrics
    
    metrics = all_metrics()
    metric_names = [m.name for m in metrics]
    
    print(f"📋 Registered metrics: {metric_names}")
    
    assert "dataset_and_code_score" in metric_names, "Dataset & Code Score metric not registered"
    assert "performance_claims" in metric_names, "Performance Claims metric not registered"
    
    print("✅ Both metrics properly registered!")
    return True

def main():
    """Run all tests."""
    print("🚀 Testing Your Metrics Implementation\n")
    
    success = True
    
    # Run tests
    success &= test_dataset_code_score()
    success &= test_performance_claims() 
    success &= test_metric_registration()
    
    # Print final result
    print("\n" + "="*50)
    if success:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Task 3.3: Dataset & Code Score metric working")
        print("✅ Task 4.3: Performance Claims metric working")
        print("✅ Task 4.2: Metrics properly registered")
        print("\nYour metrics are ready for integration! 🚀")
    else:
        print("❌ SOME TESTS FAILED!")
        print("Please check the error messages above.")
    
    print("="*50)
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())
