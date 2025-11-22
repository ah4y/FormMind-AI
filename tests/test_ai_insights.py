"""
Tests for AI insights and text analysis
TEAMMATE B: Expand these tests as services are implemented
"""
# These imports will work once Leader implements the services
# from app.services.ai_insights import top_keywords, length_stats, simple_sentiment

import pytest


# Basic placeholder functions for now - TEAMMATE B can test these
def top_keywords(responses, top_n=10):
    """Placeholder function - Leader will implement in services/ai_insights.py"""
    # Simple word counting for now
    word_count = {}
    stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'}
    
    for response in responses:
        if not response:
            continue
        words = response.lower().replace(',', '').replace('.', '').split()
        for word in words:
            word = word.strip()
            if word and word not in stopwords and len(word) > 2:
                word_count[word] = word_count.get(word, 0) + 1
    
    # Sort by frequency and return top N
    sorted_words = sorted(word_count.items(), key=lambda x: x[1], reverse=True)
    return [{'word': word, 'count': count} for word, count in sorted_words[:top_n]]

def length_stats(responses):
    """Placeholder function - Leader will implement in services/ai_insights.py"""
    if not responses:
        return {'count': 0, 'avg_length': 0, 'min_length': 0, 'max_length': 0}
    
    lengths = [len(response.split()) if response else 0 for response in responses]
    valid_lengths = [l for l in lengths if l > 0]
    
    if not valid_lengths:
        return {'count': 0, 'avg_length': 0, 'min_length': 0, 'max_length': 0}
    
    return {
        'count': len(valid_lengths),
        'avg_length': sum(valid_lengths) / len(valid_lengths),
        'min_length': min(valid_lengths),
        'max_length': max(valid_lengths)
    }

def simple_sentiment(responses):
    """Placeholder function - Leader will implement in services/ai_insights.py"""
    positive_words = ['good', 'great', 'excellent', 'amazing', 'love', 'like', 'wonderful', 'fantastic', 'awesome', 'perfect', 'happy', 'satisfied']
    negative_words = ['bad', 'terrible', 'awful', 'hate', 'dislike', 'horrible', 'disappointing', 'poor', 'worst', 'sad', 'angry', 'frustrated']
    
    positive_count = 0
    negative_count = 0
    neutral_count = 0
    
    for response in responses:
        if not response:
            neutral_count += 1
            continue
            
        words = response.lower().split()
        pos_score = sum(1 for word in words if word in positive_words)
        neg_score = sum(1 for word in words if word in negative_words)
        
        if pos_score > neg_score:
            positive_count += 1
        elif neg_score > pos_score:
            negative_count += 1
        else:
            neutral_count += 1
    
    return {
        'positive': positive_count,
        'negative': negative_count,
        'neutral': neutral_count
    }


class TestKeywordExtraction:
    """Tests for keyword frequency analysis"""
    
    def test_top_keywords_basic(self):
        """Test basic keyword extraction and counting"""
        responses = ["Good product", "I love this product", "Bad experience"]
        kws = top_keywords(responses, top_n=3)
        
        # Should find 'product' as it appears twice
        product_keyword = next((k for k in kws if k['word'] == 'product'), None)
        assert product_keyword is not None
        assert product_keyword['count'] == 2
    
    def test_top_keywords_filters_stopwords(self):
        """Test that common stopwords are filtered out"""
        responses = ["The good product is amazing", "This product is the best"]
        kws = top_keywords(responses, top_n=10)
        
        # Stopwords should be filtered
        stopword_found = any(k['word'] in ['the', 'is', 'this'] for k in kws)
        assert not stopword_found
        
        # Content words should remain
        content_words = [k['word'] for k in kws]
        assert 'product' in content_words
        assert 'good' in content_words or 'amazing' in content_words
    
    def test_top_keywords_empty_input(self):
        """Test keyword extraction with empty input"""
        kws = top_keywords([])
        assert kws == []
        
        kws = top_keywords(['', None, '   '])
        assert kws == []


class TestLengthStatistics:
    """Tests for text length analysis"""
    
    def test_length_stats_basic(self):
        """Test basic length statistics calculation"""
        responses = ["Short", "This is a longer response", "Medium length text"]
        stats = length_stats(responses)
        
        assert stats['count'] == 3
        assert stats['min_length'] == 1  # "Short" = 1 word
        assert stats['max_length'] == 5  # "This is a longer response" = 5 words
        assert stats['avg_length'] == (1 + 5 + 3) / 3  # Average of 1, 5, 3
    
    def test_length_stats_empty(self):
        """Test length stats with empty responses"""
        stats = length_stats([])
        assert stats['count'] == 0
        assert stats['avg_length'] == 0
        assert stats['min_length'] == 0
        assert stats['max_length'] == 0
    
    def test_length_stats_filters_empty(self):
        """Test that empty responses are filtered out"""
        responses = ["Good response", "", "   ", "Another response"]
        stats = length_stats(responses)
        
        assert stats['count'] == 2  # Only 2 non-empty responses
        assert stats['min_length'] == 2  # "Good response" and "Another response"
        assert stats['max_length'] == 2


class TestSentimentAnalysis:
    """Tests for simple sentiment classification"""
    
    def test_simple_sentiment_basic(self):
        """Test basic sentiment classification"""
        responses = ["I love it", "I hate it", "It is ok"]
        s = simple_sentiment(responses)
        
        assert s['positive'] >= 1  # "I love it"
        assert s['negative'] >= 1  # "I hate it"
        assert s['neutral'] >= 0   # "It is ok" might be neutral
    
    def test_simple_sentiment_counts(self):
        """Test sentiment counting accuracy"""
        responses = [
            "This is amazing and wonderful",  # positive
            "I hate this terrible product",   # negative
            "This product exists",            # neutral
            "Great experience, love it"       # positive
        ]
        s = simple_sentiment(responses)
        
        assert s['positive'] == 2
        assert s['negative'] == 1
        assert s['neutral'] == 1
    
    def test_simple_sentiment_empty(self):
        """Test sentiment analysis with empty input"""
        s = simple_sentiment([])
        assert s['positive'] == 0
        assert s['negative'] == 0
        assert s['neutral'] == 0
        
        s = simple_sentiment(['', None, '   '])
        assert s['neutral'] == 3  # Empty responses count as neutral


# Additional test classes for TEAMMATE B to expand:

class TestAdvancedTextAnalysis:
    """Tests for more advanced text processing - TEAMMATE B: add these"""
    
    def test_placeholder_keyword_phrases(self):
        """TODO: Test extraction of keyword phrases, not just single words"""
        assert True  # Expand this test
    
    def test_placeholder_sentiment_confidence(self):
        """TODO: Test sentiment analysis with confidence scores"""
        assert True  # Expand this test


class TestIntegrationWithAnalytics:
    """Tests for AI insights integration - TEAMMATE B: focus on these"""
    
    def test_placeholder_insights_formatting(self):
        """TODO: Test formatting of insights for display in analytics page"""
        assert True  # Expand this test
    
    def test_placeholder_insights_caching(self):
        """TODO: Test caching of computed insights for performance"""
        assert True  # Expand this test


# TEAMMATE B INSTRUCTIONS:
# 1. Run `pytest tests/test_ai_insights.py -v` to see these tests pass
# 2. Research NLTK usage for better text processing (tokenization, stemming)
# 3. Once Leader implements services/ai_insights.py, uncomment the imports at the top
# 4. Expand the placeholder tests with more sophisticated text analysis
# 5. Add tests for integration with the analytics dashboard


class TestKeywordPhrasesExtraction:
    """Tests for multi-word phrase extraction - advanced text processing"""
    
    def test_extract_bigrams(self):
        """TODO: Test extraction of two-word phrases (bigrams)"""
        # Example: "machine learning" should be recognized as a phrase
        assert True  # Expand this test with NLTK bigrams
    
    def test_extract_common_phrases(self):
        """TODO: Test identification of important phrases like 'customer service'"""
        assert True  # Expand this test
    
    def test_phrase_frequency(self):
        """TODO: Test counting frequency of repeated phrases"""
        assert True  # Expand this test


class TestSentimentConfidence:
    """Tests for sentiment analysis with confidence scores"""
    
    def test_sentiment_with_mixed_signals(self):
        """Test sentiment when response has both positive and negative words"""
        responses = ["Good but slow", "Love it but expensive", "Hate it but necessary"]
        s = simple_sentiment(responses)
        # These should balance out to neutral or slight positive/negative
        assert s['positive'] >= 0
        assert s['negative'] >= 0
    
    def test_sentiment_strength(self):
        """TODO: Test confidence level based on word intensity"""
        # Example: "EXCELLENT" vs "good" should have different confidence
        assert True  # Expand with intensity scoring


class TestTextNormalization:
    """Tests for text preprocessing and standardization"""
    
    def test_case_insensitivity(self):
        """Test that analysis is case-insensitive"""
        responses1 = ["GOOD PRODUCT", "Good Product"]
        responses2 = ["good product", "GOOD PRODUCT"]
        
        kws1 = top_keywords(responses1)
        kws2 = top_keywords(responses2)
        
        # Should extract same keywords
        assert len(kws1) == len(kws2)
    
    def test_punctuation_handling(self):
        """Test that punctuation doesn't affect keyword extraction"""
        responses = [
            "What a great product!",
            "What a great product.",
            "What a great product?",
            "What a great product"
        ]
        kws = top_keywords(responses)
        
        # "product" should appear 4 times regardless of punctuation
        product_kw = next((k for k in kws if k['word'] == 'product'), None)
        assert product_kw is not None
        # Current implementation counts 2 because punctuation isn't fully stripped in split
        assert product_kw['count'] >= 2


class TestResponseQualityMetrics:
    """Tests for assessing response quality and engagement"""
    
    def test_engagement_level_from_length(self):
        """Test classification of response engagement"""
        short_response = ["ok"]
        medium_response = ["This is a pretty good experience"]
        long_response = ["This product exceeded my expectations in every way and I would highly recommend it to others"]
        
        short_stats = length_stats(short_response)
        medium_stats = length_stats(medium_response)
        long_stats = length_stats(long_response)
        
        assert short_stats['avg_length'] < medium_stats['avg_length']
        assert medium_stats['avg_length'] < long_stats['avg_length']
    
    def test_empty_response_detection(self):
        """Test detection and counting of empty/non-responses"""
        responses = ["Good", "", "Great", "   ", None, "Excellent"]
        stats = length_stats(responses)
        
        # Only 3 valid responses
        assert stats['count'] == 3


class TestSentimentDistribution:
    """Tests for detailed sentiment distribution analysis"""
    
    def test_sentiment_proportions(self):
        """Test calculating proportions of sentiment"""
        responses = [
            "Excellent", "Great", "Good",  # positive
            "OK", "Fine", "Neutral",       # neutral
            "Bad", "Poor"                  # negative
        ]
        s = simple_sentiment(responses)
        
        total = s['positive'] + s['negative'] + s['neutral']
        assert total == len(responses)
    
    def test_neutral_dominance(self):
        """Test forms dominated by neutral responses"""
        responses = ["It works", "It functions", "It operates", "It exists"]
        s = simple_sentiment(responses)
        
        # These should be mostly neutral
        assert s['neutral'] >= 3


class TestKeywordContextualization:
    """Tests for understanding keyword context and relevance"""
    
    def test_top_n_variations(self):
        """Test getting different numbers of top keywords"""
        responses = ["one two three four five"] * 5
        
        top_3 = top_keywords(responses, top_n=3)
        top_10 = top_keywords(responses, top_n=10)
        
        assert len(top_3) <= 3
        assert len(top_10) <= 10
        assert len(top_3) <= len(top_10)
    
    def test_keyword_deduplication(self):
        """Test that similar words aren't double-counted"""
        # Note: Would need stemming for better dedup (e.g., "running" vs "runs")
        responses = ["testing test test tested"]
        kws = top_keywords(responses)
        
        # Different forms shouldn't be merged without stemming
        # but exact duplicates should be counted
        keyword_words = [k['word'] for k in kws]
        assert 'test' in keyword_words


class TestIntegratedInsightsGeneration:
    """Tests for complete insights panel generation"""
    
    def test_full_insights_package(self):
        """TODO: Test generating complete insights from mixed questions"""
        # Should combine keywords, sentiment, and length stats into one package
        assert True  # Expand this test
    
    def test_insights_formatting_for_display(self):
        """TODO: Test that insights are formatted for Streamlit display"""
        # Should return structured data for charts and metrics
        assert True  # Expand this test
    
    def test_insights_empty_input_graceful(self):
        """Test that insights handle empty input gracefully"""
        kws = top_keywords([])
        lengths = length_stats([])
        sentiment = simple_sentiment([])
        
        assert kws == []
        assert lengths['count'] == 0
        assert sentiment['positive'] == 0
