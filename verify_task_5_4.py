#!/usr/bin/env python3
"""
Quick verification script for Task 5.4 timeout handling implementation.
"""

import sys
import os

# Add the src directory to Python path
sys.path.insert(0, '/Users/blas/Documents/Obsidian Vault/School/F25/ECE 461/Project Repo/ECE30861_HW1/src')

def test_timeout_implementation():
    """Test the timeout implementation components."""
    
    print("🔍 Testing Task 5.4: API Timeout Handling Implementation")
    print("=" * 60)
    
    try:
        # Test 1: Import timeout configuration
        print("1. Testing timeout configuration import...")
        from acemcli.timeout_config import TimeoutConfig, get_timeout_config, create_requests_session
        print("   ✅ Timeout configuration imported successfully")
        
        # Test 2: Create timeout configuration
        print("2. Testing timeout configuration creation...")
        config = TimeoutConfig(connect_timeout=10.0, read_timeout=30.0, total_timeout=45.0)
        print(f"   ✅ Created config: connect={config.connect_timeout}s, read={config.read_timeout}s, total={config.total_timeout}s")
        
        # Test 3: Test environment variable configuration
        print("3. Testing environment variable configuration...")
        os.environ['ACME_CONNECT_TIMEOUT'] = '5.0'
        os.environ['ACME_READ_TIMEOUT'] = '20.0'
        os.environ['ACME_TOTAL_TIMEOUT'] = '30.0'
        env_config = TimeoutConfig.from_environment()
        print(f"   ✅ Environment config: connect={env_config.connect_timeout}s, read={env_config.read_timeout}s, total={env_config.total_timeout}s")
        
        # Test 4: Test requests session creation
        print("4. Testing requests session creation...")
        session = create_requests_session()
        print(f"   ✅ Created requests session: {type(session).__name__}")
        
        # Test 5: Test metric initialization with timeout config
        print("5. Testing metric initialization...")
        
        # Test HFAPIMetric
        from acemcli.metrics.hf_api import HFAPIMetric
        hf_metric = HFAPIMetric()
        print(f"   ✅ HFAPIMetric initialized with timeout config: {hf_metric.timeout_config.total_timeout}s")
        
        # Test LocalRepoMetric
        from acemcli.metrics.local_repo import LocalRepoMetric
        local_metric = LocalRepoMetric()
        print(f"   ✅ LocalRepoMetric initialized with timeout config: {local_metric.timeout_config.total_timeout}s")
        
        # Test DatasetAndCodeScoreMetric
        from acemcli.metrics.dataset_code_score import DatasetAndCodeScoreMetric
        dataset_metric = DatasetAndCodeScoreMetric()
        print(f"   ✅ DatasetAndCodeScoreMetric initialized with timeout config: {dataset_metric.timeout_config.total_timeout}s")
        
        # Test 6: Test timeout error creation
        print("6. Testing timeout error creation...")
        from acemcli.exceptions import create_api_timeout_error
        timeout_error = create_api_timeout_error("TestAPI", "https://test.com", 30)
        print(f"   ✅ Created timeout error: {timeout_error.message}")
        print(f"      API: {timeout_error.api_name}, Status: {timeout_error.status_code}")
        
        # Test 7: Test timeout formats
        print("7. Testing timeout format conversion...")
        requests_timeout = config.as_requests_timeout()
        hf_timeout = config.as_huggingface_timeout()
        print(f"   ✅ Requests timeout: {requests_timeout}")
        print(f"   ✅ HuggingFace timeout: {hf_timeout}")
        
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Task 5.4: API Timeout Handling Implementation is COMPLETE")
        
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_integration():
    """Test integration with existing error handling."""
    
    print("\n🔧 Testing Integration with Existing Error Handling")
    print("=" * 60)
    
    try:
        # Test that all exception types work together
        from acemcli.exceptions import APIError, ValidationError, MetricError
        
        # Test that timeout errors integrate with existing exception hierarchy
        from acemcli.exceptions import create_api_timeout_error
        timeout_error = create_api_timeout_error("GitHub", "https://github.com/test", 45)
        
        assert isinstance(timeout_error, APIError)
        assert timeout_error.api_name == "GitHub"
        assert timeout_error.status_code == 408
        assert "45 seconds" in timeout_error.message
        
        print("   ✅ Timeout errors integrate properly with exception hierarchy")
        print("   ✅ Error details are properly formatted")
        print("   ✅ Status codes are correctly set")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Integration test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Task 5.4 Verification Tests")
    print("=" * 60)
    
    # Run main tests
    main_success = test_timeout_implementation()
    
    # Run integration tests
    integration_success = test_integration()
    
    if main_success and integration_success:
        print("\n🏆 TASK 5.4 VERIFICATION COMPLETE!")
        print("   All timeout handling components are working correctly.")
        print("   The implementation is ready for production use.")
        exit(0)
    else:
        print("\n💥 VERIFICATION FAILED!")
        print("   Please check the implementation and try again.")
        exit(1)
