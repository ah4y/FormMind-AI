"""FormMind - Multi-Tenant Form Builder Platform
Run with: `streamlit run app/main.py` (from project root)

A complete Google Forms-like platform with multi-tenant architecture.
"""
import sys
import os
from pathlib import Path

# Add the project root to Python path for proper imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from app.auth import login, SEED_USERS
from app.services.forms import FormsService, QuestionsService
from app.services.submissions import SubmissionsService
from app.services.analytics import AnalyticsService
from app.db import get_db_session
from app.models import Form, FormVersion, Question, QuestionOption

st.set_page_config(
    page_title="FormMind - Multi-Tenant Form Platform",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# GLOBAL STYLING
# ============================================================================
st.markdown("""
<style>
    .form-card {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        background: white;
    }
    .question-card {
        border: 1px solid #ddd;
        border-radius: 6px;
        padding: 1rem;
        margin: 0.5rem 0;
        background: #f9f9f9;
    }
    .metric-box {
        background: #f0f2f6;
        padding: 1rem;
        border-radius: 6px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================
def init_session_state():
    """Initialize session state variables"""
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'dashboard'
    if 'current_form_id' not in st.session_state:
        st.session_state.current_form_id = None
    if 'form_builder_questions' not in st.session_state:
        st.session_state.form_builder_questions = []

# ============================================================================
# AUTHENTICATION
# ============================================================================
def show_login():
    """Display login interface matching requirements"""
    st.title("🔐 FormMind Login")
    st.markdown("### Multi-Tenant Form Platform")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("#### Sign In")
        email = st.selectbox(
            "Select User Account", 
            [f"{u['email']} ({u['role']} - {u['tenant_name']})" for u in SEED_USERS],
            help="Demo accounts for different roles and tenants"
        )
        
        if st.button("🔑 Sign In", type="primary", key="signin_button"):
            # Extract email from the display string
            actual_email = email.split(' (')[0]
            user = login(actual_email)
            st.session_state['user'] = user
            st.session_state['tenant_id'] = user['tenant_id']
            st.rerun()
    
    with col2:
        st.markdown("#### Demo Accounts")
        st.info("""
        **Tenant A (tenant_1)**
        - owner@example.com (Owner)
        - admin@example.com (Admin)
        - editor@example.com (Editor)
        
        **Tenant B (tenant_2)**  
        - owner2@example.com (Owner)
        - admin2@example.com (Admin)
        """)

def show_public_form_access():
    """Handle public form access via token"""
    st.markdown("### 🔗 Access Public Form")
    
    token = st.text_input("Enter Form Token", help="Get this link from the form creator")
    
    if st.button("Access Form", key="access_form_button") and token:
        # This would typically validate the token and load the form
        st.success(f"Loading form with token: {token}")
        st.session_state['public_token'] = token
        st.session_state['current_page'] = 'fill_form'
        st.rerun()

# ============================================================================
# FORM DASHBOARD
# ============================================================================
def show_dashboard(user: Dict[str, Any]):
    """Main forms dashboard showing user's forms"""
    st.title("📋 Forms Dashboard")
    st.markdown(f"**Welcome, {user['name']}** ({user['role']} - {user['tenant_name']})")
    
    # Action buttons
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    with col1:
        if st.button("➕ Create New Form", type="primary", key="create_new_button"):
            st.session_state.current_page = 'create_form'
            st.session_state.form_builder_questions = []
            st.rerun()
    with col2:
        if st.button("📊 Analytics", key="dashboard_analytics_button"):
            st.session_state.current_page = 'analytics'
            st.rerun()
    with col3:
        if st.button("📋 Templates", key="dashboard_templates_button"):
            st.session_state.current_page = 'templates'
            st.rerun()
    with col4:
        st.button("🔄 Refresh", key="refresh_button")
    
    st.divider()
    
    # Forms list based on user role
    forms_service = FormsService()
    
    try:
        if user['role'] in ['OWNER', 'ADMIN']:
            # Can see all forms in their tenant
            forms = forms_service.get_forms_for_user(user['id'], user['role'], user['tenant_id'])
            st.subheader("🗂️ All Forms in Your Organization")
        else:
            # Editor can only see their own forms
            forms = forms_service.get_forms_for_user(user['id'], user['role'], user['tenant_id'])
            st.subheader("📝 Your Forms")
        
        if not forms:
            st.info("No forms found. Create your first form to get started!")
            return
            
        # Display forms
        for form in forms:
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
                
                with col1:
                    st.markdown(f"**{form['title']}**")
                    if form['description']:
                        desc = form['description']
                        st.caption(desc[:100] + "..." if len(desc) > 100 else desc)
                
                with col2:
                    status_color = "🟢" if form['status'] == 'published' else "🔵"
                    st.write(f"{status_color} {form['status'].title()}")
                
                with col3:
                    access_icon = "🌐" if form['access_type'] == 'public' else "🔐"
                    st.write(f"{access_icon} {form['access_type'].title()}")
                
                with col4:
                    # Display submission count from the service result
                    count = form['submission_count']
                    st.write(f"📊 {count}")
                
                with col5:
                    if st.button("✏️", key=f"edit_{form['id']}", help="Edit form"):
                        st.session_state.current_form_id = form['id']
                        st.session_state.current_page = 'edit_form'
                        st.rerun()
                
                # Form actions
                col_actions = st.columns(5)
                with col_actions[0]:
                    if st.button("👁️ View", key=f"view_{form['id']}"):
                        st.session_state.current_form_id = form['id']
                        st.session_state.current_page = 'view_form'
                        st.rerun()
                
                with col_actions[1]:
                    if st.button("📈 Analytics", key=f"analytics_{form['id']}"):
                        st.session_state.current_form_id = form['id']
                        st.session_state.current_page = 'form_analytics'
                        st.rerun()
                
                with col_actions[2]:
                    if st.button("🔗 Share", key=f"share_{form['id']}"):
                        if form['status'] == 'published':
                            token = form['public_token']
                            full_url = f"http://localhost:8501?token={token}"
                            st.success("📋 Public Link (Click to copy)")
                            st.code(full_url, language=None)
                            st.caption("Share this link with anyone to collect responses!")
                        else:
                            st.warning("Publish form first to get a shareable link")
                
                with col_actions[3]:
                    if st.button("📋 Duplicate", key=f"dup_{form['id']}"):
                        new_form_id = forms_service.duplicate_form(
                            form['id'], user['id'], user['role']
                        )
                        if new_form_id:
                            st.success(f"Form duplicated successfully! New form ID: {new_form_id}")
                            st.rerun()
                        else:
                            st.error("Failed to duplicate form.")
                
                with col_actions[4]:
                    if st.button("🗑️ Delete", key=f"del_{form['id']}"):
                        if st.session_state.get(f"confirm_delete_{form['id']}"):
                            if forms_service.delete_form(form['id'], user['id'], user['role']):
                                st.success("Form deleted successfully!")
                                st.rerun()
                            else:
                                st.error("Failed to delete form. You may not have permission.")
                        else:
                            st.session_state[f"confirm_delete_{form['id']}"] = True
                            st.warning("Click again to confirm deletion")
                
                st.divider()
                
    except Exception as e:
        st.error(f"Error loading forms: {str(e)}")

# ============================================================================
# PUBLIC FORM DISPLAY
# ============================================================================
def show_fill_form(token: str):
    """Display a public form for filling out"""
    try:
        # Get form by token
        forms_service = FormsService()
        form = forms_service.get_form_by_token(token)
        
        if not form:
            st.error("❌ Form not found. Please check your link.")
            return
        
        # Display form header
        st.title(f"📝 {form['title']}")
        if form.get('description'):
            st.markdown(form['description'])
        
        st.divider()
        
        # Get questions for the form
        questions = QuestionsService.get_questions_for_form(form['id'])
        
        if not questions:
            st.warning("This form has no questions yet.")
            return
        
        # Create form submission
        with st.form("public_form_submission"):
            answers = {}
            
            for question in questions:
                field_type = question['field_type']
                label = question['label']
                required = question['required']
                
                # Add required asterisk
                display_label = f"{label} *" if required else label
                
                # Render question based on type
                if field_type == 'short_text':
                    answers[question['id']] = st.text_input(
                        display_label,
                        help=question.get('help_text'),
                        placeholder=question.get('placeholder')
                    )
                elif field_type == 'long_text':
                    answers[question['id']] = st.text_area(
                        display_label,
                        help=question.get('help_text'),
                        placeholder=question.get('placeholder')
                    )
                elif field_type == 'multiple_choice':
                    options = question.get('options', [])
                    if options:
                        answers[question['id']] = st.radio(
                            display_label,
                            options,
                            help=question.get('help_text')
                        )
                elif field_type == 'checkboxes':
                    options = question.get('options', [])
                    if options:
                        answers[question['id']] = st.multiselect(
                            display_label,
                            options,
                            help=question.get('help_text')
                        )
                elif field_type == 'dropdown':
                    options = question.get('options', [])
                    if options:
                        answers[question['id']] = st.selectbox(
                            display_label,
                            ["Select an option"] + options,
                            help=question.get('help_text')
                        )
                elif field_type == 'number':
                    answers[question['id']] = st.number_input(
                        display_label,
                        help=question.get('help_text')
                    )
                elif field_type == 'email':
                    answers[question['id']] = st.text_input(
                        display_label,
                        help=question.get('help_text'),
                        placeholder="email@example.com"
                    )
                elif field_type == 'date':
                    answers[question['id']] = st.date_input(
                        display_label,
                        help=question.get('help_text')
                    )
                elif field_type == 'time':
                    answers[question['id']] = st.time_input(
                        display_label,
                        help=question.get('help_text')
                    )
                elif field_type == 'rating':
                    answers[question['id']] = st.slider(
                        display_label,
                        1, 5, 3,
                        help=question.get('help_text')
                    )
            
            # Submit button
            submitted = st.form_submit_button("📤 Submit Form", type="primary")
            
            if submitted:
                # Validate required fields
                missing_required = []
                for question in questions:
                    if question['required']:
                        answer = answers.get(question['id'])
                        if not answer or (isinstance(answer, str) and answer.strip() == ""):
                            missing_required.append(question['label'])
                
                if missing_required:
                    st.error(f"Please fill in the required fields: {', '.join(missing_required)}")
                else:
                    # Save submission
                    submissions_service = SubmissionsService()
                    submission_id = submissions_service.create_submission(
                        form_id=form['id'],
                        answers=answers
                    )
                    
                    if submission_id:
                        st.success("✅ Thank you! Your response has been submitted.")
                    else:
                        st.error("❌ Failed to submit response. Please try again.")
        
        # Back to home button
        if st.button("🏠 Back to Home", key="back_home_button"):
            if 'public_token' in st.session_state:
                del st.session_state['public_token']
            st.session_state['current_page'] = 'dashboard'
            st.rerun()
            
    except Exception as e:
        st.error(f"❌ Error loading form: {str(e)}")

# ============================================================================
# MAIN APPLICATION ROUTING
# ============================================================================
def main():
    """Main application router"""
    init_session_state()
    
    # Check for public form access via URL parameters
    query_params = st.query_params
    if 'token' in query_params:
        token = query_params['token']
        st.session_state['public_token'] = token
        st.session_state['current_page'] = 'fill_form'
    
    # Show public form if accessed via token
    if st.session_state.get('current_page') == 'fill_form' and st.session_state.get('public_token'):
        show_fill_form(st.session_state['public_token'])
        return
    
    # Authentication check
    if 'user' not in st.session_state:
        # Show login or public form access
        tab1, tab2 = st.tabs(["🔑 User Login", "🔗 Public Form"])
        
        with tab1:
            show_login()
        
        with tab2:
            show_public_form_access()
        
        return
    
    user = st.session_state['user']
    
    # Sidebar navigation
    with st.sidebar:
        st.title("🎯 FormMind")
        st.markdown(f"👤 **{user['name']}**")
        st.caption(f"{user['role']} - {user['tenant_name']}")
        
        st.divider()
        
        # Navigation menu
        if st.button("🏠 Dashboard", key="sidebar_dashboard"):
            st.session_state.current_page = 'dashboard'
            st.rerun()
        
        if st.button("📊 Analytics"):
            st.session_state.current_page = 'analytics'
            st.rerun()
        
        if st.button("📋 Templates"):
            st.session_state.current_page = 'templates'
            st.rerun()
        
        st.divider()
        
        # User info
        st.markdown("### Account Info")
        st.write(f"**Email:** {user['email']}")
        st.write(f"**Role:** {user['role']}")
        st.write(f"**Tenant:** {user['tenant_name']}")
        
        if st.button("🚪 Sign Out", key="signout_button"):
            st.session_state.clear()
            st.rerun()
    
    # Route to appropriate page
    page = st.session_state.current_page
    
    if page == 'dashboard':
        show_dashboard(user)
    elif page == 'create_form':
        show_form_builder(user, form_id=None)
    elif page == 'edit_form':
        show_form_builder(user, form_id=st.session_state.current_form_id)
    elif page == 'view_form':
        show_form_viewer(user)
    elif page == 'fill_form':
        show_fill_form(st.session_state.get('public_token'))
    elif page == 'form_analytics':
        show_form_analytics(user)
    elif page == 'analytics':
        show_global_analytics(user)
    elif page == 'templates':
        show_templates(user)
    else:
        show_dashboard(user)

# ============================================================================
# FORM BUILDER
# ============================================================================
def show_form_builder(user: Dict[str, Any], form_id: Optional[int] = None):
    """Complete form builder interface matching Google Forms"""
    is_editing = form_id is not None
    
    st.title("🛠️ Form Builder" + (" - Edit Form" if is_editing else " - Create New Form"))
    
    # Back button
    if st.button("← Back to Dashboard"):
        st.session_state.current_page = 'dashboard'
        st.rerun()
    
    # Initialize forms service
    forms_service = FormsService()
    
    # Load existing form data if editing
    existing_form_data = None
    existing_questions = []
    
    if is_editing and form_id:
        try:
            # Get form data
            with get_db_session() as session:
                form = session.query(Form).filter(Form.id == form_id).first()
                if form:
                    existing_form_data = {
                        'title': form.title,
                        'description': form.description or '',
                        'status': form.status,
                        'public_token': form.public_token
                    }
                    
                    # Get questions for this form
                    form_version = session.query(FormVersion).filter(
                        FormVersion.form_id == form_id,
                        FormVersion.is_active == True
                    ).first()
                    
                    if form_version:
                        questions_data = session.query(Question).filter(
                            Question.form_version_id == form_version.id
                        ).order_by(Question.order_index).all()
                        
                        for q in questions_data:
                            # Get options if any
                            options_data = session.query(QuestionOption).filter(
                                QuestionOption.question_id == q.id
                            ).order_by(QuestionOption.order_index).all()
                            
                            options = [opt.value for opt in options_data] if options_data else []
                            
                            existing_questions.append({
                                'id': q.id,
                                'type': q.field_type,
                                'label': q.label,
                                'placeholder': q.placeholder or '',
                                'help_text': q.help_text or '',
                                'required': q.required,
                                'options': options
                            })
                    
                    # Store in session for editing
                    st.session_state['form_id'] = form_id
                    
        except Exception as e:
            st.error(f"Error loading form: {e}")
    
    st.divider()
    
    # Form settings section
    st.subheader("📋 Form Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        form_title = st.text_input(
            "Form Title*", 
            value=existing_form_data['title'] if existing_form_data else '',
            placeholder="e.g., Customer Feedback Survey"
        )
        form_description = st.text_area(
            "Description", 
            value=existing_form_data['description'] if existing_form_data else '',
            placeholder="Tell people what this form is for..."
        )
        
    with col2:
        # Access settings
        st.markdown("**Access Settings**")
        is_public = st.radio("Who can fill this form?", 
                           ["🌐 Anyone with the link (Public)", "🔐 Only authenticated users"], 
                           index=0)
        is_public = is_public.startswith("🌐")
        
        # Submission settings
        st.markdown("**Submission Settings**")
        single_submission = st.checkbox("Limit to one response per user")
        
        # Time window
        col_start, col_end = st.columns(2)
        with col_start:
            start_date = st.date_input("Start Date (optional)")
        with col_end:
            end_date = st.date_input("End Date (optional)")
    
    st.divider()
    
    # Questions section
    st.subheader("❓ Questions")
    
    # Initialize questions in session state
    if 'form_builder_questions' not in st.session_state:
        if is_editing and existing_questions:
            st.session_state.form_builder_questions = existing_questions
        else:
            st.session_state.form_builder_questions = []
    
    questions = st.session_state.form_builder_questions
    
    # Add question button
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        if st.button("➕ Add Question", type="primary", key="add_question_button"):
            new_question = {
                "id": len(questions) + 1,
                "type": "short_text",
                "label": "",
                "placeholder": "",
                "help_text": "",
                "required": False,
                "options": [],  # for radio, checkbox, dropdown
                "validation": {}
            }
            questions.append(new_question)
            st.rerun()
    
    with col2:
        if st.button("📋 Add from Template", key="add_template_button"):
            # Show template selection popup
            st.session_state.show_template_popup = not st.session_state.get('show_template_popup', False)
    
    # Template selection popup
    if st.session_state.get('show_template_popup', False):
        st.markdown("### 📋 Choose Template Questions")
        
        template_options = {
            'survey': 'Customer Satisfaction Survey',
            'feedback': 'Employee Feedback Survey', 
            'research': 'Market Research Survey',
            'product': 'Product Feedback Form',
            'service': 'Service Review Form',
            'event': 'Event Registration Form',
            'education': 'Course Enrollment Form',
            'contact': 'Business Contact Form'
        }
        
        selected_template = st.selectbox(
            "Select a template:",
            options=list(template_options.keys()),
            format_func=lambda x: template_options[x],
            key="template_selector"
        )
        
        col_preview, col_add = st.columns([3, 1])
        
        with col_preview:
            if selected_template:
                st.write("**Template Questions:**")
                template_questions = get_template_questions(selected_template)
                for i, q in enumerate(template_questions):
                    st.write(f"{i+1}. {q['label']} ({q['field_type']})")
                    if q.get('options'):
                        st.write(f"   Options: {', '.join(q['options'][:3])}{'...' if len(q['options']) > 3 else ''}")
        
        with col_add:
            if st.button("✅ Add Questions", type="primary", key="add_questions_modal_button"):
                if selected_template:
                    template_questions = get_template_questions(selected_template)
                    current_questions = st.session_state.form_builder_questions
                    
                    # Add template questions to current form
                    for template_q in template_questions:
                        new_question = {
                            "id": str(uuid.uuid4()),
                            "label": template_q['label'],
                            "type": template_q['field_type'], 
                            "required": template_q.get('required', False),
                            "placeholder": template_q.get('placeholder', ''),
                            "help_text": template_q.get('help_text', ''),
                            "options": template_q.get('options', []),
                            "validation": {}
                        }
                        current_questions.append(new_question)
                    
                    st.session_state.form_builder_questions = current_questions
                    st.session_state.show_template_popup = False
                    st.success(f"Added {len(template_questions)} questions from {template_options[selected_template]}!")
                    st.rerun()
            
            if st.button("❌ Cancel", key="cancel_modal_button"):
                st.session_state.show_template_popup = False
                st.rerun()
    
    with col3:
        if len(questions) > 0:
            if st.button("🗑️ Clear All", key="clear_all_button"):
                if st.session_state.get('confirm_clear_all'):
                    st.session_state.form_builder_questions = []
                    st.session_state.confirm_clear_all = False
                    st.rerun()
                else:
                    st.session_state.confirm_clear_all = True
                    st.warning("Click again to confirm")
    
    # Display questions
    if questions:
        st.markdown("---")
        
        for i, question in enumerate(questions):
            with st.container():
                st.markdown(f"### Question {i + 1}")
                
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    # Question type
                    question_types = [
                        ("short_text", "📝 Short Text"),
                        ("long_text", "📄 Long Text"),
                        ("radio", "🔘 Multiple Choice"),
                        ("checkbox", "☑️ Checkboxes"),
                        ("dropdown", "📋 Dropdown"),
                        ("integer", "🔢 Number"),
                        ("decimal", "🔢 Decimal"),
                        ("date", "📅 Date"),
                        ("time", "🕐 Time"),
                        ("boolean", "✅ Yes/No")
                    ]
                    
                    current_type_label = next((label for value, label in question_types if value == question['type']), "📝 Short Text")
                    
                    new_type = st.selectbox(
                        "Question Type",
                        options=[value for value, label in question_types],
                        format_func=lambda x: next(label for value, label in question_types if value == x),
                        index=[value for value, label in question_types].index(question['type']),
                        key=f"type_{i}"
                    )
                    question['type'] = new_type
                
                with col2:
                    # Question actions
                    col_up, col_down, col_del = st.columns(3)
                    with col_up:
                        if i > 0 and st.button("⬆️", key=f"up_{i}", help="Move up"):
                            questions[i], questions[i-1] = questions[i-1], questions[i]
                            st.rerun()
                    
                    with col_down:
                        if i < len(questions) - 1 and st.button("⬇️", key=f"down_{i}", help="Move down"):
                            questions[i], questions[i+1] = questions[i+1], questions[i]
                            st.rerun()
                    
                    with col_del:
                        if st.button("🗑️", key=f"del_{i}", help="Delete question"):
                            questions.pop(i)
                            st.rerun()
                
                # Question details
                col_left, col_right = st.columns(2)
                
                with col_left:
                    question['label'] = st.text_input(
                        "Question Label*",
                        value=question['label'],
                        placeholder="e.g., What is your name?",
                        key=f"label_{i}"
                    )
                    
                    question['placeholder'] = st.text_input(
                        "Placeholder Text",
                        value=question['placeholder'],
                        placeholder="e.g., Enter your full name",
                        key=f"placeholder_{i}"
                    )
                
                with col_right:
                    question['help_text'] = st.text_area(
                        "Help Text",
                        value=question['help_text'],
                        placeholder="Additional instructions for users",
                        key=f"help_{i}",
                        height=100
                    )
                    
                    question['required'] = st.checkbox(
                        "Required",
                        value=question['required'],
                        key=f"required_{i}"
                    )
                
                # Type-specific settings
                if question['type'] in ['radio', 'checkbox', 'dropdown']:
                    st.markdown("**Options**")
                    
                    # Display existing options
                    if 'options' not in question:
                        question['options'] = []
                    
                    for j, option in enumerate(question['options']):
                        col_opt, col_del_opt = st.columns([4, 1])
                        with col_opt:
                            question['options'][j] = st.text_input(
                                f"Option {j + 1}",
                                value=option,
                                key=f"option_{i}_{j}"
                            )
                        with col_del_opt:
                            if st.button("❌", key=f"del_opt_{i}_{j}"):
                                question['options'].pop(j)
                                st.rerun()
                    
                    # Add new option
                    if st.button(f"➕ Add Option", key=f"add_opt_{i}"):
                        question['options'].append(f"Option {len(question['options']) + 1}")
                        st.rerun()
                
                elif question['type'] in ['integer', 'decimal']:
                    col_min, col_max = st.columns(2)
                    with col_min:
                        min_val = st.number_input(
                            "Minimum Value",
                            value=question.get('validation', {}).get('min_value'),
                            key=f"min_{i}"
                        )
                        if 'validation' not in question:
                            question['validation'] = {}
                        question['validation']['min_value'] = min_val
                    
                    with col_max:
                        max_val = st.number_input(
                            "Maximum Value", 
                            value=question.get('validation', {}).get('max_value'),
                            key=f"max_{i}"
                        )
                        question['validation']['max_value'] = max_val
                
                st.markdown("---")
    else:
        st.info("👆 Click 'Add Question' to start building your form")
    
    # Preview section
    if questions:
        st.subheader("👁️ Form Preview")
        
        with st.container():
            st.markdown("### " + (form_title if form_title else "Untitled Form"))
            if form_description:
                st.markdown(form_description)
            
            st.markdown("---")
            
            # Preview each question
            for i, question in enumerate(questions):
                label = question['label'] if question['label'] else f"Question {i + 1}"
                required_mark = " *" if question['required'] else ""
                
                st.markdown(f"**{i + 1}. {label}{required_mark}**")
                
                if question['help_text']:
                    st.caption(question['help_text'])
                
                # Render question based on type
                if question['type'] == 'short_text':
                    st.text_input(f"Question {i+1}: {question['label']}", placeholder=question['placeholder'], key=f"preview_{i}", disabled=True, label_visibility="hidden")
                
                elif question['type'] == 'long_text':
                    st.text_area(f"Question {i+1}: {question['label']}", placeholder=question['placeholder'], key=f"preview_{i}", disabled=True, label_visibility="hidden")
                
                elif question['type'] == 'radio':
                    if question['options']:
                        st.radio("Select option", question['options'], key=f"preview_{i}", disabled=True, label_visibility="hidden")
                    else:
                        st.info("Add options to see preview")
                
                elif question['type'] == 'checkbox':
                    if question['options']:
                        for opt in question['options']:
                            st.checkbox(opt, key=f"preview_{i}_{opt}", disabled=True)
                    else:
                        st.info("Add options to see preview")
                
                elif question['type'] == 'dropdown':
                    if question['options']:
                        st.selectbox("Select option", ["Select an option"] + question['options'], key=f"preview_{i}", disabled=True, label_visibility="hidden")
                    else:
                        st.info("Add options to see preview")
                
                elif question['type'] == 'integer':
                    min_val = question.get('validation', {}).get('min_value', 0)
                    max_val = question.get('validation', {}).get('max_value', 100)
                    st.number_input("Enter number", min_value=min_val, max_value=max_val, key=f"preview_{i}", disabled=True, label_visibility="hidden")
                
                elif question['type'] == 'decimal':
                    min_val = question.get('validation', {}).get('min_value', 0.0)
                    max_val = question.get('validation', {}).get('max_value', 100.0)
                    st.number_input("Enter decimal", min_value=min_val, max_value=max_val, step=0.1, key=f"preview_{i}", disabled=True, label_visibility="hidden")
                
                elif question['type'] == 'date':
                    st.date_input("Select date", key=f"preview_{i}", disabled=True, label_visibility="hidden")
                
                elif question['type'] == 'time':
                    st.time_input("Select time", key=f"preview_{i}", disabled=True, label_visibility="hidden")
                
                elif question['type'] == 'boolean':
                    st.checkbox("Yes", key=f"preview_{i}", disabled=True)
                
                st.markdown("")
    
    # Save form section
    st.divider()
    st.subheader("💾 Save Form")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("💾 Save as Draft", type="secondary", use_container_width=True, key="save_draft_button"):
            if form_title and questions:
                try:
                    # Create form in database
                    form_data = forms_service.create_form(
                        title=form_title,
                        description=form_description or "",
                        created_by=user['id'],
                        tenant_id=user['tenant_id'],
                        access_type='public' if is_public else 'authenticated',
                        single_submission=single_submission
                    )
                    
                    if form_data:
                        # Save all questions to the form
                        questions_saved = 0
                        for question in questions:
                            question_id = QuestionsService.add_question(
                                form_id=form_data['id'],
                                user_id=user['id'],
                                user_role=user.get('role', 'user').upper(),
                                question_data=question
                            )
                            if question_id:
                                questions_saved += 1
                        
                        st.success(f"✅ Form saved as draft with {questions_saved} questions!")
                        # Clear the form builder
                        st.session_state.form_builder_questions = []
                        st.session_state.current_page = 'dashboard'
                        st.rerun()
                    else:
                        st.error("❌ Failed to save form")
                        
                except Exception as e:
                    st.error(f"❌ Error saving form: {str(e)}")
            else:
                st.error("Please add a title and at least one question")
    
    with col2:
        if st.button("🚀 Publish Form", type="primary", use_container_width=True, key="publish_button"):
            if form_title and questions:
                try:
                    # Create and publish form in database
                    form_data = forms_service.create_form(
                        title=form_title,
                        description=form_description or "",
                        created_by=user['id'],
                        tenant_id=user['tenant_id'],
                        access_type='public' if is_public else 'authenticated',
                        single_submission=single_submission
                    )
                    
                    if form_data:
                        # Save all questions to the form
                        questions_saved = 0
                        for question in questions:
                            question_id = QuestionsService.add_question(
                                form_id=form_data['id'],
                                user_id=user['id'],
                                user_role=user.get('role', 'user').upper(),
                                question_data=question
                            )
                            if question_id:
                                questions_saved += 1
                        
                        # Get the public token from the created form
                        public_token = form_data.get('public_token', 'unknown')
                        full_url = f"http://localhost:8505?token={public_token}"
                        
                        # Publish the form by updating status
                        published = forms_service.update_form_settings(
                            form_id=form_data['id'],
                            user_id=user['id'], 
                            user_role=user.get('role', 'user').upper(),
                            settings={'status': 'published'}
                        )
                        
                        st.success(f"🎉 Form published successfully with {questions_saved} questions!")
                        st.success("📋 **Your Public Form Link** (Click to copy):")
                        st.code(full_url, language=None)
                        st.caption("🔗 Share this link with anyone to collect responses!")
                        
                        # Clear the form builder
                        st.session_state.form_builder_questions = []
                        st.session_state.current_page = 'dashboard'
                        st.rerun()
                    else:
                        st.error("❌ Failed to publish form")
                        
                except Exception as e:
                    st.error(f"❌ Error publishing form: {str(e)}")
            else:
                st.error("Please add a title and at least one question")
    
    with col3:
        if st.button("📋 Save as Template", use_container_width=True, key="save_template_button"):
            if form_title and questions:
                # Template details input
                with st.form("template_form"):
                    template_name = st.text_input("Template Name:", value=form_title)
                    template_category = st.selectbox("Category:", 
                        ["Survey", "Registration", "Feedback", "Contact", "Other"])
                    template_visibility = st.selectbox("Visibility:", 
                        ["private", "tenant", "public"])
                    
                    if st.form_submit_button("Save as Template"):
                        if st.session_state.get('form_id'):
                            from app.services.forms import TemplateService
                            template_service = TemplateService()
                            
                            template_id = template_service.save_form_as_template(
                                st.session_state['form_id'],
                                template_name,
                                template_category,
                                template_visibility,
                                user['id'],
                                user['tenant_id']
                            )
                            
                            if template_id:
                                st.success(f"Template saved successfully! Template ID: {template_id}")
                            else:
                                st.error("Failed to save template")
                        else:
                            st.error("Please save the form first before creating a template")
            else:
                st.error("Please add a title and at least one question")

def show_form_viewer(user: Dict[str, Any]):
    """View form details and settings"""
    st.title("👁️ Form Details")
    
    if st.button("← Back to Dashboard"):
        st.session_state.current_page = 'dashboard'
        st.rerun()
    
    form_id = st.session_state.current_form_id
    st.info(f"Viewing details for Form ID: {form_id}")
    
    # Here you would fetch form details from database
    # For now, showing placeholder
    st.subheader("📋 Form Information")
    
    col1, col2 = st.columns(2)
    with col1:
        st.write("**Title:** Customer Feedback Survey")
        st.write("**Status:** Published")
        st.write("**Created:** 2024-11-01")
        st.write("**Total Submissions:** 25")
    
    with col2:
        st.write("**Access:** Public")
        st.write("**Single Submission:** Yes")
        st.write("**Start Date:** None")
        st.write("**End Date:** None")

def show_form_filler(user: Optional[Dict[str, Any]]):
    """Fill out a form (public or authenticated)"""
    st.title("📝 Fill Form")
    
    # Check if user is accessing via public token
    if 'public_token' in st.session_state:
        st.info(f"Filling form via public link: {st.session_state['public_token']}")
    
    # Sample form for demonstration
    st.markdown("### Customer Feedback Survey")
    st.markdown("We'd love to hear your thoughts about our service.")
    st.divider()
    
    # Sample questions
    name = st.text_input("1. What is your name? *", placeholder="Enter your full name")
    email = st.text_input("2. Email address *", placeholder="your.email@example.com")
    rating = st.radio("3. How would you rate our service? *", 
                     ["⭐ Poor", "⭐⭐ Fair", "⭐⭐⭐ Good", "⭐⭐⭐⭐ Very Good", "⭐⭐⭐⭐⭐ Excellent"])
    
    features = st.multiselect("4. Which features do you use most?", 
                             ["Dashboard", "Analytics", "Form Builder", "Templates", "Sharing"])
    
    feedback = st.text_area("5. Additional feedback", placeholder="Tell us what you think...")
    
    newsletter = st.checkbox("6. Subscribe to our newsletter")
    
    st.divider()
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📤 Submit Response", type="primary"):
            if name and email and rating:
                st.success("✅ Thank you! Your response has been submitted.")
            else:
                st.error("Please fill in all required fields (marked with *)")
    
    with col2:
        if st.button("🔄 Clear Form"):
            st.rerun()

def show_form_analytics(user: Dict[str, Any]):
    """Analytics for specific form using real database data"""
    st.title("📈 Form Analytics")
    
    if st.button("← Back to Dashboard"):
        st.session_state.current_page = 'dashboard'
        st.rerun()
    
    form_id = st.session_state.current_form_id
    
    # Get real form analytics using AnalyticsService
    analytics_service = AnalyticsService()
    
    try:
        # Get form summary stats
        summary_stats = analytics_service.get_form_summary_stats(form_id, user['id'], user['role'])
        
        if not summary_stats:
            st.error("Unable to load form analytics. Form not found or access denied.")
            return
        
        st.markdown(f"### Analytics for Form: {summary_stats['form_title']}")
        
        # Summary metrics using real data
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Responses", summary_stats['total_submissions'])
        
        with col2:
            st.metric("Completion Rate", f"{summary_stats['completion_rate']:.1f}%")
        
        with col3:
            avg_time = summary_stats['avg_completion_time']
            if avg_time:
                st.metric("Avg. Time", f"{avg_time}m")
            else:
                st.metric("Avg. Time", "N/A")
        
        with col4:
            # Calculate time since last submission
            if summary_stats['total_submissions'] > 0:
                # This would need to be calculated from actual submission timestamps
                st.metric("Last Response", "Recent")
            else:
                st.metric("Last Response", "None")
        
        st.divider()
        
        # Question-specific analytics
        question_analytics = analytics_service.get_question_analytics(form_id, user['id'], user['role'])
        
        if question_analytics:
            st.subheader("📊 Question Analytics")
            
            for qa in question_analytics:
                with st.expander(f"Question: {qa['question_label']}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.metric("Total Responses", qa['total_responses'])
                        st.metric("Response Rate", f"{qa['response_rate']:.1f}%")
                    
                    with col2:
                        # Show type-specific analytics
                        if qa['question_type'] in ['radio', 'dropdown']:
                            if 'choice_distribution' in qa:
                                st.write("**Choice Distribution:**")
                                for choice in qa['choice_distribution']:
                                    st.write(f"- {choice['label']}: {choice['count']} ({choice['percentage']:.1f}%)")
                        
                        elif qa['question_type'] == 'number':
                            if 'average' in qa and qa['average']:
                                st.write(f"**Average:** {qa['average']}")
                                st.write(f"**Range:** {qa['min_value']} - {qa['max_value']}")
                        
                        elif qa['question_type'] in ['short_text', 'long_text']:
                            if 'avg_length' in qa:
                                st.write(f"**Average Length:** {qa['avg_length']} characters")
        else:
            st.info("No question analytics available yet. Add questions to your form to see detailed analytics.")
        
        # Export section
        st.divider()
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📥 Export to CSV"):
                csv_data = analytics_service.export_form_responses(form_id, user['id'], user['role'], 'csv')
                if csv_data:
                    st.download_button("Download CSV", csv_data, f"form_{form_id}_responses.csv", "text/csv")
                    st.success("CSV export ready!")
                else:
                    st.info("No data to export")
        
        with col2:
            if st.button("📊 Export to JSON"):
                json_data = analytics_service.export_form_responses(form_id, user['id'], user['role'], 'json')
                if json_data:
                    st.download_button("Download JSON", json_data, f"form_{form_id}_responses.json", "application/json")
                    st.success("JSON export ready!")
                else:
                    st.info("No data to export")
    
    except Exception as e:
        st.error(f"Error loading analytics: {str(e)}")
        st.info("Please check that the form exists and you have permission to view it.")

def show_global_analytics(user: Dict[str, Any]):
    """Global analytics dashboard using real database data"""
    st.title("📊 Analytics Dashboard")
    
    if st.button("← Back to Dashboard"):
        st.session_state.current_page = 'dashboard'
        st.rerun()
    
    # Get real dashboard statistics
    analytics_service = AnalyticsService()
    
    try:
        dashboard_stats = analytics_service.get_tenant_dashboard_stats(
            user['tenant_id'], user['id'], user['role']
        )
        
        # Global metrics using real data
        st.subheader("🌟 Overview")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Forms", dashboard_stats['total_forms'])
        
        with col2:
            st.metric("Total Responses", dashboard_stats['total_submissions'])
        
        with col3:
            st.metric("Active Forms", dashboard_stats['active_forms'])
        
        with col4:
            # Calculate conversion rate as percentage of published forms
            if dashboard_stats['total_forms'] > 0:
                conversion_rate = (dashboard_stats['active_forms'] / dashboard_stats['total_forms']) * 100
                st.metric("Published Rate", f"{conversion_rate:.1f}%")
            else:
                st.metric("Published Rate", "0%")
        
        st.divider()
        
        # Form status breakdown
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📈 Forms by Status")
            status_data = dashboard_stats.get('forms_by_status', {})
            
            if any(status_data.values()):
                # Show simple metrics instead of charts for now
                st.write(f"**Draft Forms:** {status_data.get('draft', 0)}")
                st.write(f"**Published Forms:** {status_data.get('published', 0)}")
                st.write(f"**Closed Forms:** {status_data.get('closed', 0)}")
            else:
                st.info("No forms created yet")
        
        with col2:
            st.subheader("📅 Recent Activity")
            
            recent_activity = dashboard_stats.get('recent_activity', [])
            
            if recent_activity:
                for activity in recent_activity[:5]:  # Show last 5
                    st.write(f"**{activity['form_title']}**")
                    st.caption(f"Submitted by {activity['submitter']} at {activity['submitted_at'].strftime('%Y-%m-%d %H:%M')}")
                    st.divider()
            else:
                st.info("No recent submissions")
    
    except Exception as e:
        st.error(f"Error loading dashboard analytics: {str(e)}")
        # Fallback to minimal display
        st.subheader("🌟 Overview")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Forms", "0")
        with col2:
            st.metric("Total Responses", "0")
        with col3:
            st.metric("Active Forms", "0")
        with col4:
            st.metric("Published Rate", "0%")

def show_templates(user: Dict[str, Any]):
    """Template management with real database integration"""
    st.title("📋 Form Templates")
    
    if st.button("← Back to Dashboard"):
        st.session_state.current_page = 'dashboard'
        st.rerun()
    
    st.markdown("Create forms faster with pre-built templates")
    
    # Get templates from database
    try:
        from app.services.forms import TemplateService
        template_service = TemplateService()
        templates = template_service.get_templates(user['tenant_id'], user['id'])
        
        # Show user's templates
        if templates:
            st.subheader("🎨 Your Templates")
            
            for template in templates[:5]:  # Show first 5
                with st.container():
                    col1, col2, col3 = st.columns([3, 1, 1])
                    
                    with col1:
                        st.markdown(f"**{template['name']}**")
                        st.caption(f"Category: {template.get('category', 'General')} | "
                                 f"Created: {template.get('created_at', 'Unknown')}")
                    
                    with col2:
                        if st.button("Use", key=f"use_template_{template['id']}"):
                            st.success(f"Template '{template['name']}' loaded!")
                            # TODO: Implement template loading into form builder
                    
                    with col3:
                        if st.button("Delete", key=f"del_template_{template['id']}"):
                            # TODO: Implement template deletion
                            st.info("Template deletion coming soon!")
                    
                    st.divider()
        
    except Exception as e:
        st.error(f"Error loading templates: {e}")
    
    # Template categories with predefined templates
    st.subheader("📚 Template Library")
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Survey", "📝 Feedback", "🎫 Registration", "💼 Business"])
    
    with tab1:
        st.subheader("Survey Templates")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            with st.container():
                st.markdown("#### 📝 Customer Satisfaction")
                st.write("Standard customer satisfaction survey with rating questions")
                st.caption("• Overall satisfaction rating\\n• Service quality rating\\n• Recommendation question")
                if st.button("Create from Template", key="survey_1"):
                    # Create basic customer satisfaction form
                    if create_template_form(user, "Customer Satisfaction Survey", "survey"):
                        st.success("Customer satisfaction form created!")
                        st.session_state.current_page = 'form_builder'
                        st.rerun()
        
        with col2:
            with st.container():
                st.markdown("#### 👥 Employee Feedback") 
                st.write("Collect feedback from your team members")
                st.caption("• Work satisfaction\\n• Management feedback\\n• Improvement suggestions")
                if st.button("Create from Template", key="survey_2"):
                    if create_template_form(user, "Employee Feedback Survey", "feedback"):
                        st.success("Employee feedback form created!")
                        st.session_state.current_page = 'form_builder'
                        st.rerun()
        
        with col3:
            with st.container():
                st.markdown("#### 📈 Market Research")
                st.write("Gather market insights and customer preferences")
                st.caption("• Demographics\\n• Product preferences\\n• Market trends")
                if st.button("Create from Template", key="survey_3"):
                    if create_template_form(user, "Market Research Survey", "research"):
                        st.success("Market research form created!")
                        st.session_state.current_page = 'form_builder'
                        st.rerun()
    
    with tab2:
        col1, col2 = st.columns(2)
        with col1:
            with st.container():
                st.markdown("#### 💬 Product Feedback")
                st.write("Collect detailed product feedback from users")
                st.caption("• Product rating\\n• Feature requests\\n• Bug reports")
                if st.button("Create from Template", key="feedback_1"):
                    if create_template_form(user, "Product Feedback Form", "product"):
                        st.success("Product feedback form created!")
                        st.session_state.current_page = 'form_builder'
                        st.rerun()
        
        with col2:
            with st.container():
                st.markdown("#### 🌟 Service Review")
                st.write("Service quality assessment form")
                st.caption("• Service rating\\n• Staff feedback\\n• Improvement areas")
                if st.button("Create from Template", key="feedback_2"):
                    if create_template_form(user, "Service Review Form", "service"):
                        st.success("Service review form created!")
                        st.session_state.current_page = 'form_builder'
                        st.rerun()
    
    with tab3:
        col1, col2 = st.columns(2)
        with col1:
            with st.container():
                st.markdown("#### 🎫 Event Registration")
                st.write("Standard event registration form")
                st.caption("• Personal details\\n• Contact information\\n• Preferences")
                if st.button("Create from Template", key="reg_1"):
                    if create_template_form(user, "Event Registration Form", "event"):
                        st.success("Event registration form created!")
                        st.session_state.current_page = 'form_builder'
                        st.rerun()
        
        with col2:
            with st.container():
                st.markdown("#### 📚 Course Enrollment")
                st.write("Educational course registration")
                st.caption("• Student information\\n• Course selection\\n• Prerequisites")
                if st.button("Create from Template", key="reg_2"):
                    if create_template_form(user, "Course Enrollment Form", "education"):
                        st.success("Course enrollment form created!")
                        st.session_state.current_page = 'form_builder'
                        st.rerun()
    
    with tab4:
        col1, col2 = st.columns(2)
        with col1:
            with st.container():
                st.markdown("#### 💼 Contact Form")
                st.write("Professional business contact form")
                st.caption("• Contact details\\n• Inquiry type\\n• Message")
                if st.button("Create from Template", key="biz_1"):
                    if create_template_form(user, "Business Contact Form", "contact"):
                        st.success("Contact form created!")
                        st.session_state.current_page = 'form_builder'
                        st.rerun()
        
        with col2:
            with st.container():
                st.markdown("#### 📋 Job Application")
                st.write("Professional job application form")
                st.caption("• Personal info\\n• Experience\\n• Skills assessment")
                if st.button("Create from Template", key="biz_2"):
                    if create_template_form(user, "Job Application Form", "hr"):
                        st.success("Job application form created!")
                        st.session_state.current_page = 'form_builder'
                        st.rerun()


def create_template_form(user: Dict[str, Any], form_title: str, template_type: str) -> bool:
    """Create a new form from a predefined template"""
    try:
        forms_service = FormsService()
        
        # Create the form with correct parameters
        form_result = forms_service.create_form(
            title=form_title,
            description=f"Form created from {template_type} template",
            created_by=user['id'],
            tenant_id=user['tenant_id']
        )
        
        if not form_result:
            return False
        
        form_id = form_result['id']
        
        # Add template-specific questions
        questions_service = QuestionsService()
        
        template_questions = get_template_questions(template_type)
        
        for i, question_data in enumerate(template_questions):
            # Format options correctly for the service
            options = question_data.get('options', [])
            formatted_options = []
            if options:
                for option_text in options:
                    formatted_options.append({
                        'label': option_text,
                        'value': option_text
                    })
            
            question_data_formatted = {
                'label': question_data['label'],
                'field_type': question_data['field_type'],
                'required': question_data.get('required', False),
                'placeholder': question_data.get('placeholder', ''),
                'help_text': question_data.get('help_text', ''),
                'order_index': i,
                'options': formatted_options
            }
            
            questions_service.add_question(
                form_id=form_id,
                user_id=user['id'],
                user_role=user['role'],
                question_data=question_data_formatted
            )
        
        # Store in session for form builder and set up for editing
        st.session_state['form_id'] = form_id
        st.session_state['current_form_id'] = form_id
        
        # Clear any existing form builder state so it loads fresh
        if 'form_builder_questions' in st.session_state:
            del st.session_state['form_builder_questions']
            
        return True
        
    except Exception as e:
        st.error(f"Error creating template form: {e}")
        return False


def get_template_questions(template_type: str) -> List[Dict[str, Any]]:
    """Get predefined questions for different template types"""
    templates = {
        'survey': [
            {'label': 'Overall Satisfaction', 'field_type': 'radio', 'required': True,
             'options': ['Very Satisfied', 'Satisfied', 'Neutral', 'Dissatisfied', 'Very Dissatisfied']},
            {'label': 'How likely are you to recommend us?', 'field_type': 'radio', 'required': True,
             'options': ['Very Likely', 'Likely', 'Neutral', 'Unlikely', 'Very Unlikely']},
            {'label': 'Additional Comments', 'field_type': 'long_text', 'required': False,
             'placeholder': 'Please share any additional feedback...'}
        ],
        'feedback': [
            {'label': 'Your Name', 'field_type': 'short_text', 'required': True},
            {'label': 'Email Address', 'field_type': 'short_text', 'required': True},
            {'label': 'Department', 'field_type': 'dropdown', 'required': False,
             'options': ['Sales', 'Marketing', 'Engineering', 'HR', 'Other']},
            {'label': 'Feedback', 'field_type': 'long_text', 'required': True,
             'placeholder': 'Please share your feedback...'}
        ],
        'product': [
            {'label': 'Product Rating', 'field_type': 'radio', 'required': True,
             'options': ['Excellent', 'Good', 'Average', 'Poor']},
            {'label': 'Features You Like', 'field_type': 'checkbox', 'required': False,
             'options': ['Design', 'Performance', 'Ease of Use', 'Value for Money']},
            {'label': 'Suggestions for Improvement', 'field_type': 'long_text', 'required': False}
        ],
        'service': [
            {'label': 'Service Rating', 'field_type': 'radio', 'required': True,
             'options': ['Excellent', 'Good', 'Average', 'Poor']},
            {'label': 'Staff Helpfulness', 'field_type': 'radio', 'required': True,
             'options': ['Very Helpful', 'Helpful', 'Neutral', 'Not Helpful']},
            {'label': 'Additional Comments', 'field_type': 'long_text', 'required': False}
        ],
        'event': [
            {'label': 'Full Name', 'field_type': 'short_text', 'required': True},
            {'label': 'Email Address', 'field_type': 'short_text', 'required': True},
            {'label': 'Phone Number', 'field_type': 'short_text', 'required': False},
            {'label': 'Dietary Requirements', 'field_type': 'checkbox', 'required': False,
             'options': ['Vegetarian', 'Vegan', 'Gluten-Free', 'No Restrictions']}
        ],
        'education': [
            {'label': 'Student Name', 'field_type': 'short_text', 'required': True},
            {'label': 'Student ID', 'field_type': 'short_text', 'required': True},
            {'label': 'Course Selection', 'field_type': 'dropdown', 'required': True,
             'options': ['Mathematics', 'Science', 'Literature', 'History', 'Other']},
            {'label': 'Previous Experience', 'field_type': 'long_text', 'required': False}
        ],
        'contact': [
            {'label': 'Full Name', 'field_type': 'short_text', 'required': True},
            {'label': 'Email Address', 'field_type': 'short_text', 'required': True},
            {'label': 'Company', 'field_type': 'short_text', 'required': False},
            {'label': 'Inquiry Type', 'field_type': 'dropdown', 'required': True,
             'options': ['General Inquiry', 'Support', 'Sales', 'Partnership']},
            {'label': 'Message', 'field_type': 'long_text', 'required': True,
             'placeholder': 'Please describe your inquiry...'}
        ],
        'hr': [
            {'label': 'Full Name', 'field_type': 'short_text', 'required': True},
            {'label': 'Email Address', 'field_type': 'short_text', 'required': True},
            {'label': 'Position Applied For', 'field_type': 'short_text', 'required': True},
            {'label': 'Years of Experience', 'field_type': 'dropdown', 'required': True,
             'options': ['0-1 years', '2-5 years', '6-10 years', '10+ years']},
            {'label': 'Cover Letter', 'field_type': 'long_text', 'required': False,
             'placeholder': 'Tell us why you are interested in this position...'}
        ]
    }
    
    return templates.get(template_type, [
        {'label': 'Your Name', 'field_type': 'short_text', 'required': True},
        {'label': 'Comments', 'field_type': 'long_text', 'required': False}
    ])

if __name__ == "__main__":
    main()
