"""
Analytics and reporting services for FormMind-AI
Provides summary metrics, choice/numeric stats, and text processing analytics
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc
from collections import Counter
import json

from ..models import Form, Submission, Answer, Question, QuestionOption
from ..db import get_db_session

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service class for analytics and reporting operations"""
    
    @staticmethod
    def get_form_summary_stats(form_id: int, user_id: int, user_role: str) -> Optional[Dict[str, Any]]:
        """Get high-level summary statistics for a form"""
        try:
            with get_db_session() as session:
                # Check form access
                form = session.query(Form).filter(Form.id == form_id).first()
                if not form:
                    return None
                
                # Apply role-based access control
                if user_role == "EDITOR" and form.created_by != user_id:
                    return None
                
                # Get submission count
                total_submissions = session.query(Submission).filter(
                    Submission.form_id == form_id
                ).count()
                
                # Get submission count by date (last 30 days)
                thirty_days_ago = datetime.now() - timedelta(days=30)
                recent_submissions = session.query(
                    func.date(Submission.submitted_at).label('date'),
                    func.count(Submission.id).label('count')
                ).filter(
                    and_(
                        Submission.form_id == form_id,
                        Submission.submitted_at >= thirty_days_ago
                    )
                ).group_by(
                    func.date(Submission.submitted_at)
                ).order_by('date').all()
                
                # Get completion rate (submissions vs. partial submissions)
                # For now, we'll consider all submissions as complete
                completion_rate = 100.0 if total_submissions > 0 else 0.0
                
                # Get average completion time (placeholder - would need timing data)
                avg_completion_time = None
                
                # Get top referrers (placeholder - would need referrer tracking)
                top_referrers = []
                
                return {
                    'form_id': form_id,
                    'form_title': form.title,
                    'total_submissions': total_submissions,
                    'completion_rate': completion_rate,
                    'avg_completion_time': avg_completion_time,
                    'submissions_by_date': [
                        {'date': str(row.date), 'count': row.count}
                        for row in recent_submissions
                    ],
                    'top_referrers': top_referrers,
                    'form_status': form.status,
                    'created_at': form.created_at
                }
                
        except Exception as e:
            logger.error(f"Error getting form summary stats for {form_id}: {e}")
            return None
    
    @staticmethod
    def get_question_analytics(form_id: int, user_id: int, user_role: str) -> List[Dict[str, Any]]:
        """Get detailed analytics for each question in a form"""
        try:
            with get_db_session() as session:
                # Check form access
                form = session.query(Form).filter(Form.id == form_id).first()
                if not form or (user_role == "EDITOR" and form.created_by != user_id):
                    return []
                
                # Get all questions for the form
                questions = session.query(Question).join(
                    Submission, Question.form_version_id == Submission.form_version_id
                ).filter(Submission.form_id == form_id).distinct().order_by(Question.order_index).all()
                
                question_analytics = []
                
                for question in questions:
                    # Get all answers for this question
                    answers = session.query(Answer).filter(
                        Answer.question_id == question.id
                    ).all()
                    
                    total_responses = len(answers)
                    
                    analytics = {
                        'question_id': question.id,
                        'question_label': question.label,
                        'question_type': question.field_type,
                        'total_responses': total_responses,
                        'response_rate': (total_responses / session.query(Submission).filter(
                            Submission.form_id == form_id
                        ).count()) * 100 if total_responses > 0 else 0.0
                    }
                    
                    # Type-specific analytics
                    if question.field_type in ['radio', 'dropdown']:
                        analytics.update(AnalyticsService._analyze_choice_question(question, answers, session))
                    elif question.field_type == 'checkbox':
                        analytics.update(AnalyticsService._analyze_checkbox_question(question, answers, session))
                    elif question.field_type == 'number':
                        analytics.update(AnalyticsService._analyze_numeric_question(answers))
                    elif question.field_type in ['short_text', 'long_text', 'email']:
                        analytics.update(AnalyticsService._analyze_text_question(answers))
                    
                    question_analytics.append(analytics)
                
                return question_analytics
                
        except Exception as e:
            logger.error(f"Error getting question analytics for form {form_id}: {e}")
            return []
    
    @staticmethod
    def _analyze_choice_question(question: Question, answers: List[Answer], session: Session) -> Dict[str, Any]:
        """Analyze single-choice questions (radio, dropdown)"""
        # Count responses by value
        value_counts = Counter([answer.value for answer in answers])
        
        # Get all possible options
        options = session.query(QuestionOption).filter(
            QuestionOption.question_id == question.id
        ).order_by(QuestionOption.order_index).all()
        
        choice_distribution = []
        for option in options:
            count = value_counts.get(option.value, 0)
            percentage = (count / len(answers)) * 100 if answers else 0
            choice_distribution.append({
                'label': option.label,
                'value': option.value,
                'count': count,
                'percentage': round(percentage, 2)
            })
        
        # Find most popular choice
        most_popular = max(choice_distribution, key=lambda x: x['count']) if choice_distribution else None
        
        return {
            'choice_distribution': choice_distribution,
            'most_popular_choice': most_popular,
            'unique_responses': len(value_counts)
        }
    
    @staticmethod
    def _analyze_checkbox_question(question: Question, answers: List[Answer], session: Session) -> Dict[str, Any]:
        """Analyze multiple-choice questions (checkbox)"""
        # Parse JSON values and count individual selections
        all_selections = []
        for answer in answers:
            try:
                selections = json.loads(answer.value) if answer.value.startswith('[') else [answer.value]
                all_selections.extend(selections)
            except:
                all_selections.append(answer.value)
        
        value_counts = Counter(all_selections)
        
        # Get all possible options
        options = session.query(QuestionOption).filter(
            QuestionOption.question_id == question.id
        ).order_by(QuestionOption.order_index).all()
        
        selection_distribution = []
        for option in options:
            count = value_counts.get(option.value, 0)
            percentage = (count / len(answers)) * 100 if answers else 0
            selection_distribution.append({
                'label': option.label,
                'value': option.value,
                'count': count,
                'percentage': round(percentage, 2)
            })
        
        # Calculate average selections per response
        avg_selections = len(all_selections) / len(answers) if answers else 0
        
        return {
            'selection_distribution': selection_distribution,
            'avg_selections_per_response': round(avg_selections, 2),
            'total_selections': len(all_selections)
        }
    
    @staticmethod
    def _analyze_numeric_question(answers: List[Answer]) -> Dict[str, Any]:
        """Analyze numeric questions"""
        numeric_values = []
        for answer in answers:
            try:
                numeric_values.append(float(answer.value))
            except ValueError:
                continue  # Skip invalid numeric values
        
        if not numeric_values:
            return {
                'min_value': None,
                'max_value': None,
                'average': None,
                'median': None,
                'valid_responses': 0
            }
        
        numeric_values.sort()
        n = len(numeric_values)
        
        # Calculate median
        if n % 2 == 0:
            median = (numeric_values[n//2 - 1] + numeric_values[n//2]) / 2
        else:
            median = numeric_values[n//2]
        
        return {
            'min_value': min(numeric_values),
            'max_value': max(numeric_values),
            'average': round(sum(numeric_values) / n, 2),
            'median': round(median, 2),
            'valid_responses': n,
            'distribution': AnalyticsService._create_numeric_distribution(numeric_values)
        }
    
    @staticmethod
    def _analyze_text_question(answers: List[Answer]) -> Dict[str, Any]:
        """Analyze text-based questions"""
        text_values = [answer.value for answer in answers if answer.value.strip()]
        
        if not text_values:
            return {
                'avg_length': 0,
                'min_length': 0,
                'max_length': 0,
                'common_words': [],
                'response_count': 0
            }
        
        lengths = [len(text) for text in text_values]
        
        # Find common words (simple implementation)
        all_words = []
        for text in text_values:
            words = text.lower().split()
            # Filter out common stop words
            stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should'}
            filtered_words = [word.strip('.,!?;:"') for word in words if word.lower() not in stop_words and len(word) > 2]
            all_words.extend(filtered_words)
        
        common_words = Counter(all_words).most_common(10)
        
        return {
            'avg_length': round(sum(lengths) / len(lengths), 2),
            'min_length': min(lengths),
            'max_length': max(lengths),
            'common_words': [{'word': word, 'count': count} for word, count in common_words],
            'response_count': len(text_values)
        }
    
    @staticmethod
    def _create_numeric_distribution(values: List[float], bins: int = 5) -> List[Dict[str, Any]]:
        """Create distribution bins for numeric data"""
        if not values or len(values) < 2:
            return []
        
        min_val, max_val = min(values), max(values)
        if min_val == max_val:
            return [{'range': f'{min_val}', 'count': len(values)}]
        
        bin_width = (max_val - min_val) / bins
        distribution = []
        
        for i in range(bins):
            bin_start = min_val + (i * bin_width)
            bin_end = bin_start + bin_width
            
            # Count values in this bin
            if i == bins - 1:  # Last bin includes max value
                count = sum(1 for v in values if bin_start <= v <= bin_end)
            else:
                count = sum(1 for v in values if bin_start <= v < bin_end)
            
            distribution.append({
                'range': f'{bin_start:.1f} - {bin_end:.1f}',
                'count': count
            })
        
        return distribution
    
    @staticmethod
    def export_form_responses(form_id: int, user_id: int, user_role: str, format_type: str = 'csv') -> Optional[str]:
        """Export form responses in various formats"""
        try:
            with get_db_session() as session:
                # Check form access
                form = session.query(Form).filter(Form.id == form_id).first()
                if not form or (user_role == "EDITOR" and form.created_by != user_id):
                    return None
                
                # Get submissions with answers
                submissions = session.query(Submission).filter(
                    Submission.form_id == form_id
                ).order_by(desc(Submission.submitted_at)).all()
                
                if not submissions:
                    return ""
                
                # Get questions for column headers
                questions = session.query(Question).join(
                    Submission, Question.form_version_id == Submission.form_version_id
                ).filter(Submission.form_id == form_id).distinct().order_by(Question.order_index).all()
                
                if format_type.lower() == 'csv':
                    return AnalyticsService._export_to_csv(submissions, questions, session)
                elif format_type.lower() == 'json':
                    return AnalyticsService._export_to_json(submissions, questions, session)
                else:
                    return None
                
        except Exception as e:
            logger.error(f"Error exporting form responses for {form_id}: {e}")
            return None
    
    @staticmethod
    def _export_to_csv(submissions: List[Submission], questions: List[Question], session: Session) -> str:
        """Export submissions to CSV format"""
        import csv
        from io import StringIO
        
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        headers = ['Submission ID', 'Submitted At', 'Submitted By']
        headers.extend([q.label for q in questions])
        writer.writerow(headers)
        
        # Write data rows
        for submission in submissions:
            row = [
                submission.id,
                submission.submitted_at.strftime('%Y-%m-%d %H:%M:%S'),
                submission.user_id or 'Anonymous'
            ]
            
            # Get answers for this submission
            answers = session.query(Answer).filter(
                Answer.submission_id == submission.id
            ).all()
            answer_dict = {answer.question_id: answer.value for answer in answers}
            
            # Add answers in question order
            for question in questions:
                value = answer_dict.get(question.id, '')
                # Handle checkbox values
                if question.field_type == 'checkbox' and value.startswith('['):
                    try:
                        parsed_value = json.loads(value)
                        value = ', '.join(parsed_value)
                    except:
                        pass
                row.append(value)
            
            writer.writerow(row)
        
        return output.getvalue()
    
    @staticmethod
    def _export_to_json(submissions: List[Submission], questions: List[Question], session: Session) -> str:
        """Export submissions to JSON format"""
        export_data = []
        
        for submission in submissions:
            # Get answers for this submission
            answers = session.query(Answer).filter(
                Answer.submission_id == submission.id
            ).all()
            answer_dict = {answer.question_id: answer.value for answer in answers}
            
            submission_data = {
                'submission_id': submission.id,
                'submitted_at': submission.submitted_at.isoformat(),
                'user_id': submission.user_id,
                'answers': {}
            }
            
            # Add answers with question labels
            for question in questions:
                value = answer_dict.get(question.id, None)
                # Handle checkbox values
                if value and question.field_type == 'checkbox' and value.startswith('['):
                    try:
                        value = json.loads(value)
                    except:
                        pass
                submission_data['answers'][question.label] = value
            
            export_data.append(submission_data)
        
        return json.dumps(export_data, indent=2)
    
    @staticmethod
    def get_tenant_dashboard_stats(tenant_id: int, user_id: int, user_role: str) -> Dict[str, Any]:
        """Get dashboard statistics for a tenant"""
        try:
            with get_db_session() as session:
                # Apply role-based filtering
                forms_query = session.query(Form).filter(Form.tenant_id == tenant_id)
                if user_role == "EDITOR":
                    forms_query = forms_query.filter(Form.created_by == user_id)
                
                forms = forms_query.all()
                form_ids = [f.id for f in forms]
                
                if not form_ids:
                    return {
                        'total_forms': 0,
                        'total_submissions': 0,
                        'active_forms': 0,
                        'recent_activity': []
                    }
                
                # Get statistics
                total_forms = len(forms)
                active_forms = sum(1 for f in forms if f.status == 'published')
                
                total_submissions = session.query(Submission).filter(
                    Submission.form_id.in_(form_ids)
                ).count()
                
                # Get recent activity (last 10 submissions)
                recent_submissions = session.query(Submission).filter(
                    Submission.form_id.in_(form_ids)
                ).order_by(desc(Submission.submitted_at)).limit(10).all()
                
                recent_activity = []
                for sub in recent_submissions:
                    form = next((f for f in forms if f.id == sub.form_id), None)
                    recent_activity.append({
                        'form_title': form.title if form else 'Unknown Form',
                        'submitted_at': sub.submitted_at,
                        'submitter': 'Anonymous' if sub.user_id is None else 'Registered User'
                    })
                
                return {
                    'total_forms': total_forms,
                    'total_submissions': total_submissions,
                    'active_forms': active_forms,
                    'recent_activity': recent_activity,
                    'forms_by_status': {
                        'draft': sum(1 for f in forms if f.status == 'draft'),
                        'published': sum(1 for f in forms if f.status == 'published'),
                        'closed': sum(1 for f in forms if f.status == 'closed')
                    }
                }
                
        except Exception as e:
            logger.error(f"Error getting tenant dashboard stats: {e}")
            return {
                'total_forms': 0,
                'total_submissions': 0,
                'active_forms': 0,
                'recent_activity': []
            }
    
    @staticmethod
    def get_form_analytics(form_id: int, user_id: int, user_role: str) -> Dict[str, Any]:
        """Get analytics for a specific form"""
        try:
            with get_db_session() as session:
                # Get form details
                form = session.query(Form).filter(Form.id == form_id).first()
                if not form:
                    return {'error': 'Form not found'}
                
                # Check permissions
                if not AnalyticsService._check_form_access(session, form, user_id, user_role):
                    return {'error': 'Access denied'}
                
                # Get submission count
                submission_count = session.query(Submission).filter(
                    Submission.form_id == form_id
                ).count()
                
                # Get response rate (if applicable)
                total_answers = session.query(Answer).join(Submission).filter(
                    Submission.form_id == form_id
                ).count()
                
                return {
                    'form_title': form.title,
                    'submission_count': submission_count,
                    'total_answers': total_answers,
                    'status': form.status
                }
                
        except Exception as e:
            logger.error(f"Error getting form analytics for form {form_id}: {e}")
            return {'error': 'Failed to get form analytics'}
    
    @staticmethod
    def get_global_analytics(user_id: int, user_role: str) -> Dict[str, Any]:
        """Get global analytics across all forms"""
        try:
            with get_db_session() as session:
                # For now, return basic global stats
                total_forms = session.query(Form).count()
                total_submissions = session.query(Submission).count()
                total_users = session.query(Form).count()  # Simplified
                
                return {
                    'total_forms': total_forms,
                    'total_submissions': total_submissions,
                    'total_users': total_users
                }
                
        except Exception as e:
            logger.error(f"Error getting global analytics: {e}")
            return {
                'total_forms': 0,
                'total_submissions': 0,
                'total_users': 0
            }
    
    @staticmethod
    def _check_form_access(session, form: Form, user_id: int, user_role: str) -> bool:
        """Check if user has access to view form analytics"""
        if user_role in ['ADMIN', 'OWNER']:
            return True
        
        # For other roles, check if user created the form
        return form.created_by == user_id


# Legacy helper functions for compatibility with existing tests
def summary_metrics(forms: Dict[str, Any], submissions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compute simple summary metrics for a single form.
    - total submissions
    - unique logged-in users
    - guest submissions (guest_token present)
    - is_open (based on form submission window)
    """
    total = len(submissions)
    users = set(s["user_id"] for s in submissions if s.get("user_id"))
    guest = sum(1 for s in submissions if s.get("guest_token"))
    # form times may be None — treat as open
    now = None
    is_open = True
    ss = forms.get("submission_start")
    se = forms.get("submission_end")
    if ss and se:
        is_open = ss <= se
    return {
        "total_submissions": total,
        "unique_users": len(users),
        "guest_submissions": guest,
        "is_open": is_open,
    }


def choice_stats(question: Dict[str, Any], answers: List[Dict[str, Any]]) -> Dict[str, int]:
    """Count selections for a choice-style question. Answers are expected as raw values.
    For checkbox (multiple) answers, values may be stored as comma-separated strings.
    """
    counter = Counter()
    for a in answers:
        v = a.get("value")
        if v is None:
            continue
        if isinstance(v, str) and "," in v:
            parts = [p.strip() for p in v.split(",") if p.strip()]
            counter.update(parts)
        else:
            counter.update([v])
    return dict(counter)


def numeric_stats(answers: List[Dict[str, Any]]) -> Dict[str, Any]:
    nums = []
    for a in answers:
        v = a.get("value")
        try:
            n = float(v)
            nums.append(n)
        except Exception:
            continue
    if not nums:
        return {"count": 0, "min": None, "max": None, "avg": None}
    return {"count": len(nums), "min": min(nums), "max": max(nums), "avg": sum(nums) / len(nums)}


def text_table(answers: List[Dict[str, Any]], limit: int = 10) -> List[str]:
    # return most recent text answers (value field)
    vals = [a.get("value", "") for a in answers if a.get("value")]
    return vals[-limit:]
