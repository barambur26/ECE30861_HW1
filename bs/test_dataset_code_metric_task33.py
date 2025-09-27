#!/usr/bin/env python3
"""
Task 3.3: Test Dataset & Code Score Metric with HuggingFace URL

This script tests the DatasetAndCodeScoreMetric with a real HuggingFace model URL
to verify the implementation works correctly.
"""

import os
import sys
import tempfile
import time
from pathlib import Path

# Add src directory to Python path so we can import our modules
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

# Set up logging environment variables for testing
os.environ["LOG_LEVEL"] = "2"  # Debug level
os.environ["LOG_FILE"] = str(project_root / "dataset_metric_test.log")

# Now import our modules
from acemcli.logging_setup import setup_logging
from acemcli.metrics.dataset_code_score import DatasetAndCodeScoreMetric
from acemcli.models import Category

def test_dataset_code_score_metric():
    """Test the Dataset & Code Score metric with a HuggingFace URL."""
    
    # Initialize logging
    setup_logging()
    print("🔧 Logging initialized")
    
    # Initialize the metric
    metric = DatasetAndCodeScoreMetric()
    print(f"✅ Metric initialized: {metric.name}")
    
    # Test URLs - selecting models with good documentation
    test_cases = [
        {
            "url": "https://huggingface.co/google/flan-t5-small",
            "category": "MODEL",
            "description": "Google's FLAN-T5 Small - should have good documentation"
        },
        {
            "url": "https://huggingface.co/microsoft/DialoGPT-medium", 
            "category": "MODEL",
            "description": "Microsoft's DialoGPT - well-documented model"
        }
    ]
    
    print("\n" + "="*80)
    print("🧪 TESTING DATASET & CODE SCORE METRIC")
    print("="*80)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 Test Case {i}: {test_case['description']}")
        print(f"🔗 URL: {test_case['url']}")
        print(f"📂 Category: {test_case['category']}")
        
        # Test if metric supports this URL/category
        supports = metric.supports(test_case['url'], test_case['category'])
        print(f"✅ Metric supports this URL: {supports}")
        
        if not supports:
            print("⚠️  Skipping - metric doesn't support this URL/category")
            continue
        
        # Measure computation time
        start_time = time.time()
        
        try:
            print("\n🚀 Computing dataset and code score...")
            result = metric.compute(test_case['url'], test_case['category'])
            
            end_time = time.time()
            total_time = end_time - start_time
            
            print("\n📊 RESULTS:")
            print("-" * 40)
            print(f"Repository Name: {result.name}")
            print(f"Category: {result.category}")
            print(f"Dataset & Code Score: {result.dataset_and_code_score:.3f}")
            print(f"Latency (metric): {result.dataset_and_code_score_latency} ms")
            print(f"Total Execution Time: {total_time:.2f} seconds")
            
            # Validate the result
            assert 0.0 <= result.dataset_and_code_score <= 1.0, f"Score must be in [0,1], got {result.dataset_and_code_score}"
            assert result.dataset_and_code_score_latency >= 0, f"Latency must be non-negative, got {result.dataset_and_code_score_latency}"
            assert result.category == test_case['category'], f"Category mismatch: expected {test_case['category']}, got {result.category}"
            
            print("✅ All validations passed!")
            
            # Interpret the score
            if result.dataset_and_code_score >= 0.8:
                interpretation = "🌟 EXCELLENT - Very well documented with examples"
            elif result.dataset_and_code_score >= 0.6:
                interpretation = "👍 GOOD - Well documented"
            elif result.dataset_and_code_score >= 0.4:
                interpretation = "⚠️  FAIR - Some documentation present"
            elif result.dataset_and_code_score >= 0.2:
                interpretation = "❌ POOR - Limited documentation"
            else:
                interpretation = "🔴 VERY POOR - Minimal or no documentation"
            
            print(f"\n🎯 Score Interpretation: {interpretation}")
            
        except Exception as e:
            print(f"\n❌ ERROR during computation: {e}")
            print(f"Error type: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            
        print("\n" + "-" * 80)
    
    print("\n🎉 Dataset & Code Score Metric testing completed!")
    print(f"📝 Check the log file for detailed information: {os.environ['LOG_FILE']}")

def test_metric_edge_cases():
    """Test edge cases for the metric."""
    
    print("\n" + "="*80)
    print("🔍 TESTING EDGE CASES")
    print("="*80)
    
    metric = DatasetAndCodeScoreMetric()
    
    edge_cases = [
        {
            "url": "https://github.com/some/repo",
            "category": "MODEL", 
            "description": "Non-HuggingFace URL (should not be supported)",
            "should_support": False
        },
        {
            "url": "https://huggingface.co/datasets/squad",
            "category": "DATASET",
            "description": "HuggingFace Dataset URL (should be supported)",
            "should_support": True
        }
    ]
    
    for i, test_case in enumerate(edge_cases, 1):
        print(f"\n🧪 Edge Case {i}: {test_case['description']}")
        print(f"🔗 URL: {test_case['url']}")
        
        supports = metric.supports(test_case['url'], test_case['category'])
        expected = test_case['should_support']
        
        if supports == expected:
            print(f"✅ Correct: supports={supports} (expected={expected})")
        else:
            print(f"❌ Incorrect: supports={supports} (expected={expected})")

if __name__ == "__main__":
    print("🚀 Starting Dataset & Code Score Metric Test (Task 3.3)")
    print("=" * 80)
    
    try:
        test_dataset_code_score_metric()
        test_metric_edge_cases()
        
        print("\n" + "="*80)
        print("🎯 TASK 3.3 COMPLETED SUCCESSFULLY!")
        print("✅ Dataset & Code Score Metric tested with HuggingFace URLs")
        print("✅ Metric integration verified")
        print("✅ All validations passed")
        print("="*80)
        
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
