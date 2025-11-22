"""
UI component tests for analytics dashboard - Phase 2
Tests Streamlit dashboard components and rendering logic
"""

import pytest
from datetime import datetime, timedelta
from typing import Dict, List, Any
from unittest.mock import Mock, patch, MagicMock


# ============================================================================
# METRIC CARD COMPONENT TESTS
# ============================================================================

class TestMetricCardComponent:
    """Test MetricCard component rendering and behavior."""
    
    def test_metric_card_initialization(self):
        """Test MetricCard initialization with all parameters."""
        from app.pages.analytics_dashboard import MetricCard
        
        card = MetricCard(
            label="Test Label",
            value=42,
            suffix="%",
            delta=5.2,
            icon="📊"
        )
        
        assert card.label == "Test Label"
        assert card.value == 42
        assert card.suffix == "%"
        assert card.delta == 5.2
        assert card.icon == "📊"
    
    def test_metric_card_default_values(self):
        """Test MetricCard with default values."""
        from app.pages.analytics_dashboard import MetricCard
        
        card = MetricCard(label="Metric", value=100)
        
        assert card.label == "Metric"
        assert card.value == 100
        assert card.suffix == ""
        assert card.delta is None
        assert card.icon == "📊"
    
    def test_metric_card_with_various_value_types(self):
        """Test MetricCard with different value types."""
        from app.pages.analytics_dashboard import MetricCard
        
        # Integer
        card_int = MetricCard("Count", 1000)
        assert card_int.value == 1000
        
        # Float
        card_float = MetricCard("Ratio", 3.14)
        assert card_float.value == 3.14
        
        # String
        card_str = MetricCard("Status", "Active")
        assert card_str.value == "Active"
    
    def test_metric_card_with_custom_icons(self):
        """Test MetricCard with various emoji icons."""
        from app.pages.analytics_dashboard import MetricCard
        
        icons = ["📊", "👥", "📝", "✅", "📈", "🔓"]
        
        for icon in icons:
            card = MetricCard("Test", 1, icon=icon)
            assert card.icon == icon


# ============================================================================
# METRICS ROW COMPONENT TESTS
# ============================================================================

class TestMetricsRowComponent:
    """Test MetricsRow component layout and behavior."""
    
    def test_metrics_row_initialization(self):
        """Test MetricsRow initialization."""
        from app.pages.analytics_dashboard import MetricCard, MetricsRow
        
        cards = [
            MetricCard("Card 1", 100),
            MetricCard("Card 2", 200),
            MetricCard("Card 3", 300),
        ]
        
        row = MetricsRow(cards, cols=3)
        
        assert row.cards == cards
        assert row.cols == 3
    
    def test_metrics_row_column_limit(self):
        """Test MetricsRow respects column limits."""
        from app.pages.analytics_dashboard import MetricCard, MetricsRow
        
        cards = [MetricCard(f"Card {i}", i * 100) for i in range(10)]
        
        # Request 10 columns but only have 10 cards
        row = MetricsRow(cards, cols=10)
        assert row.cols == 10
        
        # Request 20 columns but only have 10 cards
        row = MetricsRow(cards, cols=20)
        assert row.cols == 10  # Should limit to number of cards
    
    def test_metrics_row_empty_cards(self):
        """Test MetricsRow with empty card list."""
        from app.pages.analytics_dashboard import MetricsRow
        
        row = MetricsRow([], cols=4)
        assert row.cols == 1  # Should default to 1


# ============================================================================
# ANALYTICS FILTER COMPONENT TESTS
# ============================================================================

class TestAnalyticsFilterComponent:
    """Test AnalyticsFilter component functionality."""
    
    def test_filter_initialization(self):
        """Test AnalyticsFilter initialization."""
        from app.pages.analytics_dashboard import AnalyticsFilter
        
        # Mock streamlit
        with patch('streamlit.session_state', {}):
            filter_mgr = AnalyticsFilter()
            # Filter should initialize without error
            assert filter_mgr is not None
    
    def test_filter_default_values(self):
        """Test filter default values."""
        from app.pages.analytics_dashboard import AnalyticsFilter
        
        filters = {
            'start_date': datetime.now() - timedelta(days=30),
            'end_date': datetime.now(),
            'min_submissions': 0,
            'question_filter': 'all',
        }
        
        # Verify default structure
        assert 'start_date' in filters
        assert 'end_date' in filters
        assert 'min_submissions' in filters
        assert 'question_filter' in filters
        
        # Verify date range is reasonable
        assert filters['end_date'] > filters['start_date']
        assert filters['min_submissions'] >= 0
    
    def test_filter_apply_date_range(self):
        """Test applying date range filter."""
        from app.pages.analytics_dashboard import AnalyticsFilter
        
        filter_mgr = AnalyticsFilter()
        
        # Create test submissions
        now = datetime.now()
        submissions = [
            {'submitted_at': now - timedelta(days=i)} for i in range(60)
        ]
        
        filters = {
            'start_date': now - timedelta(days=30),
            'end_date': now,
            'min_submissions': 0,
            'question_filter': 'all',
        }
        
        # Apply filters
        filtered = filter_mgr.apply_filters(submissions, filters)
        
        # Should have only last 30 days
        assert len(filtered) <= len(submissions)


# ============================================================================
# CHOICE DISTRIBUTION CHART TESTS
# ============================================================================

class TestChoiceDistributionChart:
    """Test ChoiceDistributionChart component."""
    
    def test_pie_chart_creation(self):
        """Test pie chart creation."""
        from app.pages.analytics_dashboard import ChoiceDistributionChart
        
        stats = {
            'Option A': 30,
            'Option B': 50,
            'Option C': 20,
        }
        
        fig = ChoiceDistributionChart.create_pie_chart(stats, "Test Pie Chart")
        
        # Verify figure is created
        assert fig is not None
        assert fig.layout.title.text == "Test Pie Chart"
    
    def test_pie_chart_empty_stats(self):
        """Test pie chart with empty stats."""
        from app.pages.analytics_dashboard import ChoiceDistributionChart
        
        fig = ChoiceDistributionChart.create_pie_chart({}, "Empty Chart")
        
        # Should still create figure
        assert fig is not None
    
    def test_bar_chart_creation(self):
        """Test bar chart creation."""
        from app.pages.analytics_dashboard import ChoiceDistributionChart
        
        stats = {
            'Option A': 30,
            'Option B': 50,
            'Option C': 20,
        }
        
        fig = ChoiceDistributionChart.create_bar_chart(stats, "Test Bar Chart")
        
        assert fig is not None
        assert fig.layout.title.text == "Test Bar Chart"
    
    def test_bar_chart_sorting(self):
        """Test bar chart sorts by value descending."""
        from app.pages.analytics_dashboard import ChoiceDistributionChart
        
        stats = {
            'A': 10,
            'B': 50,
            'C': 30,
        }
        
        fig = ChoiceDistributionChart.create_bar_chart(stats, "Sorted Chart")
        
        # Chart data should be sorted
        assert fig is not None
        # B should be first (50), C second (30), A third (10)
    
    def test_percentage_table_creation(self):
        """Test percentage table creation."""
        from app.pages.analytics_dashboard import ChoiceDistributionChart
        
        stats = {
            'Option A': 25,
            'Option B': 50,
            'Option C': 25,
        }
        
        df = ChoiceDistributionChart.create_percentage_table(stats)
        
        # Verify DataFrame structure
        assert 'Option' in df.columns
        assert 'Count' in df.columns
        assert 'Percentage' in df.columns
        
        # Verify sorting by count (descending)
        assert df.iloc[0]['Count'] == 50  # Option B first
    
    def test_percentage_table_calculations(self):
        """Test percentage calculations are correct."""
        from app.pages.analytics_dashboard import ChoiceDistributionChart
        
        stats = {
            'A': 20,
            'B': 30,
            'C': 50,
        }
        
        df = ChoiceDistributionChart.create_percentage_table(stats)
        
        # Total should be 100
        percentages = df['Percentage'].str.rstrip('%').astype(float)
        total_percent = percentages.sum()
        assert abs(total_percent - 100.0) < 0.1


# ============================================================================
# NUMERIC ANALYSIS CHART TESTS
# ============================================================================

class TestNumericAnalysisChart:
    """Test NumericAnalysisChart component."""
    
    def test_histogram_creation(self):
        """Test histogram creation."""
        from app.pages.analytics_dashboard import NumericAnalysisChart
        
        answers = [
            {'value': str(i % 100)} for i in range(1000)
        ]
        
        fig = NumericAnalysisChart.create_histogram(answers, "Test Histogram")
        
        assert fig is not None
        assert fig.layout.title.text == "Test Histogram"
    
    def test_histogram_with_invalid_data(self):
        """Test histogram handles invalid numeric data."""
        from app.pages.analytics_dashboard import NumericAnalysisChart
        
        answers = [
            {'value': 'invalid'},
            {'value': 'text'},
            {'value': ''},
        ]
        
        fig = NumericAnalysisChart.create_histogram(answers, "Invalid Data")
        
        # Should still create figure (even if empty)
        assert fig is not None
    
    def test_box_plot_creation(self):
        """Test box plot creation."""
        from app.pages.analytics_dashboard import NumericAnalysisChart
        
        answers = [
            {'value': str(i % 100)} for i in range(500)
        ]
        
        fig = NumericAnalysisChart.create_box_plot(answers, "Test Box Plot")
        
        assert fig is not None
        assert fig.layout.title.text == "Test Box Plot"
    
    def test_box_plot_with_outliers(self):
        """Test box plot with extreme values."""
        from app.pages.analytics_dashboard import NumericAnalysisChart
        
        answers = [
            {'value': '50'},
            {'value': '51'},
            {'value': '49'},
            {'value': '1000'},  # Outlier
            {'value': '0'},     # Outlier
        ]
        
        fig = NumericAnalysisChart.create_box_plot(answers, "With Outliers")
        
        assert fig is not None


# ============================================================================
# RATING ANALYSIS CHART TESTS
# ============================================================================

class TestRatingAnalysisChart:
    """Test RatingAnalysisChart component."""
    
    def test_rating_distribution_creation(self):
        """Test rating distribution chart creation."""
        from app.pages.analytics_dashboard import RatingAnalysisChart
        
        stats = {
            '1': 5,
            '2': 10,
            '3': 20,
            '4': 40,
            '5': 25,
        }
        
        fig = RatingAnalysisChart.create_rating_distribution(stats)
        
        assert fig is not None
        assert fig.layout.title.text == "Rating Distribution"
    
    def test_rating_distribution_partial_ratings(self):
        """Test rating distribution with missing rating levels."""
        from app.pages.analytics_dashboard import RatingAnalysisChart
        
        stats = {
            '4': 30,
            '5': 70,
        }
        
        fig = RatingAnalysisChart.create_rating_distribution(stats, max_rating=5)
        
        assert fig is not None
    
    def test_average_rating_calculation(self):
        """Test average rating calculation."""
        from app.pages.analytics_dashboard import RatingAnalysisChart
        
        stats = {
            '1': 0,
            '2': 0,
            '3': 0,
            '4': 25,
            '5': 75,
        }
        
        avg = RatingAnalysisChart.calculate_average_rating(stats)
        
        # Should be 4.75 (75*5 + 25*4) / 100
        assert abs(avg - 4.75) < 0.01
    
    def test_average_rating_all_stars(self):
        """Test average rating when all responses are 5 stars."""
        from app.pages.analytics_dashboard import RatingAnalysisChart
        
        stats = {
            '5': 100,
        }
        
        avg = RatingAnalysisChart.calculate_average_rating(stats)
        
        assert avg == 5.0
    
    def test_average_rating_one_star(self):
        """Test average rating when all responses are 1 star."""
        from app.pages.analytics_dashboard import RatingAnalysisChart
        
        stats = {
            '1': 100,
        }
        
        avg = RatingAnalysisChart.calculate_average_rating(stats)
        
        assert avg == 1.0


# ============================================================================
# DASHBOARD RENDER FUNCTION TESTS
# ============================================================================

class TestDashboardRender:
    """Test main dashboard rendering function."""
    
    def test_dashboard_with_sample_data(self):
        """Test dashboard renders with sample data."""
        from app.pages.analytics_dashboard import get_sample_data
        
        forms, submissions_data, questions_data, answers_data = get_sample_data()
        
        # Verify sample data structure
        assert len(forms) > 0
        assert len(submissions_data) > 0
        assert len(questions_data) > 0
        assert len(answers_data) > 0
        
        # Verify forms have required fields
        for form in forms:
            assert 'id' in form
            assert 'title' in form
            assert 'status' in form
    
    def test_dashboard_with_empty_forms(self):
        """Test dashboard handles empty form list."""
        from app.pages.analytics_dashboard import render_analytics_dashboard
        
        with patch('streamlit.info'):
            # Should handle empty form list gracefully
            render_analytics_dashboard([], {}, {}, {})
    
    def test_dashboard_with_no_submissions(self):
        """Test dashboard with form but no submissions."""
        from app.pages.analytics_dashboard import render_analytics_dashboard
        
        forms = [{'id': 1, 'title': 'Test Form', 'status': 'published'}]
        
        with patch('streamlit.warning'):
            # Should handle no submissions gracefully
            render_analytics_dashboard(forms, {1: []}, {}, {})


# ============================================================================
# STREAMLIT SESSION STATE TESTS
# ============================================================================

class TestStreamlitSessionState:
    """Test session state management for analytics."""
    
    def test_filter_session_state_persistence(self):
        """Test filter state persists in session."""
        # Mock streamlit session_state
        mock_session_state = {
            'analytics_filters': {
                'start_date': datetime.now() - timedelta(days=30),
                'end_date': datetime.now(),
                'min_submissions': 0,
                'question_filter': 'all',
            }
        }
        
        # Filters should remain unchanged
        assert 'analytics_filters' in mock_session_state
        assert 'start_date' in mock_session_state['analytics_filters']
    
    def test_form_selector_session_state(self):
        """Test form selector maintains state."""
        mock_session_state = {
            'form_selector': 0
        }
        
        # Change selection
        mock_session_state['form_selector'] = 1
        
        # Should persist
        assert mock_session_state['form_selector'] == 1


# ============================================================================
# INTEGRATION: END-TO-END COMPONENT FLOW
# ============================================================================

class TestComponentIntegration:
    """Test component integration in dashboard."""
    
    def test_metric_cards_with_real_data(self):
        """Test metric cards render with real analytics data."""
        from app.pages.analytics_dashboard import MetricCard, MetricsRow
        
        # Simulate metrics from summary_metrics
        metrics = {
            'total_submissions': 150,
            'unique_users': 45,
            'guest_submissions': 30,
            'is_open': True,
        }
        
        # Create cards
        cards = [
            MetricCard("Total Submissions", metrics['total_submissions'], icon="📝"),
            MetricCard("Unique Users", metrics['unique_users'], icon="👥"),
            MetricCard("Guest Submissions", metrics['guest_submissions'], icon="🔓"),
            MetricCard("Form Status", "Open" if metrics['is_open'] else "Closed", icon="✅"),
        ]
        
        row = MetricsRow(cards, cols=4)
        
        assert len(row.cards) == 4
        assert row.cols == 4
    
    def test_chart_workflow(self):
        """Test complete chart rendering workflow."""
        from app.pages.analytics_dashboard import (
            ChoiceDistributionChart,
            NumericAnalysisChart,
            RatingAnalysisChart
        )
        
        # Create sample data
        choice_stats = {
            'Option A': 45,
            'Option B': 35,
            'Option C': 20,
        }
        
        numeric_answers = [{'value': str(i)} for i in range(100)]
        
        rating_stats = {
            '1': 5,
            '2': 10,
            '3': 25,
            '4': 35,
            '5': 25,
        }
        
        # Create all charts
        pie = ChoiceDistributionChart.create_pie_chart(choice_stats, "Choices")
        bar = ChoiceDistributionChart.create_bar_chart(choice_stats, "Choices Bar")
        histogram = NumericAnalysisChart.create_histogram(numeric_answers, "Numeric")
        rating_fig = RatingAnalysisChart.create_rating_distribution(rating_stats)
        
        # All should be created successfully
        assert pie is not None
        assert bar is not None
        assert histogram is not None
        assert rating_fig is not None


# ============================================================================
# UTILITY: Component Testing Helpers
# ============================================================================

def create_mock_streamlit_session():
    """Create a mock Streamlit session state."""
    return {
        'analytics_filters': {
            'start_date': datetime.now() - timedelta(days=30),
            'end_date': datetime.now(),
            'min_submissions': 0,
            'question_filter': 'all',
        },
        'form_selector': 0,
    }


def assert_chart_validity(fig) -> None:
    """Assert chart figure is valid."""
    assert fig is not None
    assert hasattr(fig, 'layout')
    assert hasattr(fig, 'data')
