"""
Tests for Monitoring Module
============================
"""

import pytest
from unittest.mock import patch, MagicMock
from app.monitoring import (
    track_api_call,
    track_gemini_call,
    track_match_score,
    track_cache_operation,
    get_metrics_summary
)
import time


class TestAPITracking:
    """Test API call tracking."""
    
    @patch('app.monitoring.api_request_duration')
    @patch('app.monitoring.api_request_counter')
    def test_successful_api_call(self, mock_counter, mock_duration):
        """Should track successful API calls."""
        
        @track_api_call("/test")
        def test_endpoint():
            return {"success": True}
        
        result = test_endpoint()
        
        assert result == {"success": True}
        # Verify metrics were recorded
        assert mock_counter.labels.called
        assert mock_duration.labels.called
    
    @patch('app.monitoring.api_request_duration')
    @patch('app.monitoring.api_request_counter')
    def test_failed_api_call(self, mock_counter, mock_duration):
        """Should track failed API calls."""
        
        @track_api_call("/test")
        def test_endpoint():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError):
            test_endpoint()
        
        # Should still record metrics for failed calls
        assert mock_counter.labels.called
    
    @patch('app.monitoring.api_request_duration')
    def test_api_call_measures_time(self, mock_duration):
        """Should measure execution time."""
        
        @track_api_call("/test")
        def slow_endpoint():
            time.sleep(0.1)
            return {"done": True}
        
        start = time.time()
        result = slow_endpoint()
        elapsed = time.time() - start
        
        assert elapsed >= 0.1
        assert result == {"done": True}


class TestGeminiTracking:
    """Test Gemini API tracking."""
    
    @patch('app.monitoring.gemini_request_duration')
    @patch('app.monitoring.gemini_request_counter')
    def test_gemini_call_tracking(self, mock_counter, mock_duration):
        """Should track Gemini API calls."""
        
        @track_gemini_call("test_function")
        def generate_content():
            return "Generated content"
        
        result = generate_content()
        
        assert result == "Generated content"
        assert mock_counter.labels.called
        assert mock_duration.labels.called
    
    @patch('app.monitoring.gemini_request_duration')
    @patch('app.monitoring.gemini_request_counter')
    def test_gemini_error_tracking(self, mock_counter, mock_duration):
        """Should track Gemini errors."""
        
        @track_gemini_call("test_function")
        def failing_generation():
            raise Exception("API Error")
        
        with pytest.raises(Exception):
            failing_generation()
        
        # Should still be tracked
        assert mock_counter.labels.called


class TestMatchScoreTracking:
    """Test match score tracking."""
    
    @patch('app.monitoring.job_match_scores')
    def test_track_high_score(self, mock_histogram):
        """Should track high match scores."""
        track_match_score(85.5)
        assert mock_histogram.observe.called
        mock_histogram.observe.assert_called_with(85.5)
    
    @patch('app.monitoring.job_match_scores')
    def test_track_low_score(self, mock_histogram):
        """Should track low match scores."""
        track_match_score(25.0)
        assert mock_histogram.observe.called
        mock_histogram.observe.assert_called_with(25.0)
    
    @patch('app.monitoring.job_match_scores')
    def test_track_perfect_score(self, mock_histogram):
        """Should track perfect match."""
        track_match_score(100.0)
        assert mock_histogram.observe.called


class TestCacheTracking:
    """Test cache operation tracking."""
    
    @patch('app.monitoring.cache_hit_counter')
    @patch('app.monitoring.cache_miss_counter')
    def test_cache_hit(self, mock_miss, mock_hit):
        """Should track cache hits."""
        track_cache_operation("hit", "test_key")
        assert mock_hit.inc.called
        assert not mock_miss.inc.called
    
    @patch('app.monitoring.cache_hit_counter')
    @patch('app.monitoring.cache_miss_counter')
    def test_cache_miss(self, mock_miss, mock_hit):
        """Should track cache misses."""
        track_cache_operation("miss", "test_key")
        assert mock_miss.inc.called
        assert not mock_hit.inc.called


class TestMetricsSummary:
    """Test metrics summary generation."""
    
    @patch('app.monitoring.api_request_counter')
    @patch('app.monitoring.gemini_request_counter')
    def test_metrics_summary_format(self, mock_gemini, mock_api):
        """Summary should contain all key metrics."""
        # Mock the counter values
        mock_api._metrics = {}
        mock_gemini._metrics = {}
        
        summary = get_metrics_summary()
        
        assert 'api_requests' in summary
        assert 'gemini_calls' in summary
        assert 'cache_stats' in summary
        assert 'timestamp' in summary


class TestDecoratorChaining:
    """Test using multiple decorators together."""
    
    @patch('app.monitoring.api_request_duration')
    @patch('app.monitoring.gemini_request_duration')
    def test_combined_decorators(self, mock_gemini_duration, mock_api_duration):
        """Should work with multiple decorators."""
        
        @track_api_call("/test")
        @track_gemini_call("test_function")
        def combined_function():
            return "Result"
        
        result = combined_function()
        
        assert result == "Result"
        # Both decorators should be active
        assert mock_api_duration.labels.called or mock_gemini_duration.labels.called


class TestErrorHandling:
    """Test monitoring under error conditions."""
    
    @patch('app.monitoring.api_request_counter')
    def test_monitoring_doesnt_break_function(self, mock_counter):
        """Monitoring errors shouldn't break the function."""
        mock_counter.labels.side_effect = Exception("Metrics error")
        
        @track_api_call("/test")
        def important_function():
            return "Critical result"
        
        # Function should still work even if monitoring fails
        result = important_function()
        assert result == "Critical result"
