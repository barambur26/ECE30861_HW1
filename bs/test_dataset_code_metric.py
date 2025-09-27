#!/usr/bin/env python3
"""
Test script for Dataset & Code Score Metric (Task 3.3)
Tests the metric with a HuggingFace URL to verify it works correctly.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import time
from acemcli.logging_setup import setup_logging
from acemcli.metrics.dataset_code_score import DatasetAndCodeScoreMetric
from acemcli.models import Category

def test_dataset_code_score_metric():
    """Test the dataset and code score metric with a real HuggingFace URL."""
    
    # Set up logging
    setup_logging()
    
    print("=" * 60)
    print("🚀 TESTING DATASET & CODE SCORE METRIC (Task 3.3)")
    print("=" * 60)
    
    # Initialize the metric
    metric = DatasetAndCodeScoreMetric()
    print(f"✅ Metric initialized: {metric.name}")
    
    # Test URL - using a well-documented HuggingFace model
    test_urls = [
        ("https://huggingface.co/google/gemma-2b", "MODEL"),
        ("https://huggingface.co/bert-base-uncased", "MODEL"),
    ]
    
    for url, category in test_urls:
        print(f"\n📊 Testing URL: {url}")
        print(f"📂 Category: {category}")
        
        # Check if metric supports this URL
        supports = metric.supports(url, category)
        print(f"🔧 Supports URL: {supports}")
        
        if not supports:
            print("❌ Metric doesn't support this URL, skipping...")
            continue
            
        # Measure execution time
        start_time = time.time()
        
        try:
            # Compute the metric
            result = metric.compute(url, category)
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            print(f"\n📈 RESULTS:")
            print(f"   Repository: {result.name}")
            print(f"   Category: {result.category}")
            print(f"   Dataset & Code Score: {result.dataset_and_code_score:.3f}")
            print(f"   Score Latency (reported): {result.dataset_and_code_score_latency} ms")
            print(f"   Actual Execution Time: {execution_time:.2f} seconds")
            
            # Validation checks
            print(f"\n🔍 VALIDATION:")
            
            # Check score range
            score_valid = 0.0 <= result.dataset_and_code_score <= 1.0
            print(f"   Score in [0,1] range: {'✅' if score_valid else '❌'} ({result.dataset_and_code_score})")
            
            # Check latency is positive
            latency_valid = result.dataset_and_code_score_latency > 0
            print(f"   Latency > 0: {'✅' if latency_valid else '❌'} ({result.dataset_and_code_score_latency} ms)")
            
            # Check result type
            from acemcli.models import MetricResult
            result_type_valid = isinstance(result, MetricResult)
            print(f"   Returns MetricResult: {'✅' if result_type_valid else '❌'}")
            
            # Check category matches
            category_valid = result.category == category
            print(f"   Category matches: {'✅' if category_valid else '❌'} ({result.category})")
            
            # Overall validation
            all_valid = score_valid and latency_valid and result_type_valid and category_valid
            print(f"\n🎯 OVERALL: {'✅ PASSED' if all_valid else '❌ FAILED'}")
            
            if all_valid:
                print(f"   The metric works correctly!")
                print(f"   Dataset & Code Score: {result.dataset_and_code_score:.3f}/1.0")
                if result.dataset_and_code_score > 0.5:
                    print(f"   🏆 Good score - repository has decent dataset/code documentation!")
                elif result.dataset_and_code_score > 0.2:
                    print(f"   📝 Moderate score - some documentation present")
                else:
                    print(f"   📋 Low score - limited dataset/code documentation")
                    
        except Exception as e:
            print(f"❌ ERROR computing metric: {e}")
            import traceback
            traceback.print_exc()
            
        print("\n" + "-" * 60)

if __name__ == "__main__":
    test_dataset_code_score_metric()
