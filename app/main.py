"""Streamlit entry for FormMind (minimal demo UI).
Run with: `streamlit run app/main.py`
"""
import streamlit as st
from app.auth import login, SEED_USERS
from app.services.ai_insights import top_keywords, length_stats, simple_sentiment
from app.services.analytics import summary_metrics


st.set_page_config(page_title="FormMind (demo)")


def show_login():
    st.sidebar.title("Login")
    email = st.sidebar.selectbox("Sign in as", [u['email'] for u in SEED_USERS])
    if st.sidebar.button("Sign in"):
        user = login(email)
        st.session_state['user'] = user
        st.experimental_rerun()


def show_dashboard(user):
    st.title("Forms Dashboard")
    st.write(f"Signed in as {user['name']} ({user['role']})")
    st.write("This is a minimal dashboard for the demo.")
    # Show some sample forms (static for the demo)
    forms = [
        {"id": 1, "title": "Event Registration", "status": "published", "single_submission": True},
        {"id": 2, "title": "Feedback Survey", "status": "draft", "single_submission": False},
    ]
    for f in forms:
        st.card = st.container()
        with st.card:
            st.header(f['title'])
            st.write(f"Status: {f['status']} — single_submission: {f['single_submission']}")


def show_analytics():
    st.title("Analytics (demo)")
    st.write("FormMind Insights (beta)")
    # Sample text responses
    responses = [
        "I love this product, it's great and easy to use.",
        "It was okay, a bit slow but the support was good.",
        "Terrible experience, I hate the workflow.",
        "Good job, I like the UI.",
    ]
    st.subheader("Top keywords")
    for k in top_keywords(responses, top_n=5):
        st.write(f"{k['word']}: {k['count']}")
    st.subheader("Length stats")
    st.write(length_stats(responses))
    st.subheader("Sentiment")
    st.write(simple_sentiment(responses))


def main():
    st.sidebar.title("FormMind (demo)")
    if 'user' not in st.session_state:
        show_login()
        st.info("Please sign in from the sidebar (demo accounts are seeded).")
        return
    user = st.session_state['user']
    page = st.sidebar.radio("Page", ["Dashboard", "Analytics"])
    if page == "Dashboard":
        show_dashboard(user)
    elif page == "Analytics":
        show_analytics()


if __name__ == "__main__":
    main()
