"""
Form-related business logic for FormMind-AI
Handles form CRUD, versioning, questions management, templates, and role-based access
"""
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import uuid
import logging
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from ..models import (
    Form, FormVersion, Question, QuestionOption, Template, 
    User, Tenant, Submission
)
from ..db import get_db_session

logger = logging.getLogger(__name__)

# In-memory fallback storage for when database is unavailable
_IN_MEMORY_FORMS: Dict[int, Dict[str, Any]] = {}
_IN_MEMORY_FORM_COUNTER = 1000
_IN_MEMORY_QUESTIONS: Dict[int, Dict[str, Any]] = {}
_IN_MEMORY_QUESTION_COUNTER = 2000


# Role-based access control functions
def needs_new_version_on_edit(form: Dict[str, Any], submissions_count: int) -> bool:
    """
    Decide whether an edit should create a new form version.
    
    Rules:
    - If form.status == 'published' and submissions_count > 0 => new version needed
    - If submissions_count == 0 => can edit in place
    - Otherwise conservative path: create new version when published
    """
    status = form.get("status", "draft")
    if submissions_count == 0:
        return False
    if status == "published" and submissions_count > 0:
        return True
    return False


def role_can_edit(user_role: str, user_id: int, form: Dict[str, Any]) -> bool:
    """
    Enforce role rules described in the prompt.
    - OWNER and ADMIN can manage all tenant forms
    - EDITOR can only manage forms they created (created_by)
    """
    if user_role in ("OWNER", "ADMIN"):
        return True
    if user_role == "EDITOR":
        return form.get("created_by") == user_id
    return False


def role_can_view(user_role: str, user_id: int, form: Dict[str, Any]) -> bool:
    """Check if user can view a form (same rules as edit for now)"""
    return role_can_edit(user_role, user_id, form)


# Form CRUD operations
class FormsService:
    """Service class for form operations"""
    
    @staticmethod
    def get_forms_for_user(user_id: int, user_role: str, tenant_id: int) -> List[Dict[str, Any]]:
        """Get forms visible to a user based on their role"""
        try:
            with get_db_session() as session:
                query = session.query(Form).filter(Form.tenant_id == tenant_id)
                
                # Apply role-based filtering
                if user_role == "EDITOR":
                    query = query.filter(Form.created_by == user_id)
                # OWNER and ADMIN can see all tenant forms
                
                forms = query.order_by(desc(Form.created_at)).all()
                
                result = []
                for form in forms:
                    # Get submission count for each form
                    submission_count = session.query(Submission).filter(
                        Submission.form_id == form.id
                    ).count()
                    
                    result.append({
                        'id': form.id,
                        'title': form.title,
                        'description': form.description,
                        'status': form.status,
                        'access_type': form.access_type,
                        'single_submission': form.single_submission,
                        'submission_start': form.submission_start,
                        'submission_end': form.submission_end,
                        'public_token': form.public_token,
                        'created_by': form.created_by,
                        'created_at': form.created_at,
                        'submission_count': submission_count
                    })
                
                return result
                
        except Exception as e:
            logger.error(f"Error getting forms for user {user_id}: {e}")
            # Fallback: return in-memory forms if database is unavailable
            result = []
            for form_id, form_data in _IN_MEMORY_FORMS.items():
                if form_data.get('created_by') == user_id:
                    result.append({
                        'id': form_id,
                        'title': form_data.get('title'),
                        'description': form_data.get('description'),
                        'status': form_data.get('status'),
                        'access_type': form_data.get('access_type'),
                        'single_submission': form_data.get('single_submission'),
                        'submission_start': form_data.get('submission_start'),
                        'submission_end': form_data.get('submission_end'),
                        'public_token': form_data.get('public_token'),
                        'created_by': form_data.get('created_by'),
                        'created_at': form_data.get('created_at'),
                        'submission_count': 0
                    })
            return result
    
    @staticmethod
    def create_form(title: str, description: str, created_by: int, tenant_id: int, 
                   access_type: str = "public", single_submission: bool = False) -> Optional[Dict[str, Any]]:
        """Create a new form with initial version"""
        try:
            with get_db_session() as session:
                # Generate public token for form access
                public_token = str(uuid.uuid4())
                
                # Create form
                form = Form(
                    tenant_id=tenant_id,
                    title=title,
                    description=description,
                    status="draft",
                    access_type=access_type,
                    single_submission=single_submission,
                    public_token=public_token,
                    created_by=created_by
                )
                session.add(form)
                session.flush()  # Get the form ID
                
                # Create initial version
                form_version = FormVersion(
                    form_id=form.id,
                    version_number=1,
                    is_active=True
                )
                session.add(form_version)
                session.flush()
                
                logger.info(f"Created form {form.id} with version {form_version.id}")
                
                return {
                    'id': form.id,
                    'title': form.title,
                    'description': form.description,
                    'status': form.status,
                    'access_type': form.access_type,
                    'single_submission': form.single_submission,
                    'public_token': form.public_token,
                    'created_by': form.created_by,
                    'version_id': form_version.id,
                    'version_number': form_version.version_number
                }
                
        except Exception as e:
            logger.error(f"Error creating form (trying in-memory fallback): {e}")
            # Fallback to in-memory storage
            global _IN_MEMORY_FORM_COUNTER
            _IN_MEMORY_FORM_COUNTER += 1
            form_id = _IN_MEMORY_FORM_COUNTER
            public_token = str(uuid.uuid4())
            
            form_data = {
                'id': form_id,
                'title': title,
                'description': description,
                'status': 'draft',
                'access_type': access_type,
                'single_submission': single_submission,
                'public_token': public_token,
                'created_by': created_by,
                'version_id': 1,
                'version_number': 1,
                'created_at': datetime.now()
            }
            _IN_MEMORY_FORMS[form_id] = form_data
            logger.info(f"Created in-memory form {form_id}")
            return form_data
    
    @staticmethod
    def get_form_by_id(form_id: int, user_id: int, user_role: str) -> Optional[Dict[str, Any]]:
        """Get form details with access control"""
        try:
            with get_db_session() as session:
                form = session.query(Form).filter(Form.id == form_id).first()
                
                if not form:
                    return None
                
                # Check access permissions
                form_dict = {'created_by': form.created_by}
                if not role_can_view(user_role, user_id, form_dict):
                    return None
                
                # Get active version
                active_version = session.query(FormVersion).filter(
                    and_(FormVersion.form_id == form_id, FormVersion.is_active == True)
                ).first()
                
                # Get questions for active version
                questions = []
                if active_version:
                    questions_query = session.query(Question).filter(
                        Question.form_version_id == active_version.id
                    ).order_by(Question.order_index).all()
                    
                    for question in questions_query:
                        # Get options for choice questions
                        options = session.query(QuestionOption).filter(
                            QuestionOption.question_id == question.id
                        ).order_by(QuestionOption.order_index).all()
                        
                        questions.append({
                            'id': question.id,
                            'label': question.label,
                            'placeholder': question.placeholder,
                            'help_text': question.help_text,
                            'field_type': question.field_type,
                            'required': question.required,
                            'default_value': question.default_value,
                            'order_index': question.order_index,
                            'validation_min': question.validation_min,
                            'validation_max': question.validation_max,
                            'validation_regex': question.validation_regex,
                            'options': [
                                {
                                    'id': opt.id,
                                    'label': opt.label,
                                    'value': opt.value,
                                    'order_index': opt.order_index
                                }
                                for opt in options
                            ]
                        })
                
                return {
                    'id': form.id,
                    'title': form.title,
                    'description': form.description,
                    'status': form.status,
                    'access_type': form.access_type,
                    'single_submission': form.single_submission,
                    'submission_start': form.submission_start,
                    'submission_end': form.submission_end,
                    'public_token': form.public_token,
                    'created_by': form.created_by,
                    'created_at': form.created_at,
                    'version_id': active_version.id if active_version else None,
                    'version_number': active_version.version_number if active_version else None,
                    'questions': questions
                }
                
        except Exception as e:
            logger.error(f"Error getting form {form_id}: {e}")
            return None
    
    @staticmethod
    def get_form_by_token(token: str) -> Optional[Dict[str, Any]]:
        """Get form by public token for public access"""
        try:
            with get_db_session() as session:
                form = session.query(Form).filter(Form.public_token == token).first()
                
                if not form:
                    return None
                
                # Get active version
                active_version = session.query(FormVersion).filter(
                    and_(FormVersion.form_id == form.id, FormVersion.is_active == True)
                ).first()
                
                return {
                    'id': form.id,
                    'title': form.title,
                    'description': form.description,
                    'status': form.status,
                    'access_type': form.access_type,
                    'single_submission': form.single_submission,
                    'submission_start': form.submission_start,
                    'submission_end': form.submission_end,
                    'public_token': form.public_token,
                    'created_by': form.created_by,
                    'created_at': form.created_at,
                    'version_id': active_version.id if active_version else None,
                    'version_number': active_version.version_number if active_version else None
                }
                
        except Exception as e:
            logger.error(f"Error getting form by token {token}: {e}")
            return None
    
    @staticmethod
    def update_form_settings(form_id: int, user_id: int, user_role: str, 
                           settings: Dict[str, Any]) -> bool:
        """Update form settings with access control"""
        try:
            with get_db_session() as session:
                form = session.query(Form).filter(Form.id == form_id).first()
                
                if not form:
                    return False
                
                # Check edit permissions
                form_dict = {'created_by': form.created_by}
                if not role_can_edit(user_role, user_id, form_dict):
                    return False
                
                # Update allowed fields
                allowed_fields = [
                    'title', 'description', 'status', 'access_type', 
                    'single_submission', 'submission_start', 'submission_end'
                ]
                
                for field, value in settings.items():
                    if field in allowed_fields:
                        setattr(form, field, value)
                
                logger.info(f"Updated form {form_id} settings")
                return True
                
        except Exception as e:
            logger.error(f"Error updating form {form_id} (trying in-memory fallback): {e}")
            # Fallback to in-memory storage
            if form_id in _IN_MEMORY_FORMS:
                allowed_fields = [
                    'title', 'description', 'status', 'access_type', 
                    'single_submission', 'submission_start', 'submission_end'
                ]
                for field, value in settings.items():
                    if field in allowed_fields:
                        _IN_MEMORY_FORMS[form_id][field] = value
                logger.info(f"Updated in-memory form {form_id} settings")
                return True
            return False
    
    @staticmethod
    def delete_form(form_id: int, user_id: int, user_role: str) -> bool:
        """Delete form with access control"""
        try:
            with get_db_session() as session:
                form = session.query(Form).filter(Form.id == form_id).first()
                
                if not form:
                    return False
                
                # Check edit permissions
                form_dict = {'created_by': form.created_by}
                if not role_can_edit(user_role, user_id, form_dict):
                    return False
                
                session.delete(form)
                logger.info(f"Deleted form {form_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error deleting form {form_id}: {e}")
            return False
    
    @staticmethod
    def duplicate_form(form_id: int, user_id: int, user_role: str, new_title: str = None) -> Optional[int]:
        """Create a copy of an existing form with all its questions"""
        try:
            with get_db_session() as session:
                # Get original form
                original_form = session.query(Form).filter(Form.id == form_id).first()
                
                if not original_form:
                    return None
                
                # Check read permissions for original form
                form_dict = {'created_by': original_form.created_by}
                if not role_can_view(user_role, user_id, form_dict):
                    return None
                
                # Create new form with copied data
                new_form_title = new_title or f"Copy of {original_form.title}"
                
                new_form = Form(
                    tenant_id=original_form.tenant_id,
                    title=new_form_title,
                    description=original_form.description,
                    status='draft',
                    created_by=user_id,
                    public_token=str(uuid.uuid4())
                )
                session.add(new_form)
                session.flush()
                
                # Create new form version
                new_version = FormVersion(
                    form_id=new_form.id,
                    version_number=1,
                    is_active=True
                )
                session.add(new_version)
                session.flush()
                
                # Copy questions from original form's active version
                original_version = session.query(FormVersion).filter(
                    FormVersion.form_id == form_id,
                    FormVersion.is_active == True
                ).first()
                
                if original_version:
                    original_questions = session.query(Question).filter(
                        Question.form_version_id == original_version.id
                    ).order_by(Question.order_index).all()
                    
                    for orig_q in original_questions:
                        new_question = Question(
                            form_version_id=new_version.id,
                            label=orig_q.label,
                            placeholder=orig_q.placeholder,
                            help_text=orig_q.help_text,
                            field_type=orig_q.field_type,
                            required=orig_q.required,
                            default_value=orig_q.default_value,
                            order_index=orig_q.order_index,
                            validation_min=orig_q.validation_min,
                            validation_max=orig_q.validation_max,
                            validation_regex=orig_q.validation_regex
                        )
                        session.add(new_question)
                        session.flush()
                        
                        # Copy question options if any
                        original_options = session.query(QuestionOption).filter(
                            QuestionOption.question_id == orig_q.id
                        ).order_by(QuestionOption.order_index).all()
                        
                        for orig_option in original_options:
                            new_option = QuestionOption(
                                question_id=new_question.id,
                                label=orig_option.label,
                                value=orig_option.value,
                                order_index=orig_option.order_index
                            )
                            session.add(new_option)
                
                logger.info(f"Duplicated form {form_id} as {new_form.id}")
                return new_form.id
                
        except Exception as e:
            logger.error(f"Error duplicating form {form_id}: {e}")
            return None


# Question management
class QuestionsService:
    """Service class for question operations"""
    
    @staticmethod
    def add_question(form_id: int, user_id: int, user_role: str, 
                    question_data: Dict[str, Any]) -> Optional[int]:
        """Add question to form with versioning logic"""
        try:
            with get_db_session() as session:
                form = session.query(Form).filter(Form.id == form_id).first()
                
                if not form:
                    return None
                
                # Check edit permissions
                form_dict = {'created_by': form.created_by, 'status': form.status}
                if not role_can_edit(user_role, user_id, form_dict):
                    return None
                
                # Check if we need a new version
                submission_count = session.query(Submission).filter(
                    Submission.form_id == form_id
                ).count()
                
                if needs_new_version_on_edit(form_dict, submission_count):
                    version_id = QuestionsService._create_new_version(session, form_id)
                else:
                    # Use active version
                    active_version = session.query(FormVersion).filter(
                        and_(FormVersion.form_id == form_id, FormVersion.is_active == True)
                    ).first()
                    version_id = active_version.id if active_version else None
                
                if not version_id:
                    return None
                
                # Get next order index
                max_order = session.query(Question.order_index).filter(
                    Question.form_version_id == version_id
                ).order_by(desc(Question.order_index)).first()
                
                next_order = (max_order[0] + 1) if max_order and max_order[0] else 0
                
                # Create question
                question = Question(
                    form_version_id=version_id,
                    label=question_data.get('label', ''),
                    placeholder=question_data.get('placeholder'),
                    help_text=question_data.get('help_text'),
                    field_type=question_data.get('field_type', 'short_text'),
                    required=question_data.get('required', False),
                    default_value=question_data.get('default_value'),
                    order_index=next_order,
                    validation_min=question_data.get('validation_min'),
                    validation_max=question_data.get('validation_max'),
                    validation_regex=question_data.get('validation_regex')
                )
                session.add(question)
                session.flush()
                
                # Add options for choice questions
                options = question_data.get('options', [])
                if options and question.field_type in ['radio', 'checkbox', 'dropdown']:
                    for i, option in enumerate(options):
                        option_obj = QuestionOption(
                            question_id=question.id,
                            label=option.get('label', ''),
                            value=option.get('value', option.get('label', '')),
                            order_index=i
                        )
                        session.add(option_obj)
                
                logger.info(f"Added question {question.id} to form {form_id}")
                return question.id
                
        except Exception as e:
            logger.error(f"Error adding question to form {form_id} (trying in-memory fallback): {e}")
            # Fallback to in-memory storage
            if form_id in _IN_MEMORY_FORMS:
                global _IN_MEMORY_QUESTION_COUNTER
                _IN_MEMORY_QUESTION_COUNTER += 1
                question_id = _IN_MEMORY_QUESTION_COUNTER
                
                question_data_copy = question_data.copy()
                _IN_MEMORY_QUESTIONS[question_id] = {
                    'id': question_id,
                    'form_id': form_id,
                    **question_data_copy
                }
                logger.info(f"Added in-memory question {question_id} to form {form_id}")
                return question_id
            return None
    
    @staticmethod
    def _create_new_version(session: Session, form_id: int) -> Optional[int]:
        """Create new version and copy questions from active version"""
        try:
            # Get current active version
            current_version = session.query(FormVersion).filter(
                and_(FormVersion.form_id == form_id, FormVersion.is_active == True)
            ).first()
            
            # Get next version number
            max_version = session.query(FormVersion.version_number).filter(
                FormVersion.form_id == form_id
            ).order_by(desc(FormVersion.version_number)).first()
            
            next_version_num = (max_version[0] + 1) if max_version else 1
            
            # Create new version
            new_version = FormVersion(
                form_id=form_id,
                version_number=next_version_num,
                is_active=True
            )
            session.add(new_version)
            session.flush()
            
            # Deactivate old version
            if current_version:
                current_version.is_active = False
                
                # Copy questions from old version
                old_questions = session.query(Question).filter(
                    Question.form_version_id == current_version.id
                ).order_by(Question.order_index).all()
                
                for old_q in old_questions:
                    new_question = Question(
                        form_version_id=new_version.id,
                        label=old_q.label,
                        placeholder=old_q.placeholder,
                        help_text=old_q.help_text,
                        field_type=old_q.field_type,
                        required=old_q.required,
                        default_value=old_q.default_value,
                        order_index=old_q.order_index,
                        validation_min=old_q.validation_min,
                        validation_max=old_q.validation_max,
                        validation_regex=old_q.validation_regex
                    )
                    session.add(new_question)
                    session.flush()
                    
                    # Copy options
                    old_options = session.query(QuestionOption).filter(
                        QuestionOption.question_id == old_q.id
                    ).order_by(QuestionOption.order_index).all()
                    
                    for old_opt in old_options:
                        new_option = QuestionOption(
                            question_id=new_question.id,
                            label=old_opt.label,
                            value=old_opt.value,
                            order_index=old_opt.order_index
                        )
                        session.add(new_option)
            
            logger.info(f"Created new version {new_version.id} for form {form_id}")
            return new_version.id
            
        except Exception as e:
            logger.error(f"Error creating new version for form {form_id}: {e}")
            return None
    
    @staticmethod
    def get_questions_for_form(form_id: int) -> List[Dict[str, Any]]:
        """Get all questions for a form (public access)"""
        try:
            with get_db_session() as session:
                # Get active version
                active_version = session.query(FormVersion).filter(
                    and_(FormVersion.form_id == form_id, FormVersion.is_active == True)
                ).first()
                
                if not active_version:
                    return []
                
                # Get questions for active version
                questions_query = session.query(Question).filter(
                    Question.form_version_id == active_version.id
                ).order_by(Question.order_index).all()
                
                questions = []
                for question in questions_query:
                    # Get options if applicable
                    options = []
                    if question.field_type in ['multiple_choice', 'checkboxes', 'dropdown']:
                        options_query = session.query(QuestionOption).filter(
                            QuestionOption.question_id == question.id
                        ).order_by(QuestionOption.order_index).all()
                        options = [opt.label for opt in options_query]
                    
                    questions.append({
                        'id': question.id,
                        'label': question.label,
                        'placeholder': question.placeholder,
                        'help_text': question.help_text,
                        'field_type': question.field_type,
                        'required': question.required,
                        'default_value': question.default_value,
                        'order_index': question.order_index,
                        'options': options
                    })
                
                return questions
                
        except Exception as e:
            logger.error(f"Error getting questions for form {form_id}: {e}")
            return []


# Template operations
class TemplateService:
    """Service class for template operations"""
    
    @staticmethod
    def save_form_as_template(form_id: int, template_name: str, category: str,
                             visibility: str, created_by: int, tenant_id: int) -> Optional[int]:
        """Save existing form structure as template"""
        try:
            with get_db_session() as session:
                # Create template record
                template = Template(
                    tenant_id=tenant_id,
                    name=template_name,
                    category=category,
                    visibility=visibility,
                    created_by=created_by
                )
                session.add(template)
                session.flush()
                
                # TODO: Store template questions structure
                # For now, we'll implement a simple reference system
                # In a full implementation, we'd copy the question structure
                
                logger.info(f"Created template {template.id} from form {form_id}")
                return template.id
                
        except Exception as e:
            logger.error(f"Error creating template from form {form_id}: {e}")
            return None
    
    @staticmethod
    def get_templates(tenant_id: int, user_id: int, visibility_filter: str = "all") -> List[Dict[str, Any]]:
        """Get available templates based on visibility"""
        try:
            with get_db_session() as session:
                query = session.query(Template)
                
                if visibility_filter == "private":
                    query = query.filter(
                        and_(Template.created_by == user_id, Template.visibility == "private")
                    )
                elif visibility_filter == "tenant":
                    query = query.filter(
                        and_(Template.tenant_id == tenant_id, Template.visibility.in_(["private", "tenant"]))
                    )
                else:  # all
                    query = query.filter(
                        or_(
                            Template.visibility == "public",
                            and_(Template.tenant_id == tenant_id, Template.visibility == "tenant"),
                            and_(Template.created_by == user_id, Template.visibility == "private")
                        )
                    )
                
                templates = query.order_by(desc(Template.created_at)).all()
                
                return [
                    {
                        'id': t.id,
                        'name': t.name,
                        'category': t.category,
                        'visibility': t.visibility,
                        'created_by': t.created_by,
                        'created_at': t.created_at
                    }
                    for t in templates
                ]
                
        except Exception as e:
            logger.error(f"Error getting templates: {e}")
            return []
