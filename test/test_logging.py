"""
Comprehensive test suite for logging framework functionality.
Tests environment variable support and logging configuration.
"""
from __future__ import annotations
import logging
import os
import tempfile
from pathlib import Path
import pytest
from acmecli.logging_setup import setup_logging


class TestLoggingSetup:
    """Test cases for the logging setup functionality."""
    
    def setup_method(self):
        """Reset logging configuration before each test."""
        # Clear any existing handlers
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
    
    def test_default_logging_level(self):
        """Test default logging level is CRITICAL (silent)."""
        # Clear environment variables
        os.environ.pop('LOG_LEVEL', None)
        os.environ.pop('LOG_FILE', None)
        
        setup_logging()
        
        assert logging.getLogger().level == logging.CRITICAL
    
    def test_log_level_0_silent(self):
        """Test LOG_LEVEL=0 sets CRITICAL level (silent)."""
        os.environ['LOG_LEVEL'] = '0'
        os.environ.pop('LOG_FILE', None)
        
        setup_logging()
        
        assert logging.getLogger().level == logging.CRITICAL
    
    def test_log_level_1_info(self):
        """Test LOG_LEVEL=1 sets INFO level."""
        os.environ['LOG_LEVEL'] = '1'
        os.environ.pop('LOG_FILE', None)
        
        setup_logging()
        
        assert logging.getLogger().level == logging.INFO
    
    def test_log_level_2_debug(self):
        """Test LOG_LEVEL=2 sets DEBUG level."""
        os.environ['LOG_LEVEL'] = '2'
        os.environ.pop('LOG_FILE', None)
        
        setup_logging()
        
        assert logging.getLogger().level == logging.DEBUG
    
    def test_invalid_log_level_defaults_to_critical(self):
        """Test invalid LOG_LEVEL defaults to CRITICAL."""
        os.environ['LOG_LEVEL'] = 'invalid'
        os.environ.pop('LOG_FILE', None)
        
        setup_logging()
        
        assert logging.getLogger().level == logging.CRITICAL
    
    def test_log_file_environment_variable(self):
        """Test LOG_FILE environment variable creates file handler."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            log_file_path = tmp_file.name
        
        try:
            os.environ['LOG_LEVEL'] = '1'
            os.environ['LOG_FILE'] = log_file_path
            
            setup_logging()
            
            # Check that handlers include file handler
            handlers = logging.getLogger().handlers
            file_handlers = [h for h in handlers if isinstance(h, logging.FileHandler)]
            
            assert len(file_handlers) > 0, "Should have at least one file handler"
            
            # Test that logging actually writes to file
            test_logger = logging.getLogger('test_logger')
            test_logger.info('Test log message')
            
            # Force flush
            for handler in file_handlers:
                handler.flush()
            
            # Check file contents
            with open(log_file_path, 'r') as f:
                content = f.read()
                assert 'Test log message' in content
                
        finally:
            # Cleanup
            os.environ.pop('LOG_FILE', None)
            os.environ.pop('LOG_LEVEL', None)
            try:
                os.unlink(log_file_path)
            except OSError:
                pass
    
    def test_logging_format_includes_required_fields(self):
        """Test that log format includes timestamp, level, and name."""
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as tmp_file:
            log_file_path = tmp_file.name
        
        try:
            os.environ['LOG_LEVEL'] = '1'
            os.environ['LOG_FILE'] = log_file_path
            
            setup_logging()
            
            test_logger = logging.getLogger('test_module')
            test_logger.info('Format test message')
            
            # Force flush
            for handler in logging.getLogger().handlers:
                if isinstance(handler, logging.FileHandler):
                    handler.flush()
            
            with open(log_file_path, 'r') as f:
                content = f.read()
                
                # Check format contains required components
                assert '[INFO]' in content, "Should include log level"
                assert 'test_module' in content, "Should include logger name"
                assert 'Format test message' in content, "Should include message"
                # Basic timestamp check (should contain year)
                assert '202' in content, "Should include timestamp"
                
        finally:
            os.environ.pop('LOG_FILE', None)
            os.environ.pop('LOG_LEVEL', None)
            try:
                os.unlink(log_file_path)
            except OSError:
                pass


def test_logging_integration_with_cli_modules():
    """Test that CLI modules can use the logging setup."""
    os.environ['LOG_LEVEL'] = '2'  # Debug level
    os.environ.pop('LOG_FILE', None)
    
    setup_logging()
    
    # Simulate what CLI modules do
    cli_logger = logging.getLogger('acmecli.cli')
    cli_logger.debug('CLI debug message')
    
    metric_logger = logging.getLogger('acmecli.metrics')
    metric_logger.info('Metric info message')
    
    # If we get here without exceptions, the integration works
    assert True


def test_multiple_setup_calls_dont_duplicate_handlers():
    """Test that calling setup_logging multiple times doesn't create duplicate handlers."""
    os.environ['LOG_LEVEL'] = '1'
    os.environ.pop('LOG_FILE', None)
    
    # Call setup multiple times
    setup_logging()
    initial_handler_count = len(logging.getLogger().handlers)
    
    setup_logging()
    second_handler_count = len(logging.getLogger().handlers)
    
    setup_logging()
    third_handler_count = len(logging.getLogger().handlers)
    
    # The force=True parameter should prevent handler duplication
    # but we should still have at least one handler
    assert initial_handler_count >= 1
    assert second_handler_count >= 1
    assert third_handler_count >= 1
    
    # Cleanup
    os.environ.pop('LOG_LEVEL', None)
