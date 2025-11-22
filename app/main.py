"""Streamlit entry for FormMind - Main application with dashboard and analytics.
Run with: `streamlit run app/main.py`

Phase 2 Enhancement: Integrated analytics dashboard with charts and filters.
"""
import streamlit as st
from datetime import datetime, timedelta
from app.auth import login, SEED_USERS
from app.services.analytics import summary_metrics, choice_stats, numeric_stats, text_table
from app.pages.analytics_dashboard import (
    render_analytics_dashboard,
    get_sample_data,
    MetricCard,
    MetricsRow,
    AnalyticsFilter,
)


st.set_page_config(
    page_title="FormMind - Form Analytics Platform",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# CUSTOM STYLING
# ============================================================================

st.markdown("""
<style>
    .main {
        padding-top: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    h1, h2, h3 {
        color: #1f77b4;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# AUTHENTICATION
# ============================================================================

def show_login():
    """Display login interface."""
    st.sidebar.title("🔐 Login")
    col1, col2 = st.sidebar.columns([3, 1])
    
    with col1:
        email = st.selectbox("Sign in as", [u['email'] for u in SEED_USERS])
    
    with col2:
        if st.button("Sign in"):
            user = login(email)
            st.session_state['user'] = user
            st.rerun()
    
    st.info("👤 Demo accounts available. Select an email and sign in.")


# ============================================================================
# DASHBOARD PAGE
# ============================================================================

def show_dashboard(user):
    """Display main forms dashboard."""
    st.title("📋 Forms Dashboard")
    st.markdown(f"**Welcome, {user['name']}** ({user['role']})")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("Manage your forms and track submissions in real-time.")
    with col2:
        if st.button("🔄 Refresh", key="refresh_dashboard"):
            st.rerun()
    
    # Sample forms
    forms = [
        {
            "id": 1,
            "title": "Customer Feedback Survey",
            "status": "published",
            "single_submission": False,
            "submissions": 157,
            "created": "2024-11-01"
        },
        {
            "id": 2,
            "title": "Event Registration",
            "status": "published",
            "single_submission": True,
            "submissions": 45,
            "created": "2024-11-10"
        },
        {
            "id": 3,
            "title": "Product Feedback",
            "status": "draft",
            "single_submission": False,
            "submissions": 0,
            "created": "2024-11-15"
        },
    ]
    
    st.subheader("📑 Your Forms")
    
    # Display forms as cards
    for idx, form in enumerate(forms):
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.write(f"**{form['title']}**")
        with col2:
            status_emoji = "🟢" if form['status'] == "published" else "🔵"
            st.write(f"{status_emoji} {form['status'].upper()}")
        with col3:
            st.write(f"📊 {form['submissions']} submissions")
        with col4:
            if st.button("📈 View Analytics", key=f"btn_{form['id']}"):
                st.session_state['selected_form_id'] = form['id']
                st.session_state['selected_page'] = "Enhanced Analytics"
                st.rerun()
        
        st.divider()


# ============================================================================
# ENHANCED ANALYTICS PAGE (PHASE 2)
# ============================================================================

def show_enhanced_analytics(user):
    """Display Phase 2 enhanced analytics dashboard."""
    
    # Load sample data
    forms, submissions_data, questions_data, answers_data = get_sample_data()
    
    # Render the full analytics dashboard
    render_analytics_dashboard(forms, submissions_data, questions_data, answers_data)
    
    # Export section
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📥 Download PDF Report"):
            st.info("PDF export coming soon!")
    
    with col2:
        if st.button("📧 Share Dashboard"):
            st.info("Email sharing coming soon!")


# ============================================================================
# LEGACY ANALYTICS PAGE (KEPT FOR REFERENCE)
# ============================================================================

def show_legacy_analytics():
    """Display legacy analytics page (for comparison)."""
    st.title("📊 Analytics (Legacy)")
    st.write("FormMind Insights (Beta) - Legacy Interface")
    st.info("This interface has been replaced by the enhanced analytics dashboard. Use the 'Enhanced Analytics' option for the latest features.")
    
    # Sample text responses
    responses = [
        "I love this product, it's great and easy to use.",
        "It was okay, a bit slow but the support was good.",
        "Terrible experience, I hate the workflow.",
        "Good job, I like the UI.",
        "Amazing! Exactly what I needed.",
        "Could be faster, but solid.",
    ]
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("📈 Top Keywords")
        keywords = {
            'great': 2,
            'good': 2,
            'product': 1,
            'fast': 1,
            'solid': 1,
        }
        for word, count in sorted(keywords.items(), key=lambda x: x[1], reverse=True)[:5]:
            st.write(f"• {word}: {count}")
    
    with col2:
        st.subheader("📝 Length Stats")
        lengths = [len(r.split()) for r in responses]
        st.write(f"**Avg Length:** {sum(lengths) // len(lengths)} words")
        st.write(f"**Min:** {min(lengths)} words")
        st.write(f"**Max:** {max(lengths)} words")
    
    with col3:
        st.subheader("😊 Sentiment")
        positive = sum(1 for r in responses if any(w in r.lower() for w in ['great', 'love', 'good', 'amazing']))
        negative = sum(1 for r in responses if any(w in r.lower() for w in ['bad', 'hate', 'terrible']))
        neutral = len(responses) - positive - negative
        
        st.write(f"✅ Positive: {positive}")
        st.write(f"⚠️ Neutral: {neutral}")
        st.write(f"❌ Negative: {negative}")


# ============================================================================
# SIDEBAR NAVIGATION
# ============================================================================

def render_sidebar():
    """Render sidebar with navigation and user info."""
    st.sidebar.title("🎯 FormMind")
    st.sidebar.markdown("---")
    
    if 'user' in st.session_state:
        user = st.session_state['user']
        st.sidebar.write(f"👤 **{user['name']}** ({user['role']})")
        st.sidebar.write(f"📧 {user['email']}")
        
        st.sidebar.markdown("---")
        st.sidebar.subheader("📍 Navigation")
        
        page = st.sidebar.radio(
            "Select Page",
            ["Dashboard", "Enhanced Analytics", "Legacy Analytics", "Settings"],
            key="main_page_selector"
        )
        
        st.sidebar.markdown("---")
        
        # Footer info
        st.sidebar.markdown("""
        **Phase 2 Features:**
        - 📊 Enhanced analytics dashboard
        - 📈 Interactive charts
        - 🔍 Advanced filters
        - ⚡ Performance optimized
        """)
        
        if st.sidebar.button("🚪 Sign Out", key="logout_btn"):
            st.session_state.clear()
            st.rerun()
        
        return page
    
    return None


# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    """Main application entry point."""
    
    # Initialize session state
    if 'user' not in st.session_state:
        show_login()
        st.info("👉 Please sign in from the sidebar to continue.")
        return
    
    # Render sidebar
    page = render_sidebar()
    
    if page is None:
        st.warning("Please sign in again.")
        return
    
    user = st.session_state['user']
    
    # Route to appropriate page
    if page == "Dashboard":
        show_dashboard(user)
    
    elif page == "Enhanced Analytics":
        show_enhanced_analytics(user)
    
    elif page == "Legacy Analytics":
        show_legacy_analytics()
    
    elif page == "Settings":
        st.title("⚙️ Settings")
        st.write("Settings page coming soon!")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### Account Settings")
            st.write("- Change password")
            st.write("- Email preferences")
            st.write("- Two-factor authentication")
        
        with col2:
            st.markdown("### Form Settings")
            st.write("- Default form template")
            st.write("- Submission notifications")
            st.write("- Custom branding")


if __name__ == "__main__":
    main()
