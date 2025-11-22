"""
Integration tests for analytics dashboard - Phase 2
Tests end-to-end analytics workflows with real data scenarios
"""

import pytest
from datetime import datetime, timedelta
from typing import Dict, List, Any
from app.services.analytics import summary_metrics, choice_stats, numeric_stats, text_table


# ============================================================================
# FIXTURES: Sample Data
# ============================================================================

@pytest.fixture
def sample_form():
    """Create a sample form for testing."""
    return {
        'id': 1,
        'title': 'Customer Satisfaction Survey',
        'status': 'published',
        'access_type': 'public',
        'single_submission': False,
        'submission_start': datetime.now() - timedelta(days=30),
        'submission_end': datetime.now() + timedelta(days=30),
    }


@pytest.fixture
def sample_questions():
    """Create sample questions with various field types."""
    return [
        {
            'id': 1,
            'label': 'Overall Satisfaction',
            'field_type': 'rating',
            'required': True,
        },
        {
            'id': 2,
            'label': 'Which features do you like?',
            'field_type': 'checkbox',
            'required': False,
        },
        {
            'id': 3,
            'label': 'Recommended Features',
            'field_type': 'radio',
            'required': False,
        },
        {
            'id': 4,
            'label': 'Price Rating',
            'field_type': 'integer',
            'required': False,
        },
        {
            'id': 5,
            'label': 'Additional Comments',
            'field_type': 'text',
            'required': False,
        }
    ]


@pytest.fixture
def sample_submissions():
    """Create sample submission records."""
    submissions = []
    for i in range(50):
        submissions.append({
            'id': i + 1,
            'form_id': 1,
            'user_id': (i % 10) + 1,
            'guest_token': f'guest_{i}' if i % 3 == 0 else None,
            'submitted_at': datetime.now() - timedelta(days=30 - (i % 30)),
            'completion_time_ms': 2000 + (i * 50),
        })
    return submissions


@pytest.fixture
def sample_answers():
    """Create sample answers for various field types."""
    answers = {
        # Rating answers (1-5)
        1: [{'value': str((i % 5) + 1)} for i in range(50)],
        
        # Checkbox answers (multiple selections)
        2: [
            {'value': 'UI'},
            {'value': 'Performance'},
            {'value': 'UI, Performance'},
            {'value': 'Docs'},
            {'value': 'UI, Docs'},
            {'value': 'Performance, Docs'},
            {'value': 'UI, Performance, Docs'},
            {'value': 'UI'},
        ] * 6 + [{'value': 'Performance'}] * 2,
        
        # Radio answers
        3: [
            {'value': 'Mobile App'},
            {'value': 'Desktop UX'},
            {'value': 'API Docs'},
            {'value': 'Integrations'},
        ] * 12 + [{'value': 'Mobile App'}] * 2,
        
        # Numeric answers
        4: [{'value': str(i % 100)} for i in range(50)],
        
        # Text answers
        5: [{'value': f'This is feedback {i}'} for i in range(50)],
    }
    return answers


# ============================================================================
# INTEGRATION TESTS: End-to-End Workflows
# ============================================================================

class TestAnalyticsDashboardWorkflow:
    """Test complete analytics dashboard workflows."""
    
    def test_form_analytics_end_to_end(self, sample_form, sample_submissions, sample_answers):
        """Test complete analytics generation for a form."""
        # Get metrics
        metrics = summary_metrics(sample_form, sample_submissions)
        
        # Verify metrics
        assert metrics['total_submissions'] == 50
        assert metrics['unique_users'] == 10
        assert metrics['guest_submissions'] == 17  # 50 / 3 ≈ 17
        assert metrics['is_open'] is True
        
        # Verify metrics are accessible for dashboard
        assert 'total_submissions' in metrics
        assert 'unique_users' in metrics
        assert 'guest_submissions' in metrics
        assert 'is_open' in metrics
    
    def test_rating_question_analytics(self, sample_answers):
        """Test rating question analytics workflow."""
        rating_answers = sample_answers[1]
        
        # Calculate stats
        stats = choice_stats({}, rating_answers)
        
        # Verify all ratings present
        assert '1' in stats
        assert '2' in stats
        assert '3' in stats
        assert '4' in stats
        assert '5' in stats
        
        # Calculate average rating
        total_score = sum(int(k) * v for k, v in stats.items())
        total_count = sum(stats.values())
        avg_rating = total_score / total_count
        
        # Average should be around 3 (since 1-5 distributed evenly)
        assert 2.5 < avg_rating < 3.5
    
    def test_checkbox_question_analytics(self, sample_answers):
        """Test checkbox (multiple selection) question analytics."""
        checkbox_answers = sample_answers[2]
        
        # Calculate stats
        stats = choice_stats({}, checkbox_answers)
        
        # Verify options are counted
        assert 'UI' in stats
        assert 'Performance' in stats
        assert 'Docs' in stats
        
        # Total count should exceed number of answers (due to multiple selections)
        total_count = sum(stats.values())
        assert total_count > len(checkbox_answers)
    
    def test_numeric_question_analytics(self, sample_answers):
        """Test numeric question analytics workflow."""
        numeric_answers = sample_answers[4]
        
        # Calculate stats
        stats = numeric_stats(numeric_answers)
        
        # Verify all statistics present
        assert stats['count'] == 50
        assert stats['min'] == 0
        assert stats['max'] == 49
        assert stats['avg'] == pytest.approx(24.5)  # (0+1+...+49)/50
    
    def test_text_question_analytics(self, sample_answers):
        """Test text question analytics workflow."""
        text_answers = sample_answers[5]
        
        # Get recent responses
        recent = text_table(text_answers, limit=10)
        
        # Verify recent responses
        assert len(recent) == 10
        assert 'This is feedback 49' in recent
        assert 'This is feedback 40' in recent  # Last 10
    
    def test_multi_question_form_analytics(self, sample_form, sample_questions, sample_submissions, sample_answers):
        """Test analytics for form with multiple question types."""
        # Process each question
        form_analytics = {}
        
        for question in sample_questions:
            q_id = question['id']
            q_type = question['field_type']
            answers = sample_answers.get(q_id, [])
            
            if q_type == 'rating':
                stats = choice_stats(question, answers)
                form_analytics[q_id] = {'type': 'rating', 'stats': stats}
            
            elif q_type in ['checkbox', 'radio']:
                stats = choice_stats(question, answers)
                form_analytics[q_id] = {'type': q_type, 'stats': stats}
            
            elif q_type == 'integer':
                stats = numeric_stats(answers)
                form_analytics[q_id] = {'type': 'numeric', 'stats': stats}
            
            elif q_type == 'text':
                recent = text_table(answers, limit=5)
                form_analytics[q_id] = {'type': 'text', 'recent': recent}
        
        # Verify all questions processed
        assert len(form_analytics) == len(sample_questions)
        
        # Verify each question has analytics
        for q_id, analytics in form_analytics.items():
            assert 'type' in analytics
            if analytics['type'] in ['rating', 'checkbox', 'radio', 'numeric']:
                assert 'stats' in analytics
            elif analytics['type'] == 'text':
                assert 'recent' in analytics


# ============================================================================
# INTEGRATION TESTS: Filter Application
# ============================================================================

class TestAnalyticsFiltering:
    """Test analytics filtering functionality."""
    
    def test_date_range_filter(self, sample_submissions):
        """Test filtering submissions by date range."""
        # Filter for last 7 days
        cutoff = datetime.now() - timedelta(days=7)
        filtered = [s for s in sample_submissions if s['submitted_at'] > cutoff]
        
        # Should have some submissions from last 7 days
        assert len(filtered) > 0
        assert len(filtered) < len(sample_submissions)
    
    def test_min_submissions_filter(self, sample_form, sample_submissions):
        """Test filtering forms by minimum submissions."""
        min_subs = 25
        
        form_subs_count = len(sample_submissions)
        passes_filter = form_subs_count >= min_subs
        
        assert passes_filter is True
    
    def test_combined_filters(self, sample_submissions):
        """Test applying multiple filters simultaneously."""
        # Date range
        cutoff = datetime.now() - timedelta(days=15)
        date_filtered = [s for s in sample_submissions if s['submitted_at'] > cutoff]
        
        # Min submissions
        min_subs = 10
        passes_min = len(date_filtered) >= min_subs
        
        assert passes_min is True
        assert len(date_filtered) <= len(sample_submissions)


# ============================================================================
# INTEGRATION TESTS: Data Consistency
# ============================================================================

class TestAnalyticsDataConsistency:
    """Test data consistency across analytics operations."""
    
    def test_submission_count_consistency(self, sample_form, sample_submissions):
        """Test submission count remains consistent through calculations."""
        initial_count = len(sample_submissions)
        
        metrics = summary_metrics(sample_form, sample_submissions)
        calculated_count = metrics['total_submissions']
        
        assert initial_count == calculated_count
    
    def test_answer_count_consistency(self, sample_answers):
        """Test answer counts remain consistent."""
        for q_id, answers in sample_answers.items():
            initial_count = len(answers)
            
            # Calculate stats (doesn't modify data)
            if q_id in [1, 2, 3]:  # Choice fields
                stats = choice_stats({}, answers)
                total_count = sum(stats.values())
            else:  # Text/numeric
                if q_id == 4:
                    stats = numeric_stats(answers)
                    total_count = stats.get('count', 0)
                else:
                    recent = text_table(answers)
                    total_count = len(recent)
            
            # Verify we processed all answers (or more for multi-select)
            if q_id in [2]:  # Multi-select can have more
                assert total_count >= initial_count
            elif q_id == 4:  # Numeric
                assert total_count == initial_count
            elif q_id == 5:  # Text (limited to 10)
                assert total_count <= initial_count
    
    def test_metrics_non_negative(self, sample_form, sample_submissions):
        """Test all metrics are non-negative."""
        metrics = summary_metrics(sample_form, sample_submissions)
        
        assert metrics['total_submissions'] >= 0
        assert metrics['unique_users'] >= 0
        assert metrics['guest_submissions'] >= 0


# ============================================================================
# INTEGRATION TESTS: Performance Characteristics
# ============================================================================

class TestAnalyticsPerformance:
    """Test performance characteristics of analytics operations."""
    
    def test_metrics_calculation_speed(self, sample_form, sample_submissions):
        """Test that metrics calculation is fast even with many submissions."""
        import time
        
        start = time.time()
        metrics = summary_metrics(sample_form, sample_submissions)
        duration = time.time() - start
        
        # Should complete in under 100ms
        assert duration < 0.1
        assert metrics is not None
    
    def test_choice_stats_calculation_speed(self, sample_answers):
        """Test choice stats calculation speed."""
        import time
        
        answers = sample_answers[2]  # Checkbox field
        
        start = time.time()
        stats = choice_stats({}, answers)
        duration = time.time() - start
        
        # Should complete in under 50ms
        assert duration < 0.05
        assert len(stats) > 0
    
    def test_numeric_stats_calculation_speed(self, sample_answers):
        """Test numeric stats calculation speed."""
        import time
        
        answers = sample_answers[4]  # Numeric field
        
        start = time.time()
        stats = numeric_stats(answers)
        duration = time.time() - start
        
        # Should complete in under 50ms
        assert duration < 0.05
        assert stats['count'] > 0


# ============================================================================
# INTEGRATION TESTS: Edge Cases
# ============================================================================

class TestAnalyticsEdgeCases:
    """Test analytics with edge case data."""
    
    def test_empty_form_analytics(self, sample_form):
        """Test analytics with no submissions."""
        empty_submissions = []
        
        metrics = summary_metrics(sample_form, empty_submissions)
        
        assert metrics['total_submissions'] == 0
        assert metrics['unique_users'] == 0
        assert metrics['guest_submissions'] == 0
    
    def test_single_submission(self, sample_form):
        """Test analytics with single submission."""
        single_submission = [{'user_id': 1, 'guest_token': None}]
        
        metrics = summary_metrics(sample_form, single_submission)
        
        assert metrics['total_submissions'] == 1
        assert metrics['unique_users'] == 1
        assert metrics['guest_submissions'] == 0
    
    def test_all_guest_submissions(self, sample_form):
        """Test analytics with all guest submissions."""
        guest_submissions = [
            {'user_id': None, 'guest_token': f'guest_{i}'} 
            for i in range(10)
        ]
        
        metrics = summary_metrics(sample_form, guest_submissions)
        
        assert metrics['total_submissions'] == 10
        assert metrics['unique_users'] == 0
        assert metrics['guest_submissions'] == 10
    
    def test_single_choice_option(self):
        """Test choice stats with single option."""
        answers = [{'value': 'Only'} for _ in range(10)]
        
        stats = choice_stats({}, answers)
        
        assert len(stats) == 1
        assert stats['Only'] == 10
    
    def test_all_invalid_numeric_answers(self):
        """Test numeric stats with all invalid values."""
        answers = [{'value': 'invalid'} for _ in range(10)]
        
        stats = numeric_stats(answers)
        
        assert stats['count'] == 0
        assert stats['min'] is None
        assert stats['max'] is None
        assert stats['avg'] is None
    
    def test_empty_text_answers(self):
        """Test text table with empty responses."""
        answers = [{'value': ''} for _ in range(10)]
        
        recent = text_table(answers)
        
        assert len(recent) == 0


# ============================================================================
# INTEGRATION TESTS: Real-World Scenarios
# ============================================================================

class TestRealWorldScenarios:
    """Test real-world form analytics scenarios."""
    
    def test_satisfaction_survey_workflow(self):
        """Simulate complete satisfaction survey analytics workflow."""
        # Create form
        form = {
            'id': 1,
            'title': 'Satisfaction Survey',
            'submission_start': datetime.now(),
            'submission_end': datetime.now() + timedelta(days=7),
        }
        
        # Create submissions (varied response pattern)
        submissions = [
            {'id': i, 'user_id': i % 20, 'guest_token': None, 'submitted_at': datetime.now()}
            for i in range(100)
        ]
        
        # Create rating answers (realistic satisfaction distribution)
        answers = {
            'satisfaction': (
                [{'value': '5'}] * 40 +  # 40% very satisfied
                [{'value': '4'}] * 30 +  # 30% satisfied
                [{'value': '3'}] * 20 +  # 20% neutral
                [{'value': '2'}] * 8 +   # 8% unsatisfied
                [{'value': '1'}] * 2     # 2% very unsatisfied
            )
        }
        
        # Calculate metrics
        metrics = summary_metrics(form, submissions)
        rating_stats = choice_stats({}, answers['satisfaction'])
        
        # Verify results
        assert metrics['total_submissions'] == 100
        assert len(rating_stats) == 5
        
        # Calculate average satisfaction
        total = sum(int(k) * v for k, v in rating_stats.items())
        avg = total / sum(rating_stats.values())
        
        # Should be high (mostly 4-5 stars)
        assert avg > 4.0
    
    def test_feature_request_survey_workflow(self):
        """Simulate feature request survey with multiple choice question."""
        # Feature request answers with multi-select
        answers = [
            {'value': 'Mobile App, Offline Mode'},
            {'value': 'Mobile App'},
            {'value': 'Dark Theme'},
            {'value': 'Mobile App, Dark Theme'},
            {'value': 'Dark Theme, Offline Mode'},
            {'value': 'Mobile App, Dark Theme, Offline Mode'},
            {'value': 'Offline Mode'},
        ] * 10  # 70 total responses
        
        stats = choice_stats({}, answers)
        
        # Each feature should have multiple mentions
        assert stats['Mobile App'] > 15
        assert stats['Dark Theme'] > 15
        assert stats['Offline Mode'] > 15
        
        # Mobile App should be most requested
        assert stats['Mobile App'] == max(stats.values())


# ============================================================================
# INTEGRATION TESTS: Filter + Analytics Combined
# ============================================================================

class TestFilteredAnalytics:
    """Test analytics after applying filters."""
    
    def test_time_period_analytics(self, sample_submissions, sample_answers):
        """Test analytics for specific time period."""
        # Get submissions from last 7 days
        cutoff = datetime.now() - timedelta(days=7)
        filtered_subs = [s for s in sample_submissions if s['submitted_at'] > cutoff]
        
        # Should have filtered some submissions
        assert 0 < len(filtered_subs) < len(sample_submissions)
        
        # Verify we can calculate metrics on filtered data
        form = {'submission_start': cutoff, 'submission_end': datetime.now()}
        metrics = summary_metrics(form, filtered_subs)
        
        assert metrics['total_submissions'] == len(filtered_subs)
    
    def test_user_segment_analytics(self, sample_submissions):
        """Test analytics for specific user segment."""
        user_id = 5
        user_submissions = [s for s in sample_submissions if s['user_id'] == user_id]
        
        # Should have some submissions
        assert len(user_submissions) > 0
        
        # Calculate metrics
        form = {}
        metrics = summary_metrics(form, user_submissions)
        
        assert metrics['total_submissions'] == len(user_submissions)
        assert metrics['unique_users'] == 1
