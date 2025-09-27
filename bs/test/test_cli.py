"""
Comprehensive test suite for CLI functionality.
"""
from __future__ import annotations
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch
from acemcli.cli import infer_category, main


class TestInferCategory:
    """Test cases for URL category inference."""
    
    def test_infer_category_model(self):
        """Test HuggingFace model URL categorization."""
        assert infer_category("https://huggingface.co/google/gemma-3-270m") == "MODEL"
    
    def test_infer_category_model_with_trailing_slash(self):
        """Test model URL with trailing slash."""
        assert infer_category("https://huggingface.co/google/gemma-3-270m/") == "MODEL"
    
    def test_infer_category_dataset(self):
        """Test dataset URL categorization."""
        assert infer_category("https://huggingface.co/datasets/squad") == "DATASET"
    
    def test_infer_category_dataset_with_complex_path(self):
        """Test dataset URL with complex path."""
        assert infer_category("https://huggingface.co/datasets/microsoft/DialoGPT-large") == "DATASET"
    
    def test_infer_category_code_github(self):
        """Test GitHub URL categorization as CODE."""
        assert infer_category("https://github.com/example/repo") == "CODE"
    
    def test_infer_category_code_other_url(self):
        """Test other URLs categorized as CODE."""
        assert infer_category("https://example.com/some/code") == "CODE"
    
    def test_infer_category_code_local_path(self):
        """Test local path categorized as CODE.""" 
        assert infer_category("/path/to/local/repo") == "CODE"


class TestMainFunction:
    """Test cases for the main CLI function."""
    
    def test_main_with_nonexistent_file(self):
        """Test main function with non-existent file."""
        result = main("/nonexistent/file.txt")
        assert result == 1  # Should return error code
    
    def test_main_with_relative_path(self):
        """Test main function with relative path (should fail)."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp_file:
            tmp_file.write("https://huggingface.co/google/gemma-3-270m\n")
            tmp_file_path = tmp_file.name
        
        try:
            # Use relative path (should fail)
            relative_path = Path(tmp_file_path).name
            result = main(relative_path)
            assert result == 1
        finally:
            try:
                Path(tmp_file_path).unlink()
            except OSError:
                pass
    
    def test_main_with_empty_file(self):
        """Test main function with empty URL file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp_file:
            tmp_file.write("")  # Empty file
            tmp_file_path = tmp_file.name
        
        try:
            result = main(tmp_file_path)
            # Should complete successfully even with no URLs
            assert result == 0
        finally:
            try:
                Path(tmp_file_path).unlink()
            except OSError:
                pass
    
    def test_main_with_mixed_url_types_filters_to_models_only(self):
        """Test that main function only processes MODEL URLs."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp_file:
            tmp_file.write(
                "https://huggingface.co/google/gemma-3-270m\n"
                "https://huggingface.co/datasets/squad\n" 
                "https://github.com/example/repo\n"
                "https://huggingface.co/microsoft/DialoGPT-large\n"
            )
            tmp_file_path = tmp_file.name
        
        try:
            # Mock the compute_all function to avoid actual processing
            with patch('acemcli.cli.compute_all') as mock_compute:
                mock_compute.return_value = []  # Return empty results
                
                result = main(tmp_file_path)
                assert result == 0
                
                # Check that only MODEL URLs were passed to compute_all
                args, kwargs = mock_compute.call_args
                passed_pairs = list(args[0])
                
                # Should only have the 2 model URLs
                model_urls = [pair[0] for pair in passed_pairs]
                assert len(model_urls) == 2
                assert "https://huggingface.co/google/gemma-3-270m" in model_urls
                assert "https://huggingface.co/microsoft/DialoGPT-large" in model_urls
                
        finally:
            try:
                Path(tmp_file_path).unlink()
            except OSError:
                pass
    
    def test_main_with_whitespace_and_empty_lines(self):
        """Test main function handles whitespace and empty lines correctly."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp_file:
            tmp_file.write(
                "\n"
                "  https://huggingface.co/google/gemma-3-270m  \n"
                "\n"
                "\t\n"
                " https://huggingface.co/microsoft/DialoGPT-large\n"
                "\n"
            )
            tmp_file_path = tmp_file.name
        
        try:
            with patch('acemcli.cli.compute_all') as mock_compute:
                mock_compute.return_value = []
                
                result = main(tmp_file_path)
                assert result == 0
                
                # Should parse 2 URLs despite whitespace
                args, kwargs = mock_compute.call_args
                passed_pairs = list(args[0])
                assert len(passed_pairs) == 2
                
        finally:
            try:
                Path(tmp_file_path).unlink()
            except OSError:
                pass
    
    @patch('acemcli.cli.compute_all')
    def test_main_handles_compute_exception(self, mock_compute):
        """Test main function handles exceptions from compute_all."""
        mock_compute.side_effect = Exception("Computation failed")
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp_file:
            tmp_file.write("https://huggingface.co/google/gemma-3-270m\n")
            tmp_file_path = tmp_file.name
        
        try:
            result = main(tmp_file_path)
            assert result == 1  # Should return error code
        finally:
            try:
                Path(tmp_file_path).unlink()
            except OSError:
                pass
    
    def test_main_with_file_read_error(self):
        """Test main function with file that can't be read."""
        # Create file and then make it unreadable
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp_file:
            tmp_file.write("https://huggingface.co/google/gemma-3-270m\n")
            tmp_file_path = tmp_file.name
        
        try:
            # Change permissions to make file unreadable (Unix only)
            import os
            import stat
            if hasattr(os, 'chmod'):
                os.chmod(tmp_file_path, stat.S_IWRITE)  # Remove read permission
                
                result = main(tmp_file_path)
                assert result == 1  # Should return error code
        finally:
            try:
                # Restore permissions and cleanup
                if hasattr(os, 'chmod'):
                    os.chmod(tmp_file_path, stat.S_IREAD | stat.S_IWRITE)
                Path(tmp_file_path).unlink()
            except OSError:
                pass


def test_infer_category_edge_cases():
    """Test edge cases for category inference."""
    # Test empty string
    assert infer_category("") == "CODE"
    
    # Test URL with datasets in path but not HuggingFace
    assert infer_category("https://example.com/datasets/something") == "CODE"
    
    # Test HuggingFace URL that's not model or dataset
    assert infer_category("https://huggingface.co/spaces/example") == "MODEL"  # Default HF behavior


def test_main_integration_basic():
    """Basic integration test for main function."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp_file:
        # Use a URL that will likely fail gracefully
        tmp_file.write("https://huggingface.co/test/nonexistent-model\n")
        tmp_file_path = tmp_file.name
    
    try:
        # This should not crash even if the model doesn't exist
        # The actual download will fail but it should be handled gracefully
        result = main(tmp_file_path)
        # Result could be 0 or 1 depending on error handling
        assert result in [0, 1]
    finally:
        try:
            Path(tmp_file_path).unlink()
        except OSError:
            pass
