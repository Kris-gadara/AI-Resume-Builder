"""
Tests for Cache Module
======================
"""

import pytest
from unittest.mock import patch, MagicMock
from app.cache import (
    cached,
    clear_cache,
    get_cache_stats,
    generate_cache_key
)
import time


class TestCacheDecorator:
    """Test caching decorator."""
    
    @patch('app.cache.redis_client')
    def test_cache_miss_executes_function(self, mock_redis):
        """Cache miss should execute the function."""
        mock_redis.get.return_value = None
        
        call_count = [0]
        
        @cached(ttl=3600)
        def expensive_function(x: int) -> int:
            call_count[0] += 1
            return x * 2
        
        result = expensive_function(5)
        
        assert result == 10
        assert call_count[0] == 1
        assert mock_redis.get.called
    
    @patch('app.cache.redis_client')
    def test_cache_hit_skips_function(self, mock_redis):
        """Cache hit should skip function execution."""
        # Mock cached value
        import json
        mock_redis.get.return_value = json.dumps({"result": 10}).encode()
        
        call_count = [0]
        
        @cached(ttl=3600)
        def expensive_function(x: int) -> int:
            call_count[0] += 1
            return x * 2
        
        result = expensive_function(5)
        
        assert result == 10
        assert call_count[0] == 0  # Function not executed
        assert mock_redis.get.called
    
    @patch('app.cache.redis_client')
    def test_cache_stores_result(self, mock_redis):
        """Should store function result in cache."""
        mock_redis.get.return_value = None
        
        @cached(ttl=3600)
        def expensive_function(x: int) -> int:
            return x * 2
        
        result = expensive_function(5)
        
        assert result == 10
        assert mock_redis.setex.called
        # Verify TTL was set
        call_args = mock_redis.setex.call_args
        assert call_args[0][1] == 3600  # TTL
    
    @patch('app.cache.redis_client')
    def test_redis_unavailable_executes_function(self, mock_redis):
        """Should work even if Redis is unavailable."""
        mock_redis.get.side_effect = Exception("Redis down")
        
        @cached(ttl=3600)
        def important_function(x: int) -> int:
            return x * 2
        
        # Should still work
        result = important_function(5)
        assert result == 10
    
    @patch('app.cache.redis_client')
    def test_different_args_different_cache(self, mock_redis):
        """Different arguments should generate different cache keys."""
        mock_redis.get.return_value = None
        
        @cached(ttl=3600)
        def multiply(x: int, y: int) -> int:
            return x * y
        
        result1 = multiply(2, 3)
        result2 = multiply(4, 5)
        
        assert result1 == 6
        assert result2 == 20
        # Should be called with different keys
        assert mock_redis.get.call_count == 2


class TestCacheKeyGeneration:
    """Test cache key generation."""
    
    def test_simple_key_generation(self):
        """Should generate consistent keys."""
        key1 = generate_cache_key("test_func", 1, 2, 3)
        key2 = generate_cache_key("test_func", 1, 2, 3)
        
        assert key1 == key2
    
    def test_different_args_different_keys(self):
        """Different arguments should produce different keys."""
        key1 = generate_cache_key("test_func", 1, 2)
        key2 = generate_cache_key("test_func", 3, 4)
        
        assert key1 != key2
    
    def test_kwargs_in_key(self):
        """Kwargs should be included in key."""
        key1 = generate_cache_key("test_func", x=1, y=2)
        key2 = generate_cache_key("test_func", x=1, y=3)
        
        assert key1 != key2
    
    def test_order_independent_kwargs(self):
        """Kwargs order shouldn't matter."""
        key1 = generate_cache_key("test_func", x=1, y=2)
        key2 = generate_cache_key("test_func", y=2, x=1)
        
        assert key1 == key2


class TestCacheManagement:
    """Test cache management operations."""
    
    @patch('app.cache.redis_client')
    def test_clear_cache(self, mock_redis):
        """Should clear all cached values."""
        mock_redis.keys.return_value = [b'cache:key1', b'cache:key2']
        
        clear_cache()
        
        assert mock_redis.delete.called
    
    @patch('app.cache.redis_client')
    def test_clear_specific_pattern(self, mock_redis):
        """Should clear cache matching specific pattern."""
        mock_redis.keys.return_value = [b'cache:test_func:*']
        
        clear_cache(pattern="test_func")
        
        assert mock_redis.keys.called
        assert mock_redis.delete.called
    
    @patch('app.cache.redis_client')
    def test_get_cache_stats(self, mock_redis):
        """Should return cache statistics."""
        mock_redis.dbsize.return_value = 42
        mock_redis.info.return_value = {
            'used_memory_human': '10M',
            'keyspace_hits': '1000',
            'keyspace_misses': '200'
        }
        
        stats = get_cache_stats()
        
        assert 'total_keys' in stats
        assert 'memory_used' in stats
        assert stats['total_keys'] == 42


class TestCacheTTL:
    """Test TTL (Time To Live) functionality."""
    
    @patch('app.cache.redis_client')
    def test_custom_ttl(self, mock_redis):
        """Should use custom TTL when specified."""
        mock_redis.get.return_value = None
        
        @cached(ttl=7200)  # 2 hours
        def long_cache_function():
            return "result"
        
        result = long_cache_function()
        
        assert result == "result"
        call_args = mock_redis.setex.call_args
        assert call_args[0][1] == 7200
    
    @patch('app.cache.redis_client')
    def test_zero_ttl_disables_cache(self, mock_redis):
        """TTL of 0 should disable caching."""
        mock_redis.get.return_value = None
        
        call_count = [0]
        
        @cached(ttl=0)
        def no_cache_function():
            call_count[0] += 1
            return "result"
        
        # Call twice
        result1 = no_cache_function()
        result2 = no_cache_function()
        
        # Both should execute the function
        assert call_count[0] == 2


class TestCacheDataTypes:
    """Test caching different data types."""
    
    @patch('app.cache.redis_client')
    def test_cache_dict(self, mock_redis):
        """Should cache dictionary results."""
        mock_redis.get.return_value = None
        
        @cached(ttl=3600)
        def return_dict():
            return {"name": "John", "age": 30}
        
        result = return_dict()
        
        assert isinstance(result, dict)
        assert result["name"] == "John"
    
    @patch('app.cache.redis_client')
    def test_cache_list(self, mock_redis):
        """Should cache list results."""
        mock_redis.get.return_value = None
        
        @cached(ttl=3600)
        def return_list():
            return [1, 2, 3, 4, 5]
        
        result = return_list()
        
        assert isinstance(result, list)
        assert len(result) == 5
    
    @patch('app.cache.redis_client')
    def test_cache_string(self, mock_redis):
        """Should cache string results."""
        mock_redis.get.return_value = None
        
        @cached(ttl=3600)
        def return_string():
            return "Hello, World!"
        
        result = return_string()
        
        assert result == "Hello, World!"


class TestCachePerformance:
    """Test cache performance improvements."""
    
    @patch('app.cache.redis_client')
    def test_cache_improves_performance(self, mock_redis):
        """Cache should significantly improve performance."""
        # First call - cache miss
        mock_redis.get.return_value = None
        
        @cached(ttl=3600)
        def slow_function():
            time.sleep(0.1)
            return "result"
        
        # First call - slow
        start = time.time()
        result1 = slow_function()
        first_duration = time.time() - start
        
        # Setup cache hit
        import json
        mock_redis.get.return_value = json.dumps({"result": "result"}).encode()
        
        # Second call - fast
        start = time.time()
        result2 = slow_function()
        second_duration = time.time() - start
        
        assert result1 == result2
        # Cache hit should be much faster
        assert second_duration < first_duration
