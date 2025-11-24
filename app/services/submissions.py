"""
Submission-related business logic for FormMind-AI
Handles form submissions, validation, single-submission enforcement, and submission window checks
"""
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import logging
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func

from ..models import Form, FormVersion, Question, QuestionOption, Submission, Answer, User
from ..db import get_db_session

logger = logging.getLogger(__name__)


class SubmissionsService:
    """Service class for form submission operations"""
    
    @staticmethod
    def validate_submission_window(form: Form) -> Tuple[bool, str]:
        """Check if form is accepting submissions based on time window"""
        now = datetime.now()
        
        if form.submission_start and now < form.submission_start:
            return False, f"Submission period starts on {form.submission_start.strftime('%Y-%m-%d %H:%M')}"
        
        if form.submission_end and now > form.submission_end:
            return False, f"Submission period ended on {form.submission_end.strftime('%Y-%m-%d %H:%M')}"
        
        return True, "Submission window is open"
    
    @staticmethod
    def check_single_submission_rule(form: Form, user_id: Optional[int] = None, 
                                   ip_address: Optional[str] = None) -> Tuple[bool, str]:
        """Check if user can submit based on single submission rules"""
        if not form.single_submission:
            return True, "Multiple submissions allowed"
        
        try:
            with get_db_session() as session:
                # Check for existing submissions
                query = session.query(Submission).filter(Submission.form_id == form.id)
                
                if user_id:
                    # For authenticated users, check by user_id
                    existing = query.filter(Submission.user_id == user_id).first()
                    if existing:
                        return False, "You have already submitted this form"
                
                elif ip_address:
                    # For anonymous users, check by guest_token (IP address)
                    existing = query.filter(Submission.guest_token == ip_address).first()
                    if existing:
                        return False, "A submission from this IP address already exists"
                
                return True, "Submission allowed"
                
        except Exception as e:
            logger.error(f"Error checking single submission rule: {e}")
            return False, "Error validating submission rules"
    
    @staticmethod
    def validate_submission_data(form_version_id: int, submission_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate submission data against form questions"""
        errors = []
        
        try:
            with get_db_session() as session:
                # Get all questions for this form version
                questions = session.query(Question).filter(
                    Question.form_version_id == form_version_id
                ).order_by(Question.order_index).all()
                
                for question in questions:
                    field_key = f"question_{question.id}"
                    value = submission_data.get(field_key)
                    
                    # Check required fields
                    if question.required and (value is None or str(value).strip() == ""):
                        errors.append(f"Question '{question.label}' is required")
                        continue
                    
                    if value is None or str(value).strip() == "":
                        continue  # Skip validation for empty optional fields
                    
                    # Type-specific validation
                    if question.field_type == "number":
                        try:
                            num_value = float(value)
                            if question.validation_min is not None and num_value < question.validation_min:
                                errors.append(f"'{question.label}' must be at least {question.validation_min}")
                            if question.validation_max is not None and num_value > question.validation_max:
                                errors.append(f"'{question.label}' must be at most {question.validation_max}")
                        except ValueError:
                            errors.append(f"'{question.label}' must be a valid number")
                    
                    elif question.field_type == "email":
                        if "@" not in str(value) or "." not in str(value):
                            errors.append(f"'{question.label}' must be a valid email address")
                    
                    elif question.field_type in ["short_text", "long_text"]:
                        text_length = len(str(value))
                        if question.validation_min is not None and text_length < question.validation_min:
                            errors.append(f"'{question.label}' must be at least {question.validation_min} characters")
                        if question.validation_max is not None and text_length > question.validation_max:
                            errors.append(f"'{question.label}' must be at most {question.validation_max} characters")
                    
                    elif question.field_type in ["radio", "dropdown"]:
                        # Validate choice options
                        valid_options = session.query(QuestionOption.value).filter(
                            QuestionOption.question_id == question.id
                        ).all()
                        valid_values = [opt[0] for opt in valid_options]
                        
                        if str(value) not in valid_values:
                            errors.append(f"'{question.label}' has an invalid selection")
                    
                    elif question.field_type == "checkbox":
                        # Validate multiple choice options
                        if isinstance(value, list):
                            valid_options = session.query(QuestionOption.value).filter(
                                QuestionOption.question_id == question.id
                            ).all()
                            valid_values = [opt[0] for opt in valid_options]
                            
                            for selected_value in value:
                                if str(selected_value) not in valid_values:
                                    errors.append(f"'{question.label}' has an invalid selection: {selected_value}")
                        else:
                            errors.append(f"'{question.label}' must be a list for checkbox type")
                
                return len(errors) == 0, errors
                
        except Exception as e:
            logger.error(f"Error validating submission data: {e}")
            return False, ["Error validating submission data"]
    
    @staticmethod
    def submit_form(form_id: int, submission_data: Dict[str, Any], 
                   user_id: Optional[int] = None, ip_address: Optional[str] = None) -> Tuple[bool, str, Optional[int]]:
        """Submit form with full validation and rule enforcement"""
        try:
            with get_db_session() as session:
                # Get form details
                form = session.query(Form).filter(Form.id == form_id).first()
                if not form:
                    return False, "Form not found", None
                
                # Check if form is accepting submissions
                if form.status != "published":
                    return False, "Form is not published", None
                
                # Validate submission window
                window_valid, window_message = SubmissionsService.validate_submission_window(form)
                if not window_valid:
                    return False, window_message, None
                
                # Check single submission rules
                single_valid, single_message = SubmissionsService.check_single_submission_rule(
                    form, user_id, ip_address
                )
                if not single_valid:
                    return False, single_message, None
                
                # Get active form version
                active_version = session.query(FormVersion).filter(
                    and_(FormVersion.form_id == form_id, FormVersion.is_active == True)
                ).first()
                
                if not active_version:
                    return False, "Form version not found", None
                
                # Validate submission data
                data_valid, validation_errors = SubmissionsService.validate_submission_data(
                    active_version.id, submission_data
                )
                if not data_valid:
                    return False, "; ".join(validation_errors), None
                
                # Create submission record
                submission = Submission(
                    form_id=form_id,
                    form_version_id=active_version.id,
                    user_id=user_id,
                    ip_address=ip_address,
                    submitted_at=datetime.now()
                )
                session.add(submission)
                session.flush()  # Get submission ID
                
                # Store answers
                questions = session.query(Question).filter(
                    Question.form_version_id == active_version.id
                ).all()
                
                for question in questions:
                    field_key = f"question_{question.id}"
                    value = submission_data.get(field_key)
                    
                    if value is not None and str(value).strip() != "":
                        # Handle different field types
                        if question.field_type == "checkbox" and isinstance(value, list):
                            # Store as JSON string for multiple values
                            import json
                            value_str = json.dumps(value)
                        else:
                            value_str = str(value)
                        
                        answer = Answer(
                            submission_id=submission.id,
                            question_id=question.id,
                            value=value_str
                        )
                        session.add(answer)
                
                logger.info(f"Created submission {submission.id} for form {form_id}")
                return True, "Submission successful", submission.id
                
        except Exception as e:
            logger.error(f"Error submitting form {form_id}: {e}")
            return False, f"Error processing submission: {str(e)}", None
    
    @staticmethod
    def get_form_submissions(form_id: int, user_id: int, user_role: str) -> List[Dict[str, Any]]:
        """Get submissions for a form with access control"""
        try:
            with get_db_session() as session:
                # Check form access
                form = session.query(Form).filter(Form.id == form_id).first()
                if not form:
                    return []
                
                # Apply role-based access control
                if user_role == "EDITOR" and form.created_by != user_id:
                    return []
                
                # Get submissions with user info
                submissions = session.query(Submission).filter(
                    Submission.form_id == form_id
                ).order_by(desc(Submission.submitted_at)).all()
                
                result = []
                for submission in submissions:
                    # Get submitter info if available
                    submitter_name = "Anonymous"
                    if submission.user_id:
                        user = session.query(User).filter(User.id == submission.user_id).first()
                        if user:
                            submitter_name = user.email
                    
                    # Get answers
                    answers = session.query(Answer).join(Question).filter(
                        Answer.submission_id == submission.id
                    ).order_by(Question.order_index).all()
                    
                    answer_data = {}
                    for answer in answers:
                        question_label = answer.question.label
                        answer_data[question_label] = answer.value
                    
                    result.append({
                        'id': submission.id,
                        'submitted_at': submission.submitted_at,
                        'user_id': submitter_name,
                        'guest_token': submission.guest_token,
                        'answers': answer_data
                    })
                
                return result
                
        except Exception as e:
            logger.error(f"Error getting submissions for form {form_id}: {e}")
            return []
    
    @staticmethod
    def get_submission_by_id(submission_id: int, user_id: int, user_role: str) -> Optional[Dict[str, Any]]:
        """Get detailed submission data with access control"""
        try:
            with get_db_session() as session:
                submission = session.query(Submission).filter(Submission.id == submission_id).first()
                if not submission:
                    return None
                
                # Check form access
                form = session.query(Form).filter(Form.id == submission.form_id).first()
                if user_role == "EDITOR" and form.created_by != user_id:
                    return None
                
                # Get detailed answers with question info
                answers = session.query(Answer).join(Question).filter(
                    Answer.submission_id == submission_id
                ).order_by(Question.order_index).all()
                
                detailed_answers = []
                for answer in answers:
                    question = answer.question
                    
                    # Parse checkbox values
                    value = answer.value
                    if question.field_type == "checkbox":
                        try:
                            import json
                            value = json.loads(answer.value)
                        except:
                            pass
                    
                    detailed_answers.append({
                        'question_id': question.id,
                        'question_label': question.label,
                        'question_type': question.field_type,
                        'value': value
                    })
                
                return {
                    'id': submission.id,
                    'form_id': submission.form_id,
                    'submitted_at': submission.submitted_at,
                    'user_id': submission.user_id,
                    'guest_token': submission.guest_token,
                    'answers': answers
                }
                
        except Exception as e:
            logger.error(f"Error getting submission {submission_id}: {e}")
            return None
    
    @staticmethod
    def get_form_by_public_token(public_token: str) -> Optional[Dict[str, Any]]:
        """Get form details for public submission using token"""
        try:
            with get_db_session() as session:
                form = session.query(Form).filter(Form.public_token == public_token).first()
                
                if not form or form.status != "published":
                    return None
                
                # Get active version and questions
                active_version = session.query(FormVersion).filter(
                    and_(FormVersion.form_id == form.id, FormVersion.is_active == True)
                ).first()
                
                if not active_version:
                    return None
                
                questions = session.query(Question).filter(
                    Question.form_version_id == active_version.id
                ).order_by(Question.order_index).all()
                
                question_list = []
                for question in questions:
                    # Get options for choice questions
                    options = session.query(QuestionOption).filter(
                        QuestionOption.question_id == question.id
                    ).order_by(QuestionOption.order_index).all()
                    
                    question_list.append({
                        'id': question.id,
                        'label': question.label,
                        'placeholder': question.placeholder,
                        'help_text': question.help_text,
                        'field_type': question.field_type,
                        'required': question.required,
                        'default_value': question.default_value,
                        'validation_min': question.validation_min,
                        'validation_max': question.validation_max,
                        'options': [
                            {
                                'label': opt.label,
                                'value': opt.value
                            }
                            for opt in options
                        ]
                    })
                
                return {
                    'id': form.id,
                    'title': form.title,
                    'description': form.description,
                    'single_submission': form.single_submission,
                    'submission_start': form.submission_start,
                    'submission_end': form.submission_end,
                    'questions': question_list
                }
                
        except Exception as e:
            logger.error(f"Error getting form by token {public_token}: {e}")
            return None
    
    @staticmethod
    def create_submission(form_id: int, answers: Dict[int, Any], 
                         user_id: Optional[int] = None, ip_address: Optional[str] = None) -> Optional[int]:
        """Create a new form submission with answers"""
        try:
            with get_db_session() as session:
                # Get form to validate
                form = session.query(Form).filter(Form.id == form_id).first()
                if not form:
                    logger.error(f"Form {form_id} not found")
                    return None
                
                # Check submission window
                can_submit_time, time_msg = SubmissionsService.validate_submission_window(form)
                if not can_submit_time:
                    logger.error(f"Submission window check failed: {time_msg}")
                    return None
                
                # Check single submission rule
                can_submit_single, single_msg = SubmissionsService.check_single_submission_rule(
                    form, user_id, ip_address
                )
                if not can_submit_single:
                    logger.error(f"Single submission check failed: {single_msg}")
                    return None
                
                # Get the active form version
                active_version = session.query(FormVersion).filter(
                    and_(FormVersion.form_id == form_id, FormVersion.is_active == True)
                ).first()
                
                if not active_version:
                    logger.error(f"No active version found for form {form_id}")
                    return None
                
                # Create submission record
                submission = Submission(
                    form_id=form_id,
                    form_version_id=active_version.id,
                    user_id=user_id,
                    guest_token=ip_address,  # Use guest_token field for IP tracking
                    submitted_at=datetime.now()
                )
                session.add(submission)
                session.flush()  # Get submission ID
                
                # Create answer records
                for question_id, answer_value in answers.items():
                    if answer_value is not None and answer_value != "":
                        # Convert answer to string for storage
                        if isinstance(answer_value, (list, tuple)):
                            answer_text = ", ".join(str(v) for v in answer_value)
                        else:
                            answer_text = str(answer_value)
                        
                        answer = Answer(
                            submission_id=submission.id,
                            question_id=question_id,
                            value=answer_text
                        )
                        session.add(answer)
                
                session.commit()
                logger.info(f"Created submission {submission.id} for form {form_id}")
                return submission.id
                
        except Exception as e:
            logger.error(f"Error creating submission for form {form_id}: {e}")
            return None


# Legacy helper functions for compatibility with existing tests
def can_submit(user_id, form: Dict, existing_submissions: List[Dict]) -> bool:
    """Enforce single_submission: if true, a logged-in user may only submit once."""
    if not form.get("single_submission"):
        return True
    if not user_id:
        # guests are allowed but may be tracked separately
        return True
    for s in existing_submissions:
        if s.get("user_id") == user_id and s.get("form_id") == form.get("id"):
            return False
    return True


def validate_submission(form: Dict, answers: List[Dict]) -> List[str]:
    """Simple validation for required fields. Answers is a list of {question_id, value}.
    Return list of error messages (empty if ok).
    """
    errors = []
    # For this lightweight implementation, question metadata may be embedded in form['questions']
    questions = {q['id']: q for q in form.get('questions', [])}
    for qid, q in questions.items():
        if q.get('required'):
            found = False
            for a in answers:
                if a.get('question_id') == qid and a.get('value') not in (None, ""):
                    found = True
            if not found:
                errors.append(f"Question '{q.get('label')}' is required.")
    return errors
