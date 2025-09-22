"""
Test suite for Dataset & Code Score metric functionality.
"""
from __future__ import annotations
import tempfile
from pathlib import Path
import pytest
from acmecli.metrics.dataset_code_score import DatasetAndCodeScoreMetric


class TestDatasetAndCodeScoreMetric:
    """Test cases for the Dataset & Code Score metric."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.metric = DatasetAndCodeScoreMetric()
    
    def test_metric_name(self):
        """Test that metric has correct name."""
        assert self.metric.name == "dataset_and_code_score"
    
    def test_supports_huggingface_model_urls(self):
        """Test that metric supports HuggingFace model URLs."""
        model_url = "https://huggingface.co/google/gemma-3-270m"
        assert self.metric.supports(model_url, "MODEL") is True
    
    def test_supports_huggingface_dataset_urls(self):
        """Test that metric supports HuggingFace dataset URLs."""
        dataset_url = "https://huggingface.co/datasets/squad"
        assert self.metric.supports(dataset_url, "DATASET") is True
    
    def test_does_not_support_code_category(self):
        """Test that metric doesn't support CODE category."""
        hf_url = "https://huggingface.co/google/gemma-3-270m"
        assert self.metric.supports(hf_url, "CODE") is False
    
    def test_does_not_support_non_huggingface_urls(self):
        """Test that metric doesn't support non-HuggingFace URLs."""
        github_url = "https://github.com/example/repo"
        assert self.metric.supports(github_url, "MODEL") is False
    
    def test_score_readme_content_dataset_indicators(self):
        """Test scoring of README content with dataset indicators."""
        content = """
        # Model Training
        
        This model was trained on a large dataset with careful data collection.
        The training data includes annotations and labels from multiple sources.
        We used a corpus of text with validation set for evaluation.
        """
        
        score = self.metric._score_readme_content(content)
        assert score > 0.0
        assert score <= 1.0
    
    def test_score_readme_content_code_indicators(self):
        """Test scoring of README content with code indicators."""
        content = """
        # Usage Example
        
        Here's a quickstart tutorial showing how to use this model.
        Check out our sample code and demonstration scripts.
        See the Jupyter notebook for a complete example.
        """
        
        score = self.metric._score_readme_content(content)
        assert score > 0.0
        assert score <= 1.0
    
    def test_score_readme_content_structured_sections(self):
        """Test scoring of README content with structured sections."""
        content = """
        ## Dataset Information
        Our training dataset is carefully curated.
        
        ## Usage Instructions  
        Follow these steps to use the model.
        
        ## Training Details
        Model was trained with these parameters.
        """
        
        score = self.metric._score_readme_content(content)
        assert score > 0.0
        assert score <= 1.0
    
    def test_score_readme_content_external_links(self):
        """Test scoring of README content with external links."""
        content = """
        # Model Details
        
        Dataset: https://huggingface.co/datasets/squad
        Code: https://github.com/example/training-scripts
        Additional data: https://example.com/dataset-info
        """
        
        score = self.metric._score_readme_content(content)
        assert score > 0.0
        assert score <= 1.0
    
    def test_score_readme_content_technical_details(self):
        """Test scoring of README content with technical details."""
        content = """
        # Technical Specifications
        
        Architecture: Transformer with 7B parameters
        Training: 100 epochs with Adam optimizer
        Batch size: 32, learning rate: 1e-4
        Evaluation metrics: accuracy, F1-score
        Performance: 95% accuracy on test set
        """
        
        score = self.metric._score_readme_content(content)
        assert score > 0.0
        assert score <= 1.0
    
    def test_score_readme_content_empty_returns_zero(self):
        """Test that empty content returns zero score."""
        content = ""
        score = self.metric._score_readme_content(content)
        assert score == 0.0
    
    def test_has_comprehensive_dataset_info_positive(self):
        """Test detection of comprehensive dataset information."""
        content = """
        {
            "description": "A large dataset for NLP tasks",
            "source": "Wikipedia and Common Crawl", 
            "size": "10GB",
            "format": "JSON",
            "license": "MIT"
        }
        """
        
        assert self.metric._has_comprehensive_dataset_info(content) is True
    
    def test_has_comprehensive_dataset_info_insufficient(self):
        """Test detection when dataset info is insufficient."""
        content = """
        {
            "description": "A dataset",
            "size": "1GB"
        }
        """
        
        assert self.metric._has_comprehensive_dataset_info(content) is False
    
    def test_analyze_readme_files_with_no_files(self):
        """Test README analysis with no README files."""
        files = [Path("config.json"), Path("model.bin")]
        score = self.metric._analyze_readme_files(files)
        assert score == 0.0
    
    def test_analyze_dataset_documentation_with_no_files(self):
        """Test dataset documentation analysis with no relevant files."""
        files = [Path("README.md"), Path("config.json")]
        score = self.metric._analyze_dataset_documentation(files)
        assert score == 0.0
    
    def test_analyze_example_code_with_no_files(self):
        """Test example code analysis with no code files."""
        files = [Path("README.md"), Path("config.json")]
        score = self.metric._analyze_example_code(files)
        assert score == 0.0
    
    def test_analyze_dataset_links_with_no_files(self):
        """Test dataset links analysis with no documentation files."""
        files = [Path("model.bin"), Path("config.json")]
        score = self.metric._analyze_dataset_links(files)
        assert score == 0.0
    
    def test_analyze_training_scripts_with_no_files(self):
        """Test training scripts analysis with no script files."""
        files = [Path("README.md"), Path("config.json")]
        score = self.metric._analyze_training_scripts(files)
        assert score == 0.0
    
    def test_get_weights_for_model_category(self):
        """Test that weights are returned for MODEL category."""
        weights = self.metric._get_weights_for_category("MODEL")
        
        assert isinstance(weights, dict)
        assert len(weights) == 5
        assert all(isinstance(w, float) for w in weights.values())
        assert abs(sum(weights.values()) - 1.0) < 0.01  # Should sum to ~1.0
    
    def test_get_weights_for_dataset_category(self):
        """Test that weights are returned for DATASET category."""
        weights = self.metric._get_weights_for_category("DATASET")
        
        assert isinstance(weights, dict)
        assert len(weights) == 5
        assert abs(sum(weights.values()) - 1.0) < 0.01
    
    def test_get_weights_for_code_category(self):
        """Test that weights are returned for CODE category."""
        weights = self.metric._get_weights_for_category("CODE")
        
        assert isinstance(weights, dict) 
        assert len(weights) == 5
        assert abs(sum(weights.values()) - 1.0) < 0.01
    
    def test_analyze_repository_with_mock_files(self):
        """Test full repository analysis with mock files."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_path = Path(tmp_dir)
            
            # Create mock README
            readme_content = """
            # Great Model
            
            ## Dataset
            This model was trained on a high-quality dataset with careful curation.
            
            ## Example Usage
            ```python
            from model import GreatModel
            model = GreatModel()
            ```
            
            Dataset: https://huggingface.co/datasets/example
            """
            
            readme_file = repo_path / "README.md"
            readme_file.write_text(readme_content)
            
            # Create example notebook
            notebook_file = repo_path / "example.ipynb"
            notebook_file.write_text('{"cells": []}')
            
            # Create dataset info
            dataset_info = '{"description": "A dataset", "source": "web", "size": "1GB", "format": "json", "license": "MIT"}'
            dataset_file = repo_path / "dataset_info.json" 
            dataset_file.write_text(dataset_info)
            
            score = self.metric._analyze_repository(repo_path, "MODEL")
            
            assert isinstance(score, float)
            assert 0.0 <= score <= 1.0
            assert score > 0.0  # Should have some positive score


def test_dataset_code_score_metric_returns_valid_score_and_latency():
    """Test that compute method returns valid score and latency format."""
    metric = DatasetAndCodeScoreMetric()
    
    # This will fail to download but should return 0.0 score gracefully
    score, latency = metric.compute("https://huggingface.co/nonexistent/model", "MODEL")
    
    assert isinstance(score, float)
    assert 0.0 <= score <= 1.0
    assert isinstance(latency, int)
    assert latency >= 0
