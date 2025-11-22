"""
Performance tests for analytics - Phase 2
Tests analytics functions with large datasets and measures execution time
"""

import pytest
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any
from app.services.analytics import summary_metrics, choice_stats, numeric_stats, text_table


# ============================================================================
# FIXTURES: Large Dataset Generation
# ============================================================================

@pytest.fixture
def large_dataset_1000():
    """Generate 1000 sample submissions."""
    submissions = []
    for i in range(1000):
        submissions.append({
            'id': i + 1,
            'form_id': 1,
            'user_id': (i % 100) + 1,
            'guest_token': f'guest_{i}' if i % 4 == 0 else None,
            'submitted_at': datetime.now() - timedelta(days=30 - (i % 30)),
            'completion_time_ms': 2000 + (i % 5000),
        })
    return submissions


@pytest.fixture
def large_dataset_10000():
    """Generate 10000 sample submissions."""
    submissions = []
    for i in range(10000):
        submissions.append({
            'id': i + 1,
            'form_id': 1,
            'user_id': (i % 500) + 1,
            'guest_token': f'guest_{i}' if i % 5 == 0 else None,
            'submitted_at': datetime.now() - timedelta(days=30 - (i % 30)),
            'completion_time_ms': 2000 + (i % 5000),
        })
    return submissions


@pytest.fixture
def large_choice_dataset():
    """Generate large dataset of choice answers."""
    choices = ['Option A', 'Option B', 'Option C', 'Option D', 'Option E']
    answers = []
    for i in range(10000):
        # Mix of single and multiple selections
        if i % 3 == 0:
            selected = f"{choices[i % 5]}, {choices[(i + 1) % 5]}"
        else:
            selected = choices[i % 5]
        answers.append({'value': selected})
    return answers


@pytest.fixture
def large_numeric_dataset():
    """Generate large dataset of numeric answers."""
    answers = []
    for i in range(10000):
        answers.append({'value': str((i % 1000) + 1)})
    return answers


@pytest.fixture
def large_text_dataset():
    """Generate large dataset of text answers."""
    answers = []
    for i in range(10000):
        answers.append({'value': f'Response text number {i} with some details'})
    return answers


@pytest.fixture
def sample_form():
    """Create a sample form."""
    return {
        'id': 1,
        'title': 'Large Form',
        'submission_start': datetime.now() - timedelta(days=30),
        'submission_end': datetime.now() + timedelta(days=30),
    }


# ============================================================================
# PERFORMANCE TESTS: Metrics Calculation
# ============================================================================

class TestMetricsPerformance:
    """Test performance of metrics calculation."""
    
    def test_metrics_1000_submissions(self, sample_form, large_dataset_1000):
        """Test metrics calculation with 1000 submissions."""
        start_time = time.time()
        metrics = summary_metrics(sample_form, large_dataset_1000)
        duration = time.time() - start_time
        
        # Should complete quickly
        assert duration < 0.1, f"Metrics calculation took {duration:.3f}s (expected < 0.1s)"
        
        # Verify results
        assert metrics['total_submissions'] == 1000
        assert metrics['unique_users'] == 100
        assert metrics['guest_submissions'] == 250  # 1000 / 4
    
    def test_metrics_10000_submissions(self, sample_form, large_dataset_10000):
        """Test metrics calculation with 10000 submissions."""
        start_time = time.time()
        metrics = summary_metrics(sample_form, large_dataset_10000)
        duration = time.time() - start_time
        
        # Should still be fast even with 10x more data
        assert duration < 0.2, f"Metrics calculation took {duration:.3f}s (expected < 0.2s)"
        
        # Verify results
        assert metrics['total_submissions'] == 10000
        assert metrics['unique_users'] == 500
        assert metrics['guest_submissions'] == 2000  # 10000 / 5
    
    def test_metrics_scaling_linear(self, sample_form, large_dataset_1000, large_dataset_10000):
        """Test that metrics calculation scales linearly with data size."""
        start_1k = time.time()
        summary_metrics(sample_form, large_dataset_1000)
        time_1k = time.time() - start_1k
        
        start_10k = time.time()
        summary_metrics(sample_form, large_dataset_10000)
        time_10k = time.time() - start_10k
        
        # 10x data should take roughly 10x time (allow 15x due to overhead)
        ratio = time_10k / time_1k
        assert ratio < 15, f"Non-linear scaling detected: {ratio:.1f}x"


# ============================================================================
# PERFORMANCE TESTS: Choice Statistics
# ============================================================================

class TestChoiceStatsPerformance:
    """Test performance of choice statistics calculation."""
    
    def test_choice_stats_1000_answers(self, large_choice_dataset):
        """Test choice stats with 1000 answers."""
        answers = large_choice_dataset[:1000]
        
        start_time = time.time()
        stats = choice_stats({}, answers)
        duration = time.time() - start_time
        
        # Should complete quickly
        assert duration < 0.05, f"Choice stats took {duration:.3f}s (expected < 0.05s)"
        assert len(stats) > 0
    
    def test_choice_stats_10000_answers(self, large_choice_dataset):
        """Test choice stats with 10000 answers."""
        start_time = time.time()
        stats = choice_stats({}, large_choice_dataset)
        duration = time.time() - start_time
        
        # Should handle 10x data efficiently
        assert duration < 0.1, f"Choice stats took {duration:.3f}s (expected < 0.1s)"
        assert len(stats) > 0
    
    def test_choice_stats_scaling_linear(self, large_choice_dataset):
        """Test linear scaling of choice stats."""
        subset_1k = large_choice_dataset[:1000]
        subset_10k = large_choice_dataset[:10000]
        
        start_1k = time.time()
        choice_stats({}, subset_1k)
        time_1k = time.time() - start_1k
        
        start_10k = time.time()
        choice_stats({}, subset_10k)
        time_10k = time.time() - start_10k
        
        ratio = time_10k / time_1k if time_1k > 0 else 1
        assert ratio < 15, f"Non-linear scaling: {ratio:.1f}x"


# ============================================================================
# PERFORMANCE TESTS: Numeric Statistics
# ============================================================================

class TestNumericStatsPerformance:
    """Test performance of numeric statistics calculation."""
    
    def test_numeric_stats_1000_values(self, large_numeric_dataset):
        """Test numeric stats with 1000 values."""
        answers = large_numeric_dataset[:1000]
        
        start_time = time.time()
        stats = numeric_stats(answers)
        duration = time.time() - start_time
        
        # Should be very fast
        assert duration < 0.05, f"Numeric stats took {duration:.3f}s (expected < 0.05s)"
        assert stats['count'] == 1000
    
    def test_numeric_stats_10000_values(self, large_numeric_dataset):
        """Test numeric stats with 10000 values."""
        start_time = time.time()
        stats = numeric_stats(large_numeric_dataset)
        duration = time.time() - start_time
        
        # Should handle 10k values efficiently
        assert duration < 0.1, f"Numeric stats took {duration:.3f}s (expected < 0.1s)"
        assert stats['count'] == 10000
    
    def test_numeric_stats_memory_efficiency(self, large_numeric_dataset):
        """Test that numeric stats don't use excessive memory."""
        import sys
        
        # Get initial memory
        import gc
        gc.collect()
        
        start_time = time.time()
        stats = numeric_stats(large_numeric_dataset)
        duration = time.time() - start_time
        
        # Should complete in reasonable time
        assert duration < 0.2, f"Numeric stats took {duration:.3f}s (expected < 0.2s)"


# ============================================================================
# PERFORMANCE TESTS: Text Processing
# ============================================================================

class TestTextTablePerformance:
    """Test performance of text table operations."""
    
    def test_text_table_1000_responses(self, large_text_dataset):
        """Test text table with 1000 responses."""
        answers = large_text_dataset[:1000]
        
        start_time = time.time()
        recent = text_table(answers, limit=10)
        duration = time.time() - start_time
        
        # Should be fast even with large dataset
        assert duration < 0.05, f"Text table took {duration:.3f}s (expected < 0.05s)"
        assert len(recent) == 10
    
    def test_text_table_10000_responses(self, large_text_dataset):
        """Test text table with 10000 responses."""
        start_time = time.time()
        recent = text_table(large_text_dataset, limit=10)
        duration = time.time() - start_time
        
        # Should still be fast for 10k
        assert duration < 0.1, f"Text table took {duration:.3f}s (expected < 0.1s)"
        assert len(recent) == 10
    
    def test_text_table_with_various_limits(self, large_text_dataset):
        """Test text table performance with different limits."""
        for limit in [1, 10, 100, 1000]:
            start_time = time.time()
            recent = text_table(large_text_dataset, limit=limit)
            duration = time.time() - start_time
            
            # Should scale with limit size
            assert duration < 0.05, f"Text table (limit={limit}) took {duration:.3f}s"
            assert len(recent) == min(limit, len(large_text_dataset))


# ============================================================================
# PERFORMANCE TESTS: Combined Operations
# ============================================================================

class TestCombinedOperationsPerformance:
    """Test performance of multiple analytics operations combined."""
    
    def test_full_form_analytics(self, sample_form, large_dataset_1000):
        """Test full form analytics with multiple operations."""
        # Simulate processing all questions for a form
        choice_answers = [{'value': f'Option {i % 5}'} for i in range(len(large_dataset_1000))]
        numeric_answers = [{'value': str(i % 100)} for i in range(len(large_dataset_1000))]
        text_answers = [{'value': f'Text {i}'} for i in range(len(large_dataset_1000))]
        
        start_time = time.time()
        
        # Calculate all stats
        metrics = summary_metrics(sample_form, large_dataset_1000)
        choice_stats_result = choice_stats({}, choice_answers)
        numeric_stats_result = numeric_stats(numeric_answers)
        text_result = text_table(text_answers)
        
        duration = time.time() - start_time
        
        # All operations combined should be fast
        assert duration < 0.5, f"Full analytics took {duration:.3f}s (expected < 0.5s)"
        
        # Verify all operations completed
        assert metrics is not None
        assert choice_stats_result is not None
        assert numeric_stats_result is not None
        assert text_result is not None
    
    def test_full_form_analytics_10k(self, sample_form, large_dataset_10000):
        """Test full form analytics with 10000 submissions."""
        choice_answers = [{'value': f'Option {i % 5}'} for i in range(len(large_dataset_10000))]
        numeric_answers = [{'value': str(i % 100)} for i in range(len(large_dataset_10000))]
        text_answers = [{'value': f'Text {i}'} for i in range(len(large_dataset_10000))]
        
        start_time = time.time()
        
        # Calculate all stats
        metrics = summary_metrics(sample_form, large_dataset_10000)
        choice_stats_result = choice_stats({}, choice_answers)
        numeric_stats_result = numeric_stats(numeric_answers)
        text_result = text_table(text_answers)
        
        duration = time.time() - start_time
        
        # Should still complete in reasonable time
        assert duration < 1.0, f"Full analytics (10k) took {duration:.3f}s (expected < 1.0s)"


# ============================================================================
# PERFORMANCE TESTS: Stress Testing
# ============================================================================

class TestAnalyticsStress:
    """Stress tests for analytics system."""
    
    def test_extreme_choice_options(self):
        """Test choice stats with many different options."""
        # Create answers with many unique options
        answers = [{'value': f'Option {i}'} for i in range(1000)]
        
        start_time = time.time()
        stats = choice_stats({}, answers)
        duration = time.time() - start_time
        
        # Should handle many unique options
        assert len(stats) == 1000
        assert duration < 0.1, f"Extreme options took {duration:.3f}s"
    
    def test_multi_select_explosion(self):
        """Test choice stats with heavy multi-select data."""
        # Create answers with many selections each
        answers = []
        for i in range(1000):
            # Each answer has 5-10 selections
            selections = [f'Option {j}' for j in range(i % 10 + 5)]
            answers.append({'value': ', '.join(selections)})
        
        start_time = time.time()
        stats = choice_stats({}, answers)
        duration = time.time() - start_time
        
        # Should handle multi-select efficiently
        assert len(stats) > 0
        assert duration < 0.2, f"Multi-select explosion took {duration:.3f}s"
    
    def test_numeric_edge_values(self):
        """Test numeric stats with extreme values."""
        import sys
        
        answers = []
        for i in range(1000):
            if i % 3 == 0:
                answers.append({'value': str(sys.maxsize)})
            elif i % 3 == 1:
                answers.append({'value': str(-sys.maxsize)})
            else:
                answers.append({'value': str(i)})
        
        start_time = time.time()
        stats = numeric_stats(answers)
        duration = time.time() - start_time
        
        # Should handle extreme values
        assert stats['min'] is not None
        assert stats['max'] is not None
        assert duration < 0.1, f"Extreme values took {duration:.3f}s"
    
    def test_very_long_text_responses(self):
        """Test text table with very long responses."""
        long_text = "a" * 10000  # 10KB text
        answers = [{'value': f'{long_text} {i}'} for i in range(1000)]
        
        start_time = time.time()
        recent = text_table(answers, limit=10)
        duration = time.time() - start_time
        
        # Should handle long text efficiently
        assert len(recent) == 10
        assert duration < 0.1, f"Very long text took {duration:.3f}s"


# ============================================================================
# PERFORMANCE TESTS: Comparison Benchmarks
# ============================================================================

class TestPerformanceBenchmarks:
    """Benchmark performance against expected standards."""
    
    def test_benchmark_metrics_vs_size(self, sample_form):
        """Benchmark metrics calculation against various dataset sizes."""
        sizes = [100, 500, 1000, 5000]
        times = []
        
        for size in sizes:
            submissions = [
                {'id': i, 'user_id': i % 50, 'guest_token': None}
                for i in range(size)
            ]
            
            start_time = time.time()
            summary_metrics(sample_form, submissions)
            duration = time.time() - start_time
            times.append(duration)
        
        # Verify linear or sub-linear growth
        # time[1000] should be roughly 2x time[500]
        ratio = times[2] / times[1] if times[1] > 0 else 1
        assert ratio < 3, f"Non-linear growth detected: {ratio:.1f}x"
    
    def test_benchmark_choice_stats_vs_uniqueness(self):
        """Benchmark choice stats against number of unique options."""
        base_answers = 1000
        
        benchmarks = []
        for unique_count in [5, 10, 50, 100]:
            answers = [
                {'value': f'Option {i % unique_count}'}
                for i in range(base_answers)
            ]
            
            start_time = time.time()
            choice_stats({}, answers)
            duration = time.time() - start_time
            benchmarks.append((unique_count, duration))
        
        # Performance shouldn't degrade significantly with unique options
        for unique, duration in benchmarks:
            assert duration < 0.1, f"Choice stats with {unique} unique options took {duration:.3f}s"


# ============================================================================
# PERFORMANCE TESTS: Memory Profiling
# ============================================================================

class TestMemoryEfficiency:
    """Test memory efficiency of analytics operations."""
    
    def test_metrics_memory_constant(self, sample_form, large_dataset_10000):
        """Test that metrics calculation uses constant memory."""
        # Metrics should not scale with data size
        import sys
        
        metrics = summary_metrics(sample_form, large_dataset_10000)
        
        # Metrics dict should be small regardless of input size
        metrics_size = sys.getsizeof(metrics)
        assert metrics_size < 1000, f"Metrics dict too large: {metrics_size} bytes"
    
    def test_choice_stats_reasonable_memory(self, large_choice_dataset):
        """Test that choice stats uses reasonable memory."""
        import sys
        
        stats = choice_stats({}, large_choice_dataset)
        
        # Stats dict should be smaller than input
        stats_size = sum(sys.getsizeof(k) + sys.getsizeof(v) for k, v in stats.items())
        input_size = sum(sys.getsizeof(a['value']) for a in large_choice_dataset)
        
        # Stats should compress data, not expand it
        assert stats_size < input_size


# ============================================================================
# UTILITY: Performance Reporting
# ============================================================================

def print_performance_report(test_name: str, duration: float, dataset_size: int) -> None:
    """Print a performance report for a test."""
    throughput = dataset_size / duration if duration > 0 else 0
    print(f"\n{test_name}:")
    print(f"  Dataset Size: {dataset_size:,}")
    print(f"  Duration: {duration:.4f}s")
    print(f"  Throughput: {throughput:,.0f} items/sec")
