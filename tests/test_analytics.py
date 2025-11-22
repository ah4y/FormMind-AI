"""
Tests for analytics and metrics calculations
TEAMMATE B: Expand these tests as services are implemented
"""
# These imports will work once Leader implements the services
# from app.services.analytics import choice_stats, numeric_stats, text_table

import pytest


# Basic placeholder functions for now - TEAMMATE B can test these
def choice_stats(question, answers):
    """Placeholder function - Leader will implement in services/analytics.py"""
    stats = {}
    for answer in answers:
        # Handle both single choices and comma-separated multiple choices
        choices = answer['value'].split(',') if ',' in answer['value'] else [answer['value']]
        for choice in choices:
            choice = choice.strip()
            stats[choice] = stats.get(choice, 0) + 1
    return stats

def numeric_stats(answers):
    """Placeholder function - Leader will implement in services/analytics.py"""
    valid_numbers = []
    for answer in answers:
        try:
            num = float(answer['value'])
            valid_numbers.append(num)
        except (ValueError, TypeError):
            continue
    
    if not valid_numbers:
        return {'count': 0, 'min': None, 'max': None, 'average': None}
    
    return {
        'count': len(valid_numbers),
        'min': min(valid_numbers),
        'max': max(valid_numbers),
        'average': sum(valid_numbers) / len(valid_numbers)
    }

def text_table(answers, limit=10):
    """Placeholder function - Leader will implement in services/analytics.py"""
    # Return last N answers as strings
    text_answers = [answer['value'] for answer in answers if answer['value'].strip()]
    return text_answers[-limit:]


class TestChoiceStatistics:
    """Tests for radio/dropdown/checkbox statistics"""
    
    def test_choice_stats_simple_radio(self):
        """Test basic choice counting for radio buttons"""
        question = {'id': 1}
        answers = [
            {'value': 'A'},
            {'value': 'B'},
            {'value': 'A'},
            {'value': 'A'}
        ]
        stats = choice_stats(question, answers)
        assert stats['A'] == 3
        assert stats['B'] == 1
    
    def test_choice_stats_multiple_checkbox(self):
        """Test counting for checkbox (multiple selection)"""
        question = {'id': 1}
        answers = [
            {'value': 'A'},
            {'value': 'B'},
            {'value': 'A'},
            {'value': 'A,B'},  # Multiple selection
        ]
        stats = choice_stats(question, answers)
        assert stats['A'] == 3  # A appears in 3 answers
        assert stats['B'] == 2  # B appears in 2 answers


class TestNumericStatistics:
    """Tests for integer/decimal field statistics"""
    
    def test_numeric_stats_basic(self):
        """Test basic numeric statistics"""
        answers = [{'value': '1'}, {'value': '2.5'}, {'value': '3'}]
        s = numeric_stats(answers)
        assert s['count'] == 3
        assert s['min'] == 1.0
        assert s['max'] == 3.0
        assert s['average'] == 2.1666666666666665  # (1 + 2.5 + 3) / 3
    
    def test_numeric_stats_with_invalid(self):
        """Test numeric stats ignoring invalid values"""
        answers = [{'value': '1'}, {'value': '2.5'}, {'value': 'bad'}, {'value': ''}]
        s = numeric_stats(answers)
        assert s['count'] == 2
        assert s['min'] == 1.0
        assert s['max'] == 2.5
    
    def test_numeric_stats_empty(self):
        """Test numeric stats with no valid numbers"""
        answers = [{'value': 'bad'}, {'value': 'text'}, {'value': ''}]
        s = numeric_stats(answers)
        assert s['count'] == 0
        assert s['min'] is None
        assert s['max'] is None
        assert s['average'] is None


class TestTextStatistics:
    """Tests for text response handling"""
    
    def test_text_table_basic(self):
        """Test basic text table generation"""
        answers = [{'value': 'first'}, {'value': 'second'}, {'value': 'third'}]
        t = text_table(answers, limit=5)
        assert len(t) == 3
        assert t == ['first', 'second', 'third']
    
    def test_text_table_with_limit(self):
        """Test text table respects limit"""
        answers = [{'value': str(i)} for i in range(20)]
        t = text_table(answers, limit=5)
        assert len(t) == 5
        assert t == ['15', '16', '17', '18', '19']  # Last 5 entries
    
    def test_text_table_filters_empty(self):
        """Test text table filters out empty responses"""
        answers = [{'value': 'good'}, {'value': ''}, {'value': '  '}, {'value': 'also good'}]
        t = text_table(answers, limit=10)
        assert len(t) == 2
        assert 'good' in t
        assert 'also good' in t


# Additional test classes for TEAMMATE B to expand:

class TestSummaryMetrics:
    """Tests for high-level form metrics - TEAMMATE B: add these"""
    
    def test_placeholder_submission_counts(self):
        """TODO: Test total submission counting"""
        assert True  # Expand this test
    
    def test_placeholder_unique_users(self):
        """TODO: Test unique logged-in user counting"""
        assert True  # Expand this test
    
    def test_placeholder_guest_submissions(self):
        """TODO: Test guest submission counting"""
        assert True  # Expand this test


class TestVersionAwareAnalytics:
    """Tests for per-version analytics - TEAMMATE B: focus on these"""
    
    def test_placeholder_version_filtering(self):
        """TODO: Test analytics filtered by form version"""
        assert True  # Expand this test


# TEAMMATE B INSTRUCTIONS:
# 1. Run `pytest tests/test_analytics.py -v` to see these tests pass
# 2. Once Leader implements services/analytics.py, uncomment the imports at the top
# 3. Expand the placeholder tests with real functionality
# 4. Add tests for rating calculations and distribution
# 5. Add tests for version-aware analytics filtering


class TestRatingAnalytics:
    """Tests for rating field statistics (1-5 star ratings)"""
    
    def test_rating_distribution(self):
        """Test counting of rating distributions"""
        answers = [
            {'value': '5'},
            {'value': '4'},
            {'value': '5'},
            {'value': '3'},
            {'value': '5'}
        ]
        stats = choice_stats({}, answers)
        assert stats['5'] == 3
        assert stats['4'] == 1
        assert stats['3'] == 1
        
        # Calculate average rating
        total_rating = sum(int(k) * v for k, v in stats.items())
        avg_rating = total_rating / sum(stats.values())
        assert avg_rating == 4.4  # (5+4+5+3+5) / 5 = 22/5 = 4.4
    
    def test_rating_edge_cases(self):
        """Test rating distribution with edge cases"""
        answers = [{'value': '1'}, {'value': '5'}]
        stats = choice_stats({}, answers)
        assert len(stats) == 2
        assert stats['1'] == 1
        assert stats['5'] == 1


class TestMultipleChoiceAnalytics:
    """Tests for checkbox/multiple choice analytics"""
    
    def test_checkbox_overlap(self):
        """Test overlapping selections in checkbox fields"""
        answers = [
            {'value': 'Python'},
            {'value': 'Python,JavaScript'},
            {'value': 'JavaScript'},
            {'value': 'Python,JavaScript,Go'}
        ]
        stats = choice_stats({}, answers)
        assert stats['Python'] == 3
        assert stats['JavaScript'] == 3
        assert stats['Go'] == 1
    
    def test_checkbox_with_spaces(self):
        """Test handling of spaces in checkbox selections"""
        answers = [
            {'value': 'Option A, Option B'},
            {'value': 'Option A'},
            {'value': 'Option B, Option C'}
        ]
        stats = choice_stats({}, answers)
        assert stats['Option A'] == 2
        assert stats['Option B'] == 2
        assert stats['Option C'] == 1


class TestNumericAnomalies:
    """Tests for edge cases in numeric data analysis"""
    
    def test_numeric_with_decimals(self):
        """Test handling of decimal values"""
        answers = [{'value': '3.14'}, {'value': '2.71'}, {'value': '1.41'}]
        s = numeric_stats(answers)
        assert s['count'] == 3
        assert abs(s['average'] - 2.42) < 0.01
    
    def test_numeric_with_negative(self):
        """Test negative number statistics"""
        answers = [{'value': '-5'}, {'value': '10'}, {'value': '0'}]
        s = numeric_stats(answers)
        assert s['min'] == -5
        assert s['max'] == 10
        assert s['average'] == 5.0 / 3
    
    def test_numeric_single_value(self):
        """Test numeric stats with single valid answer"""
        answers = [{'value': '42'}]
        s = numeric_stats(answers)
        assert s['count'] == 1
        assert s['min'] == 42
        assert s['max'] == 42
        assert s['average'] == 42


class TestTextResponseAnalytics:
    """Tests for text response collection and display"""
    
    def test_text_table_ordering(self):
        """Test that text table returns newest responses first"""
        answers = [{'value': f'Response {i}'} for i in range(1, 6)]
        t = text_table(answers, limit=3)
        assert t == ['Response 3', 'Response 4', 'Response 5']
    
    def test_text_table_mixed_content(self):
        """Test text table with mixed empty and filled responses"""
        answers = [
            {'value': 'Good'},
            {'value': ''},
            {'value': 'Better'},
            {'value': '   '},
            {'value': 'Best'}
        ]
        t = text_table(answers, limit=10)
        assert len(t) == 3
        assert 'Good' in t
        assert 'Better' in t
        assert 'Best' in t


class TestAnalyticsAggregation:
    """Tests for combining multiple question analytics"""
    
    def test_combined_form_metrics(self):
        """Test creating summary metrics across multiple questions"""
        # Simulate analytics for a form with 3 questions
        q1_stats = choice_stats({}, [{'value': 'A'}, {'value': 'A'}, {'value': 'B'}])
        q2_stats = numeric_stats([{'value': '8'}, {'value': '9'}, {'value': '7'}])
        q3_text = text_table([{'value': 'Feedback 1'}, {'value': 'Feedback 2'}])
        
        assert len(q1_stats) == 2
        assert q2_stats['count'] == 3
        assert len(q3_text) == 2
    
    def test_empty_form_response(self):
        """Test handling of forms with no responses"""
        stats = choice_stats({}, [])
        metrics = numeric_stats([])
        text = text_table([])
        
        assert stats == {}
        assert metrics['count'] == 0
        assert text == []
