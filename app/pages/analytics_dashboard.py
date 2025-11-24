"""Analytics Dashboard - Phase 2 enhanced analytics page with charts and filters."""

import sys
import os
from pathlib import Path

# Ensure proper imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from app.services.analytics import summary_metrics, choice_stats, numeric_stats, text_table


# ============================================================================
# METRIC CARDS COMPONENT
# ============================================================================

class MetricCard:
    """Reusable metric card component for displaying key statistics."""
    
    def __init__(self, label: str, value: Any, suffix: str = "", 
                 delta: Optional[float] = None, icon: str = "📊"):
        self.label = label
        self.value = value
        self.suffix = suffix
        self.delta = delta
        self.icon = icon
    
    def render(self) -> None:
        """Render metric card in Streamlit."""
        col1, col2 = st.columns([3, 1])
        with col1:
            st.metric(
                label=self.label,
                value=f"{self.value}{self.suffix}",
                delta=self.delta,
            )
        with col2:
            st.write(f"<div style='font-size: 24px; text-align: center; margin-top: 8px'>{self.icon}</div>", 
                    unsafe_allow_html=True)


class MetricsRow:
    """Container for multiple metric cards displayed in a row."""
    
    def __init__(self, cards: List[MetricCard], cols: int = 4):
        self.cards = cards
        self.cols = min(cols, len(cards)) if cards else 1
    
    def render(self) -> None:
        """Render all cards in columnar layout."""
        if not self.cards:
            st.info("No metrics to display")
            return
        
        columns = st.columns(self.cols)
        for idx, card in enumerate(self.cards):
            with columns[idx % self.cols]:
                card.render()


# ============================================================================
# FILTER COMPONENT
# ============================================================================

class AnalyticsFilter:
    """Manages analytics filters (date range, submission count, etc.)."""
    
    def __init__(self):
        self.initialize_session_state()
    
    def initialize_session_state(self) -> None:
        """Initialize session state for filters."""
        if 'analytics_filters' not in st.session_state:
            st.session_state.analytics_filters = {
                'start_date': datetime.now() - timedelta(days=30),
                'end_date': datetime.now(),
                'min_submissions': 0,
                'question_filter': 'all',
            }
    
    def render_filters(self, available_questions: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Render filter controls in sidebar and return filter dict."""
        st.sidebar.markdown("---")
        st.sidebar.subheader("📅 Filters")
        
        # Date range filter
        col1, col2 = st.sidebar.columns(2)
        with col1:
            start_date = st.date_input(
                "Start Date",
                value=st.session_state.analytics_filters['start_date'].date(),
                key='filter_start_date'
            )
        with col2:
            end_date = st.date_input(
                "End Date",
                value=st.session_state.analytics_filters['end_date'].date(),
                key='filter_end_date'
            )
        
        # Min submissions filter
        min_subs = st.sidebar.slider(
            "Minimum Submissions",
            min_value=0,
            max_value=1000,
            value=st.session_state.analytics_filters['min_submissions'],
            step=10,
            key='filter_min_subs'
        )
        
        # Question filter
        question_options = ['all']
        if available_questions:
            question_options.extend([q['label'] for q in available_questions])
        
        question_filter = st.sidebar.selectbox(
            "Filter by Question",
            options=question_options,
            index=0,
            key='filter_question'
        )
        
        # Update session state
        st.session_state.analytics_filters = {
            'start_date': datetime.combine(start_date, datetime.min.time()),
            'end_date': datetime.combine(end_date, datetime.max.time()),
            'min_submissions': min_subs,
            'question_filter': question_filter,
        }
        
        return st.session_state.analytics_filters
    
    def apply_filters(self, submissions: List[Dict[str, Any]], 
                     filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Apply active filters to submissions list."""
        filtered = submissions
        
        # Apply date range filter
        if 'submitted_at' in (submissions[0] if submissions else {}):
            filtered = [
                s for s in filtered
                if filters['start_date'] <= s['submitted_at'] <= filters['end_date']
            ]
        
        return filtered


# ============================================================================
# CHART COMPONENTS
# ============================================================================

class ChoiceDistributionChart:
    """Component for rendering choice field distribution charts."""
    
    @staticmethod
    def create_pie_chart(stats: Dict[str, int], title: str) -> go.Figure:
        """Create pie chart for choice distribution."""
        if not stats:
            return go.Figure().add_annotation(text="No data available")
        
        labels = list(stats.keys())
        values = list(stats.values())
        
        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            textposition='inside',
            textinfo='percent+label',
            hovertemplate='<b>%{label}</b><br>Count: %{value}<br>%{percent}<extra></extra>'
        )])
        
        fig.update_layout(
            title=title,
            height=400,
            showlegend=True,
        )
        
        return fig
    
    @staticmethod
    def create_bar_chart(stats: Dict[str, int], title: str) -> go.Figure:
        """Create bar chart for choice distribution."""
        if not stats:
            return go.Figure().add_annotation(text="No data available")
        
        # Sort by value descending
        sorted_items = sorted(stats.items(), key=lambda x: x[1], reverse=True)
        labels = [item[0] for item in sorted_items]
        values = [item[1] for item in sorted_items]
        
        fig = go.Figure(data=[go.Bar(
            x=labels,
            y=values,
            marker=dict(
                color=values,
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(title="Count")
            ),
            text=values,
            textposition='outside',
            hovertemplate='<b>%{x}</b><br>Count: %{y}<extra></extra>'
        )])
        
        fig.update_layout(
            title=title,
            xaxis_title="Option",
            yaxis_title="Count",
            height=400,
            showlegend=False,
        )
        
        return fig
    
    @staticmethod
    def create_percentage_table(stats: Dict[str, int]) -> pd.DataFrame:
        """Create DataFrame with percentages for display."""
        if not stats:
            return pd.DataFrame()
        
        total = sum(stats.values())
        data = {
            'Option': list(stats.keys()),
            'Count': list(stats.values()),
            'Percentage': [f"{(v/total)*100:.1f}%" for v in stats.values()],
        }
        
        df = pd.DataFrame(data)
        return df.sort_values('Count', ascending=False).reset_index(drop=True)


class NumericAnalysisChart:
    """Component for rendering numeric field analysis."""
    
    @staticmethod
    def create_histogram(answers: List[Dict[str, Any]], title: str, bins: int = 10) -> go.Figure:
        """Create histogram for numeric responses."""
        values = []
        for answer in answers:
            try:
                val = float(answer.get('value', 0))
                values.append(val)
            except (ValueError, TypeError):
                continue
        
        if not values:
            return go.Figure().add_annotation(text="No numeric data available")
        
        fig = go.Figure(data=[go.Histogram(
            x=values,
            nbinsx=bins,
            marker=dict(color='rgba(0, 100, 200, 0.7)'),
            hovertemplate='Value: %{x}<br>Count: %{y}<extra></extra>'
        )])
        
        fig.update_layout(
            title=title,
            xaxis_title="Value",
            yaxis_title="Frequency",
            height=400,
        )
        
        return fig
    
    @staticmethod
    def create_box_plot(answers: List[Dict[str, Any]], title: str) -> go.Figure:
        """Create box plot for numeric response distribution."""
        values = []
        for answer in answers:
            try:
                val = float(answer.get('value', 0))
                values.append(val)
            except (ValueError, TypeError):
                continue
        
        if not values:
            return go.Figure().add_annotation(text="No numeric data available")
        
        fig = go.Figure(data=[go.Box(
            y=values,
            name="Responses",
            marker=dict(color='rgba(0, 100, 200, 0.7)'),
            boxmean='sd'
        )])
        
        fig.update_layout(
            title=title,
            yaxis_title="Value",
            height=300,
        )
        
        return fig


class RatingAnalysisChart:
    """Component for rendering rating/Likert scale analysis."""
    
    @staticmethod
    def create_rating_distribution(stats: Dict[str, int], max_rating: int = 5) -> go.Figure:
        """Create stacked visualization for rating distribution."""
        # Ensure all rating levels are present
        all_ratings = {str(i): stats.get(str(i), 0) for i in range(1, max_rating + 1)}
        
        labels = [f"{i} Star{'s' if i != 1 else ''}" for i in range(1, max_rating + 1)]
        values = list(all_ratings.values())
        
        colors = ['#d62728', '#ff7f0e', '#ffdd57', '#90ee90', '#2ca02c']  # Red to Green
        
        fig = go.Figure(data=[go.Bar(
            x=labels,
            y=values,
            marker=dict(color=colors[:len(labels)]),
            text=values,
            textposition='outside',
            hovertemplate='<b>%{x}</b><br>Count: %{y}<extra></extra>'
        )])
        
        fig.update_layout(
            title="Rating Distribution",
            xaxis_title="Rating",
            yaxis_title="Count",
            height=350,
            showlegend=False,
        )
        
        return fig
    
    @staticmethod
    def calculate_average_rating(stats: Dict[str, int]) -> float:
        """Calculate weighted average rating."""
        total_score = sum(int(k) * v for k, v in stats.items() if k.isdigit())
        total_count = sum(stats.values())
        return total_score / total_count if total_count > 0 else 0


# ============================================================================
# MAIN DASHBOARD RENDER FUNCTION
# ============================================================================

def render_analytics_dashboard(forms: List[Dict[str, Any]], 
                               submissions_data: Dict[int, List[Dict[str, Any]]],
                               questions_data: Dict[int, List[Dict[str, Any]]],
                               answers_data: Dict[int, List[Dict[str, Any]]]) -> None:
    """
    Render the complete analytics dashboard with charts and filters.
    
    Args:
        forms: List of form dictionaries
        submissions_data: Dict mapping form_id to submissions list
        questions_data: Dict mapping form_id to questions list
        answers_data: Dict mapping question_id to answers list
    """
    
    st.title("📊 FormMind Analytics Dashboard")
    st.markdown("Comprehensive analytics with charts, filters, and insights")
    
    # Initialize filters
    filter_manager = AnalyticsFilter()
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    selected_form_idx = st.sidebar.selectbox(
        "Select Form",
        range(len(forms)) if forms else [0],
        format_func=lambda i: forms[i].get('title', 'Untitled') if i < len(forms) else "No forms",
        key='form_selector'
    )
    
    if not forms:
        st.info("No forms available. Create a form first to view analytics.")
        return
    
    selected_form = forms[selected_form_idx]
    form_id = selected_form.get('id', selected_form_idx)
    
    # Get form data
    submissions = submissions_data.get(form_id, [])
    questions = questions_data.get(form_id, [])
    
    # Apply filters
    available_questions = questions if isinstance(questions, list) else []
    filters = filter_manager.render_filters(available_questions)
    filtered_submissions = filter_manager.apply_filters(submissions, filters)
    
    # ========== SUMMARY METRICS SECTION ==========
    st.subheader("📈 Summary Metrics")
    
    metrics = summary_metrics(selected_form, filtered_submissions)
    
    metric_cards = [
        MetricCard("Total Submissions", metrics['total_submissions'], icon="📝"),
        MetricCard("Unique Users", metrics['unique_users'], icon="👥"),
        MetricCard("Guest Submissions", metrics['guest_submissions'], icon="🔓"),
        MetricCard("Form Status", "Open" if metrics['is_open'] else "Closed", icon="✅"),
    ]
    
    metrics_row = MetricsRow(metric_cards, cols=4)
    metrics_row.render()
    
    # ========== FORM INFORMATION SECTION ==========
    st.subheader("📋 Form Details")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info(f"**Status:** {selected_form.get('status', 'unknown').upper()}")
    with col2:
        st.info(f"**Access:** {selected_form.get('access_type', 'public').upper()}")
    with col3:
        single_sub = "Yes" if selected_form.get('single_submission') else "No"
        st.info(f"**Single Submission:** {single_sub}")
    
    if not filtered_submissions:
        st.warning("No submissions match the current filters.")
        return
    
    # ========== QUESTION ANALYTICS SECTION ==========
    st.subheader("📊 Question Analytics")
    
    if not questions:
        st.info("No questions in this form.")
        return
    
    # Create tabs for each question
    question_tabs = st.tabs([q.get('label', f"Q{i}") for i, q in enumerate(questions)])
    
    for tab_idx, (tab, question) in enumerate(zip(question_tabs, questions)):
        with tab:
            question_id = question.get('id', tab_idx)
            field_type = question.get('field_type', 'text')
            
            # Get answers for this question
            question_answers = answers_data.get(question_id, [])
            
            if not question_answers:
                st.info("No responses for this question yet.")
                continue
            
            # Render based on field type
            if field_type in ['radio', 'dropdown', 'checkbox']:
                st.markdown(f"**Field Type:** {field_type.upper()}")
                
                stats = choice_stats(question, question_answers)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.plotly_chart(
                        ChoiceDistributionChart.create_pie_chart(
                            stats, 
                            f"Distribution - {question.get('label', 'Question')}"
                        ),
                        use_container_width=True
                    )
                
                with col2:
                    st.plotly_chart(
                        ChoiceDistributionChart.create_bar_chart(
                            stats,
                            "Response Count"
                        ),
                        use_container_width=True
                    )
                
                # Percentage table
                st.markdown("**Response Breakdown**")
                percentage_df = ChoiceDistributionChart.create_percentage_table(stats)
                st.dataframe(percentage_df, use_container_width=True, hide_index=True)
            
            elif field_type in ['integer', 'decimal', 'number']:
                st.markdown(f"**Field Type:** {field_type.upper()}")
                
                numeric_info = numeric_stats(question_answers)
                
                # Numeric statistics
                stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
                with stat_col1:
                    st.metric("Count", numeric_info['count'])
                with stat_col2:
                    st.metric("Min", f"{numeric_info['min']:.2f}" if numeric_info['min'] is not None else "—")
                with stat_col3:
                    st.metric("Max", f"{numeric_info['max']:.2f}" if numeric_info['max'] is not None else "—")
                with stat_col4:
                    st.metric("Average", f"{numeric_info['avg']:.2f}" if numeric_info['avg'] is not None else "—")
                
                # Charts
                col1, col2 = st.columns(2)
                
                with col1:
                    st.plotly_chart(
                        NumericAnalysisChart.create_histogram(
                            question_answers,
                            "Response Distribution"
                        ),
                        use_container_width=True
                    )
                
                with col2:
                    st.plotly_chart(
                        NumericAnalysisChart.create_box_plot(
                            question_answers,
                            "Statistical Summary"
                        ),
                        use_container_width=True
                    )
            
            elif field_type == 'rating':
                st.markdown(f"**Field Type:** RATING")
                
                stats = choice_stats(question, question_answers)
                avg_rating = RatingAnalysisChart.calculate_average_rating(stats)
                
                # Rating metric
                col1, col2 = st.columns([1, 3])
                with col1:
                    st.metric("Average Rating", f"{avg_rating:.1f} ⭐", delta=None)
                with col2:
                    st.plotly_chart(
                        RatingAnalysisChart.create_rating_distribution(stats),
                        use_container_width=True
                    )
            
            elif field_type == 'text':
                st.markdown(f"**Field Type:** TEXT")
                st.write("Recent Responses:")
                
                recent_responses = text_table(question_answers, limit=10)
                
                for idx, response in enumerate(recent_responses, 1):
                    st.write(f"{idx}. {response}")
    
    # ========== RESPONSE TIME ANALYSIS ==========
    st.subheader("⏱️ Response Time Analysis")
    
    completion_times = [
        s.get('completion_time_ms', 0) 
        for s in filtered_submissions 
        if s.get('completion_time_ms')
    ]
    
    if completion_times:
        comp_col1, comp_col2, comp_col3 = st.columns(3)
        with comp_col1:
            st.metric("Avg Completion Time", f"{sum(completion_times)//len(completion_times)}ms")
        with comp_col2:
            st.metric("Min Time", f"{min(completion_times)}ms")
        with comp_col3:
            st.metric("Max Time", f"{max(completion_times)}ms")
    else:
        st.info("No completion time data available.")
    
    # ========== EXPORT OPTIONS ==========
    st.subheader("📥 Export")
    
    if st.button("Download Analytics Report (CSV)"):
        # Create simple CSV export
        export_data = {
            'form_title': selected_form.get('title'),
            'metric': list(metrics.keys()),
            'value': list(metrics.values())
        }
        export_df = pd.DataFrame([export_data])
        csv = export_df.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f"analytics_{form_id}_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )


# ============================================================================
# HELPER FUNCTIONS FOR DATA LOADING (Mock for demo)
# ============================================================================

def get_sample_data() -> Tuple[List[Dict], Dict, Dict, Dict]:
    """Get sample data for dashboard demo."""
    # Sample forms
    forms = [
        {
            'id': 1,
            'title': 'Customer Feedback Survey',
            'status': 'published',
            'access_type': 'public',
            'single_submission': False,
            'submission_start': datetime.now() - timedelta(days=30),
            'submission_end': datetime.now() + timedelta(days=30),
        },
        {
            'id': 2,
            'title': 'Event Registration',
            'status': 'published',
            'access_type': 'public',
            'single_submission': True,
        }
    ]
    
    # Sample questions
    questions_data = {
        1: [
            {'id': 1, 'label': 'How satisfied are you?', 'field_type': 'rating'},
            {'id': 2, 'label': 'What features do you like?', 'field_type': 'checkbox'},
            {'id': 3, 'label': 'Rate the UI clarity', 'field_type': 'integer'},
            {'id': 4, 'label': 'Additional Comments', 'field_type': 'text'},
        ],
        2: [
            {'id': 5, 'label': 'Preferred Time Slot', 'field_type': 'radio'},
            {'id': 6, 'label': 'Number of Attendees', 'field_type': 'integer'},
        ]
    }
    
    # Sample submissions
    submissions_data = {
        1: [
            {'id': i, 'user_id': i % 5, 'guest_token': None, 'submitted_at': datetime.now() - timedelta(hours=j), 'completion_time_ms': 3000}
            for i, j in enumerate(range(1, 26), 1)
        ],
        2: [
            {'id': i, 'user_id': i % 3, 'guest_token': f'guest_{i}', 'submitted_at': datetime.now() - timedelta(days=j), 'completion_time_ms': 5000}
            for i, j in enumerate(range(1, 16), 1)
        ]
    }
    
    # Sample answers
    answers_data = {
        1: [{'value': str(i % 5 + 1)} for i in range(25)],  # Ratings 1-5
        2: [{'value': 'UI, Performance'}, {'value': 'Docs'}, {'value': 'UI, Speed, Docs'}] * 8 + [{'value': 'Performance'}],
        3: [{'value': str(i % 10 + 1)} for i in range(25)],  # Numbers 1-10
        4: [{'value': f'Comment {i}'} for i in range(25)],
        5: [{'value': 'Morning'}, {'value': 'Afternoon'}, {'value': 'Evening'}] * 5,
        6: [{'value': str(i % 20 + 1)} for i in range(15)],
    }
    
    return forms, submissions_data, questions_data, answers_data


# ============================================================================
# PAGE ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    # For demo purposes, load sample data
    forms, submissions_data, questions_data, answers_data = get_sample_data()
    render_analytics_dashboard(forms, submissions_data, questions_data, answers_data)
