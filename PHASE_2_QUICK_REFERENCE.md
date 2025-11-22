# Phase 2 Quick Reference Guide

## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the app
streamlit run app/main.py

# 3. Sign in with demo account
# 4. Click "Enhanced Analytics" to see Phase 2 dashboard
```

## 📁 Phase 2 Files

| File | Purpose |
|------|---------|
| `app/pages/analytics_dashboard.py` | Main analytics dashboard with all components |
| `tests/test_integration_analytics.py` | 30+ integration tests |
| `tests/test_performance_analytics.py` | 25+ performance tests |
| `tests/test_ui_components.py` | 35+ UI component tests |
| `app/main.py` | Updated with Phase 2 integration |

## 🧩 Core Components

### MetricCard
```python
from app.pages.analytics_dashboard import MetricCard

card = MetricCard("Total Submissions", 150, suffix=" forms", icon="📝")
```

### Charts
```python
from app.pages.analytics_dashboard import ChoiceDistributionChart

# Pie chart for choice distribution
fig = ChoiceDistributionChart.create_pie_chart(stats, "Title")

# Bar chart
fig = ChoiceDistributionChart.create_bar_chart(stats, "Title")

# Percentage table
df = ChoiceDistributionChart.create_percentage_table(stats)
```

### Filters
```python
from app.pages.analytics_dashboard import AnalyticsFilter

filter_mgr = AnalyticsFilter()
filters = filter_mgr.render_filters()
filtered = filter_mgr.apply_filters(submissions, filters)
```

## 📊 Analytics Functions

```python
from app.services.analytics import (
    summary_metrics,      # Get form metrics
    choice_stats,         # Analyze choice responses
    numeric_stats,        # Analyze numeric responses
    text_table            # Get recent text responses
)

# Get overview metrics
metrics = summary_metrics(form, submissions)
# Returns: {total_submissions, unique_users, guest_submissions, is_open}

# Analyze choices (radio, checkbox, dropdown)
stats = choice_stats(question, answers)
# Returns: {option: count, ...}

# Analyze numbers
stats = numeric_stats(answers)
# Returns: {count, min, max, avg}

# Get text responses
recent = text_table(answers, limit=10)
# Returns: [response1, response2, ...]
```

## 🧪 Running Tests

```bash
# All tests
pytest tests/ -v

# Specific test file
pytest tests/test_integration_analytics.py -v

# With coverage
pytest tests/ --cov=app

# Specific test class
pytest tests/test_performance_analytics.py::TestMetricsPerformance -v

# Run with output
pytest tests/test_ui_components.py -v -s
```

## 📈 Dashboard Navigation

1. **Sign In** → Select demo account from sidebar
2. **Dashboard** → View forms and click "View Analytics"
3. **Enhanced Analytics** → Full Phase 2 dashboard
4. **Filters** → Date range, min submissions, question filter
5. **Charts** → Click question tabs to see specific analytics
6. **Export** → Download CSV reports

## 🎯 Key Features

| Feature | Location |
|---------|----------|
| Metric Cards | Top of dashboard |
| Form Details | Below metrics |
| Question Analytics | Tab-based layout |
| Filters | Sidebar |
| Charts | Question tabs |
| Export | Bottom of dashboard |

## ⚡ Performance Targets

- Metrics: < 100ms (1K), < 200ms (10K)
- Choice Stats: < 50ms (1K), < 100ms (10K)
- Full Analytics: < 500ms (1K), < 1s (10K)

## 🔍 Chart Types by Field Type

| Field Type | Chart |
|-----------|-------|
| Radio | Pie + Bar |
| Checkbox | Pie + Bar |
| Dropdown | Pie + Bar |
| Rating | Bar (1-5) + Avg |
| Integer/Decimal | Histogram + Box Plot |
| Text | Recent Responses |

## 📝 Sample Data Access

```python
from app.pages.analytics_dashboard import get_sample_data

forms, submissions_data, questions_data, answers_data = get_sample_data()
```

## 🧩 Component Usage

### In Streamlit Context
```python
import streamlit as st
from app.pages.analytics_dashboard import render_analytics_dashboard

# Render full dashboard
render_analytics_dashboard(forms, submissions_data, questions_data, answers_data)

# Use individual components
from app.pages.analytics_dashboard import (
    MetricCard,
    MetricsRow,
    ChoiceDistributionChart,
)

cards = [MetricCard("Label", value) for value in values]
row = MetricsRow(cards)
row.render()
```

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| Import errors | Run `pip install -r requirements.txt` |
| Streamlit not found | Verify installation: `pip list \| grep streamlit` |
| Charts not showing | Check plotly: `pip install plotly>=5.0.0` |
| Test failures | Verify conftest.py is in tests/ directory |
| Session state issues | Clear cache: `st.cache_clear()` |

## 📚 Documentation

- Full docs: See `PHASE_2_IMPLEMENTATION.md`
- Component code: `app/pages/analytics_dashboard.py` (docstrings)
- Test examples: `tests/test_*.py`
- Architecture: `PHASE_2_IMPLEMENTATION.md` (Architecture section)

## 🎓 Learning Resources

**Component Architecture:**
- MetricCard: Simple display component
- MetricsRow: Layout container
- AnalyticsFilter: State management
- Chart classes: Visualization factories

**Testing Patterns:**
- Integration: Real data workflows
- Performance: Timing and scaling
- UI: Mock Streamlit interactions

**Data Flow:**
```
Forms → Submissions → Answers
    ↓
[Filter]
    ↓
[Analyze]
    ↓
[Visualize]
    ↓
[Display]
```

## 🚀 Next Steps

1. Run the app: `streamlit run app/main.py`
2. Explore sample data in Enhanced Analytics
3. Run tests: `pytest tests/`
4. Review code: `app/pages/analytics_dashboard.py`
5. Modify for your needs

## 📞 Quick Links

- Tests: `pytest tests/ -v`
- Main App: `streamlit run app/main.py`
- Dashboard Code: `app/pages/analytics_dashboard.py`
- Full Docs: `PHASE_2_IMPLEMENTATION.md`
- Original TODO: `TODO_TEAM.md`

---

**Phase 2 Complete! ✅**
