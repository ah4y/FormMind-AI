"""
Form-related business logic for FormMind-AI
Handles form CRUD, versioning, questions management, templates, and role-based access
"""
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import uuid
import logging
try:
    from sqlalchemy.orm import Session
    from sqlalchemy import and_, or_, desc

    from ..models import (
        Form, FormVersion, Question, QuestionOption, Template, 
        User, Tenant, Submission
    )
    from ..db import get_db_session
    SQLALCHEMY_AVAILABLE = True
except Exception:
    # Running in a lightweight environment (tests or dev) without SQLAlchemy.
    # Service stubs below do not require DB; fall back gracefully.
    Session = None
    and_ = or_ = desc = None
    Form = FormVersion = Question = QuestionOption = Template = User = Tenant = Submission = None
    def get_db_session(*args, **kwargs):
        raise RuntimeError("Database not configured in this environment")
    SQLALCHEMY_AVAILABLE = False

logger = logging.getLogger(__name__)


# If SQLAlchemy isn't available (lightweight dev/test), expose the simple
# in-memory service stubs so teammates can iterate without a DB.
if not SQLALCHEMY_AVAILABLE:
    try:
        from .forms_stubs import (
            create_form, get_form, list_forms, update_form,
            add_question, remove_question, reorder_questions,
            save_template, create_from_template
        )
    except Exception:
        # Importing stubs failed; environment may not need them.
        pass


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
            return []
    
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
            logger.error(f"Error creating form: {e}")
            return None
    
    @staticmethod
    def get_form_by_id(form_id: int, user_id: int, user_role: str) -> Optional[Dict[str, Any]]:
        """Get form details with access control"""
        try:
            with get_db_session() as session:
                form = session.query(Form).filter(Form.id == form_id).first()
                
                if not form:
                    return None

            # --------------------------
            # DB-agnostic in-memory service stubs for Team A
            # These helpers let Team A iterate on UI and unit tests before the
            # Leader implements persistence. They are intentionally simple.
            # --------------------------

                
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
    def update_form_settings(form_id: int, user_id: int, user_role: str, 
                           **updates) -> bool:
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
                
                for field, value in updates.items():

                    if field in allowed_fields:
                        setattr(form, field, value)
                
                logger.info(f"Updated form {form_id} settings")
                return True
                
        except Exception as e:
            logger.error(f"Error updating form {form_id}: {e}")
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
            logger.error(f"Error adding question to form {form_id}: {e}")
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
