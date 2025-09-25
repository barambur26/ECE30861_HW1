"""
Test suite for Performance Claims metric functionality.
"""
from __future__ import annotations
import tempfile
from pathlib import Path
import pytest
from acemcli.metrics.performance_claims import PerformanceClaimsMetric


class TestPerformanceClaimsMetric:
    """Test cases for the Performance Claims metric."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.metric = PerformanceClaimsMetric()
    
    def test_metric_name(self):
        """Test that metric has correct name."""
        assert self.metric.name == "performance_claims"
    
    def test_supports_huggingface_model_urls(self):
        """Test that metric supports HuggingFace model URLs."""
        model_url = "https://huggingface.co/google/gemma-3-270m"
        assert self.metric.supports(model_url, "MODEL") is True
    
    def test_does_not_support_non_model_categories(self):
        """Test that metric only supports MODEL category."""
        hf_url = "https://huggingface.co/google/gemma-3-270m"
        assert self.metric.supports(hf_url, "DATASET") is False
        assert self.metric.supports(hf_url, "CODE") is False
    
    def test_does_not_support_non_huggingface_urls(self):
        """Test that metric doesn't support non-HuggingFace URLs."""
        github_url = "https://github.com/example/repo"
        assert self.metric.supports(github_url, "MODEL") is False
    
    def test_has_quantitative_results_detects_percentages(self):
        """Test detection of percentage values."""
        content = "Our model achieves 95.2% accuracy on the test set."
        assert self.metric._has_quantitative_results(content) is True
    
    def test_has_quantitative_results_detects_metrics(self):
        """Test detection of common evaluation metrics."""
        content = "F1 score: 0.89, BLEU: 32.1, accuracy 0.95"
        assert self.metric._has_quantitative_results(content) is True
    
    def test_has_quantitative_results_detects_performance_metrics(self):
        """Test detection of performance timing metrics."""
        content = "Inference speed: 150 fps, latency: 6.7ms"
        assert self.metric._has_quantitative_results(content) is True
    
    def test_has_quantitative_results_detects_model_size(self):
        """Test detection of model size metrics."""
        content = "7B parameters, 13.2 GFLOPS"
        assert self.metric._has_quantitative_results(content) is True
    
    def test_has_quantitative_results_returns_false_for_no_metrics(self):
        """Test that no metrics returns False."""
        content = "This is a great model with excellent performance."
        assert self.metric._has_quantitative_results(content) is False
    
    def test_has_comparison_table_detects_markdown_tables(self):
        """Test detection of markdown comparison tables."""
        content = """
        | Model | Accuracy | F1-Score |
        |-------|----------|----------|
        | Ours  | 95.2%    | 0.89     |
        | Baseline | 92.1% | 0.85     |
        """
        assert self.metric._has_comparison_table(content) is True
    
    def test_has_comparison_table_returns_false_for_no_tables(self):
        """Test that no tables returns False."""
        content = "Our model is better than the baseline."
        assert self.metric._has_comparison_table(content) is False
    
    def test_has_comparison_table_returns_false_for_non_numerical_tables(self):
        """Test that tables without numbers return False."""
        content = """
        | Feature | Status |
        |---------|--------|
        | GPU     | Yes    |
        | CPU     | No     |
        """
        assert self.metric._has_comparison_table(content) is False
    
    def test_extract_performance_content_finds_sections(self):
        """Test extraction of performance content from documentation."""
        content = """
        # Model Description
        This is a great model.
        
        ## Performance
        Our model achieves 95% accuracy.
        It also has fast inference.
        
        ## Usage
        Use it like this.
        """
        
        performance_content = self.metric._extract_performance_content(content)
        assert "Our model achieves 95% accuracy" in performance_content
        assert "It also has fast inference" in performance_content
        assert "Use it like this" not in performance_content
    
    def test_analyze_benchmark_results_with_no_files(self):
        """Test benchmark analysis with no relevant files."""
        files = [Path("README.md"), Path("config.json")]
        score = self.metric._analyze_benchmark_results(files)
        assert score == 0.0
    
    def test_analyze_evaluation_metrics_empty_files(self):
        """Test evaluation metrics analysis with empty file list."""
        files = []
        score = self.metric._analyze_evaluation_metrics(files)
        assert score == 0.0
    
    def test_analyze_comparison_tables_empty_files(self):
        """Test comparison tables analysis with empty file list."""
        files = []
        score = self.metric._analyze_comparison_tables(files)
        assert score == 0.0
    
    def test_analyze_performance_docs_empty_files(self):
        """Test performance docs analysis with empty file list.""" 
        files = []
        score = self.metric._analyze_performance_docs(files)
        assert score == 0.0
    
    def test_analyze_credibility_empty_files(self):
        """Test credibility analysis with empty file list."""
        files = []
        score = self.metric._analyze_credibility(files)
        assert score == 0.0
    
    def test_analyze_performance_claims_with_mock_repo(self):
        """Test full performance claims analysis with mock repository."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_path = Path(tmp_dir)
            
            # Create a mock README with performance claims
            readme_content = """
            # Awesome Model
            
            ## Performance
            Our model achieves 95.2% accuracy on GLUE benchmark.
            
            | Model | Accuracy | F1-Score |
            |-------|----------|----------|
            | Ours  | 95.2%    | 0.89     |
            | BERT  | 92.1%    | 0.85     |
            
            Reference: https://arxiv.org/abs/2023.12345
            """
            
            readme_file = repo_path / "README.md"
            readme_file.write_text(readme_content)
            
            # Create mock evaluation results
            results_content = '{"accuracy": 0.952, "f1_score": 0.89}'
            results_file = repo_path / "eval_results.json"
            results_file.write_text(results_content)
            
            score = self.metric._analyze_performance_claims(repo_path)
            
            # Should get a positive score for having performance claims
            assert score > 0.0
            assert score <= 1.0


def test_performance_claims_metric_returns_valid_score_and_latency():
    """Test that compute method returns valid score and latency format."""
    metric = PerformanceClaimsMetric()
    
    # This will fail to download but should return 0.0 score gracefully
    score, latency = metric.compute("https://huggingface.co/nonexistent/model", "MODEL")
    
    assert isinstance(score, float)
    assert 0.0 <= score <= 1.0
    assert isinstance(latency, int)
    assert latency >= 0
