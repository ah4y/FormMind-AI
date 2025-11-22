# FormMind AI Insights - Algorithm Documentation

**Author**: Teammate B (Analytics & AI Insights)  
**Last Updated**: November 22, 2025

## Overview

FormMind includes a lightweight AI analysis layer that processes text responses without relying on external APIs. This document details the algorithms used for keyword extraction, sentiment analysis, and text statistics.

---

## 1. Keyword Extraction

### Algorithm: Frequency-Based Word Counting with Stopword Filtering

#### Purpose
Identify the most frequently mentioned topics or concepts in text responses.

#### Implementation
1. **Text Tokenization**: Split responses into individual words
2. **Normalization**: Convert to lowercase and remove punctuation
3. **Stopword Filtering**: Exclude common words that don't carry meaning
4. **Word Length Filter**: Exclude words shorter than 3 characters (reduces noise)
5. **Frequency Counting**: Count occurrences of each word
6. **Sorting**: Return top N words sorted by frequency (descending)

#### Stopwords
The following English words are filtered out:
- Articles: the, a, an
- Conjunctions: and, or, but
- Prepositions: in, on, at, to, for, of, with, by
- Verb forms: is, are, was, were, be, been, have, has, had, do, does, did
- Modals: will, would, could, should, may, might, can
- Pronouns: I, you, he, she, it, we, they, me, him, her, us, them
- Demonstratives: this, that, these, those

#### Example
**Input Responses**:
```
"The product quality is excellent and I love it"
"Great quality but the delivery was slow"
"Quality seems good, will order again"
```

**Processing**:
1. Tokenize and lowercase: ["the", "product", "quality", "is", "excellent", ...]
2. Remove stopwords and short words: ["product", "quality", "excellent", "love", ...]
3. Count frequencies: {"product": 1, "quality": 3, "excellent": 1, "love": 1, ...}
4. Return top 10: [{"word": "quality", "count": 3}, {"word": "excellent", "count": 1}, ...]

#### Use Cases
- Identify common praise/complaint topics
- Find trending themes in feedback
- Understand customer focus areas

#### Future Enhancements (with NLTK)
- **Stemming**: Combine "running", "runs", "run" → "run"
- **Lemmatization**: Combine "better", "best" → "good"
- **Bigrams**: Extract 2-word phrases like "customer service"
- **TF-IDF**: Weight words by importance across all forms

---

## 2. Sentiment Analysis

### Algorithm: Lexicon-Based Sentiment Scoring

#### Purpose
Classify text responses as positive, negative, or neutral to understand overall satisfaction.

#### Implementation
1. **Word Tokenization**: Split text into words
2. **Positive Word Detection**: Count words in positive lexicon
3. **Negative Word Detection**: Count words in negative lexicon
4. **Net Score Calculation**: positive_count - negative_count
5. **Classification**: 
   - If positive_count > negative_count → **Positive**
   - If negative_count > positive_count → **Negative**
   - Otherwise → **Neutral**

#### Sentiment Lexicons

**Positive Words** (12 common):
```
good, great, excellent, amazing, love, like, wonderful, 
fantastic, awesome, perfect, happy, satisfied
```

**Negative Words** (12 common):
```
bad, terrible, awful, hate, dislike, horrible, disappointing, 
poor, worst, sad, angry, frustrated
```

#### Example
**Input Responses**:
```
"I love this product, it's amazing" → positive_count=2, negative_count=0 → POSITIVE
"Terrible quality, very disappointed" → positive_count=0, negative_count=2 → NEGATIVE
"The product exists" → positive_count=0, negative_count=0 → NEUTRAL
"Great product but slow delivery" → positive_count=1, negative_count=1 → NEUTRAL
```

#### Use Cases
- Get quick satisfaction gauge
- Identify forms with primarily negative/positive feedback
- Track sentiment trends over time
- Flag problematic areas for investigation

#### Limitations & Future Improvements
- **Negation Handling**: "not good" is currently counted as 0, not as negative
- **Intensifiers**: "AMAZING" treated same as "amazing" (could use all-caps detection)
- **Domain-Specific Terms**: Lexicon is generic, not customized per industry
- **Context Awareness**: Machine learning models (VADER, TextBlob) for better accuracy
- **Emoji Support**: Add emoji sentiment mapping

#### NLTK Enhancement Path
```python
from nltk.sentiment import SentimentIntensityAnalyzer

sia = SentimentIntensityAnalyzer()
scores = sia.polarity_scores("I love this product!")
# Returns: {'neg': 0.0, 'neu': 0.295, 'pos': 0.705, 'compound': 0.818}
```

---

## 3. Text Length Statistics

### Algorithm: Response Length Analysis

#### Purpose
Understand engagement levels and response depth across feedback.

#### Implementation
1. **Word Count**: Split response by whitespace and count tokens
2. **Filter Empty**: Exclude responses with 0 words
3. **Calculate Metrics**:
   - **Count**: Number of non-empty responses
   - **Min Length**: Shortest response (in words)
   - **Max Length**: Longest response (in words)
   - **Average Length**: Mean response length

#### Formula
```
avg_length = sum(response_lengths) / count(non_empty_responses)
```

#### Example
**Input Responses**:
```
"Good"                                          → 1 word
"This is a detailed review"                    → 5 words
"Amazing product with excellent quality"       → 5 words
""                                              → 0 words (filtered)
"The best purchase I've made"                  → 6 words
```

**Calculation**:
- Valid responses: [1, 5, 5, 6]
- Count: 4
- Min: 1
- Max: 6
- Average: (1 + 5 + 5 + 6) / 4 = 4.25

#### Use Cases
- **Engagement Measurement**: Longer responses = more engagement
- **Form Quality**: Low average length might indicate unclear questions
- **Response Patterns**: Compare lengths across questions/forms
- **Data Quality**: Very short responses might indicate rushing/low effort

#### Engagement Tiers (Suggested)
- **Low Engagement**: 1-2 words average
- **Medium Engagement**: 3-6 words average
- **High Engagement**: 7+ words average

---

## 4. Analytics Integration

### Data Flow

```
Raw Submissions
    ↓
Extract Text Responses
    ↓
┌─────────────────────────────────────────┐
│     Parallel Processing                 │
├─────────────────────────────────────────┤
│ Keyword Extraction  │  Sentiment Analysis │ Length Stats │
│ (top_keywords)      │  (simple_sentiment) │ (length_stats) │
└─────────────────────────────────────────┘
    ↓
Format for Display
    ↓
Streamlit Dashboard
```

### Performance Considerations

1. **Caching**: Cache computed insights to avoid recalculation
2. **Batch Processing**: Process responses in batches if large dataset
3. **Lazy Loading**: Calculate insights only when user views analytics page
4. **Sample for Preview**: Show insights for first 100 responses in preview

#### Pseudocode: Efficient Insight Calculation
```python
def calculate_insights(submission_ids, cache_manager):
    cached = cache_manager.get(submission_ids)
    if cached and still_valid(cached):
        return cached
    
    responses = fetch_responses(submission_ids)
    insights = {
        'keywords': top_keywords(responses, top_n=10),
        'sentiment': simple_sentiment(responses),
        'length_stats': length_stats(responses)
    }
    
    cache_manager.set(submission_ids, insights, ttl=3600)
    return insights
```

---

## 5. Version-Aware Analytics

### Concept
When a form is edited after collecting submissions, FormMind creates a new version. Analytics can be calculated:
- Per version (only submissions for that version)
- Across all versions (combined analytics)

### Implementation
```python
def get_version_responses(form_id, version_num=None):
    """
    If version_num provided:
        Return responses only for that version
    Else:
        Return responses for all versions
    """
    if version_num:
        query = submissions.filter(form_id, version_num)
    else:
        query = submissions.filter(form_id)
    return extract_text_responses(query)
```

### Use Cases
- Compare how question changes affect feedback
- Track sentiment trends across versions
- Identify if improvements in form clarity affect response quality

---

## 6. Research Notes: NLTK Integration

### Current Status
NLTK is listed in `requirements.txt` but not yet integrated.

### Recommended NLTK Features to Add

#### 1. **Tokenization** (Better than `.split()`)
```python
from nltk.tokenize import word_tokenize
tokens = word_tokenize("I don't like it!")
# Result: ['I', 'do', "n't", 'like', 'it', '!']
```
**Benefit**: Handles contractions, punctuation better

#### 2. **Stemming** (Combine word variations)
```python
from nltk.stem import PorterStemmer
stemmer = PorterStemmer()
print([stemmer.stem(w) for w in ['running', 'runs', 'ran']])
# Result: ['run', 'run', 'ran']
```
**Benefit**: "quality", "qualities", "qualified" → "qualiti"

#### 3. **Stopword Filtering** (Official NLTK stopwords)
```python
from nltk.corpus import stopwords
stop_words = set(stopwords.words('english'))
# 179 English stopwords vs our 40
```
**Benefit**: More comprehensive filtering

#### 4. **Part-of-Speech Tagging** (Identify word types)
```python
from nltk import pos_tag, word_tokenize
pos_tag(word_tokenize("good product"))
# Result: [('good', 'JJ'), ('product', 'NN')]
```
**Benefit**: Extract only adjectives (e.g., "good", "excellent") for better sentiment

#### 5. **Bigrams/Trigrams** (Multi-word phrases)
```python
from nltk import bigrams
list(bigrams("customer service is great".split()))
# Result: [('customer', 'service'), ('service', 'is'), ('is', 'great')]
```
**Benefit**: Identify phrases like "customer service"

### Implementation Priority
1. **High**: Stemming, Better Tokenization
2. **Medium**: Official Stopwords, POS Tagging
3. **Low**: Bigrams, Lemmatization

### Setup Code (to add to services/ai_insights.py)
```python
import nltk
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from nltk.tokenize import word_tokenize

# Download required NLTK data (run once)
# nltk.download('punkt')
# nltk.download('stopwords')

stemmer = PorterStemmer()
stop_words = set(stopwords.words('english'))
```

---

## 7. Testing Strategy

### Test Categories (See `tests/test_ai_insights.py`)

#### Unit Tests
- Keyword extraction with various inputs
- Sentiment classification accuracy
- Length calculation correctness
- Edge cases (empty strings, special characters)

#### Integration Tests
- Combining multiple text fields
- Caching consistency
- Version filtering

#### Performance Tests
- Benchmark with 1000+ responses
- Memory usage profiling
- Cache hit rates

### Sample Test Data
See `sample_analytics_data.json` for realistic test datasets.

---

## 8. Future Enhancements

### Short-term (Phase 2)
- Add NLTK stemming for better keyword grouping
- Implement phrase extraction (bigrams)
- Add POS tagging for better sentiment

### Medium-term (Phase 3)
- Machine learning-based sentiment (VADER, TextBlob)
- Topic modeling (Latent Dirichlet Allocation)
- Emotion detection (happy, sad, angry, surprised)

### Long-term
- Custom domain-specific lexicons per industry
- Multi-language support
- Deep learning models (BERT, GPT-based analysis)

---

## 9. References & Resources

### Official Documentation
- [NLTK Book - Text Processing](https://www.nltk.org/book/)
- [NLTK Sentiment Analysis](https://www.nltk.org/howto/sentiment_analysis.html)

### Related Papers
- Porter, M. (1980). An algorithm for suffix stripping.
- Pang et al. (2002). Thumbs up? Sentiment Classification

### Tools & Libraries
- **NLTK**: Natural Language Toolkit
- **TextBlob**: Simplified NLP (alternative)
- **spaCy**: Industrial NLP
- **Transformers (HuggingFace)**: State-of-the-art models

---

**Document maintained by**: Teammate B  
**Questions?** Reach out in team Slack or GitHub issues.
