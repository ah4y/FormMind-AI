"""
SQLAlchemy models for FormMind-AI
Matches the database schema defined in migrations/init_db.sql
"""
from sqlalchemy import (
    Column,
    Integer,
    Text,
    Boolean,
    ForeignKey,
    DateTime,
    Numeric,
    UniqueConstraint,
    Index,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .db import Base


class Tenant(Base):
    """Organizations using FormMind"""
    __tablename__ = "tenants"
    
    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    users = relationship("User", back_populates="tenant")
    forms = relationship("Form", back_populates="tenant")
    templates = relationship("Template", back_populates="tenant")


class User(Base):
    """Users belong to a tenant and have roles: OWNER, ADMIN, EDITOR"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"))
    email = Column(Text, nullable=False)
    name = Column(Text)
    password_hash = Column(Text)
    role = Column(Text, nullable=False)  # OWNER, ADMIN, EDITOR
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login_at = Column(DateTime(timezone=True))

    # Relationships
    tenant = relationship("Tenant", back_populates="users")
    created_forms = relationship("Form", foreign_keys="Form.created_by")
    created_templates = relationship("Template", foreign_keys="Template.created_by")

    # Constraints
    __table_args__ = (
        UniqueConstraint('tenant_id', 'email', name='unique_tenant_email'),
        Index('idx_user_tenant_email', 'tenant_id', 'email'),
    )


class Form(Base):
    """Top-level form entity with versioning support"""
    __tablename__ = "forms"
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"))
    title = Column(Text, nullable=False)
    description = Column(Text)
    status = Column(Text, nullable=False, default="draft")  # draft, published, unpublished
    access_type = Column(Text, nullable=False, default="public")  # public, authenticated
    single_submission = Column(Boolean, default=False)
    submission_start = Column(DateTime(timezone=True))
    submission_end = Column(DateTime(timezone=True))
    public_token = Column(Text)  # For public URLs
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    tenant = relationship("Tenant", back_populates="forms")
    creator = relationship("User", foreign_keys=[created_by], overlaps="created_forms")
    versions = relationship("FormVersion", back_populates="form", cascade="all, delete-orphan")
    submissions = relationship("Submission", back_populates="form")

    # Indexes
    __table_args__ = (
        Index('idx_form_tenant_status', 'tenant_id', 'status'),
        Index('idx_form_public_token', 'public_token'),
    )


class FormVersion(Base):
    """Immutable snapshots of form structure for versioning"""
    __tablename__ = "form_versions"
    
    id = Column(Integer, primary_key=True)
    form_id = Column(Integer, ForeignKey("forms.id", ondelete="CASCADE"))
    version_number = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)

    # Relationships
    form = relationship("Form", back_populates="versions")
    questions = relationship("Question", back_populates="form_version", cascade="all, delete-orphan")

    # Constraints
    __table_args__ = (
        UniqueConstraint('form_id', 'version_number', name='unique_form_version'),
        Index('idx_form_version_active', 'form_id', 'is_active'),
    )


class Question(Base):
    """Questions/fields in a specific form version"""
    __tablename__ = "questions"
    
    id = Column(Integer, primary_key=True)
    form_version_id = Column(Integer, ForeignKey("form_versions.id", ondelete="CASCADE"))
    label = Column(Text, nullable=False)
    placeholder = Column(Text)
    help_text = Column(Text)
    field_type = Column(Text)  # short_text, long_text, radio, checkbox, dropdown, integer, decimal, date, time, boolean
    required = Column(Boolean, default=False)
    default_value = Column(Text)
    order_index = Column(Integer, default=0)
    validation_min = Column(Numeric)
    validation_max = Column(Numeric)
    validation_regex = Column(Text)

    # Relationships
    form_version = relationship("FormVersion", back_populates="questions")
    options = relationship("QuestionOption", back_populates="question", cascade="all, delete-orphan")
    answers = relationship("Answer", back_populates="question")

    # Indexes
    __table_args__ = (
        Index('idx_question_form_version_order', 'form_version_id', 'order_index'),
    )


class QuestionOption(Base):
    """Options for radio/checkbox/dropdown questions"""
    __tablename__ = "question_options"
    
    id = Column(Integer, primary_key=True)
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"))
    label = Column(Text)
    value = Column(Text)
    order_index = Column(Integer, default=0)

    # Relationships
    question = relationship("Question", back_populates="options")

    # Indexes
    __table_args__ = (
        Index('idx_option_question_order', 'question_id', 'order_index'),
    )


class Submission(Base):
    """One completed submission of a form"""
    __tablename__ = "submissions"
    
    id = Column(Integer, primary_key=True)
    form_id = Column(Integer, ForeignKey("forms.id", ondelete="CASCADE"))
    form_version_id = Column(Integer, ForeignKey("form_versions.id", ondelete="CASCADE"))
    user_id = Column(Integer, ForeignKey("users.id"))  # NULL for guest submissions
    guest_token = Column(Text)  # For tracking guest submissions
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())
    completion_time_ms = Column(Integer)  # Time taken to complete form

    # Relationships
    form = relationship("Form", back_populates="submissions")
    form_version = relationship("FormVersion")
    user = relationship("User")
    answers = relationship("Answer", back_populates="submission", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index('idx_submission_form_user', 'form_id', 'user_id'),
        Index('idx_submission_form_date', 'form_id', 'submitted_at'),
    )


class Answer(Base):
    """Individual answers for a submission"""
    __tablename__ = "answers"
    
    id = Column(Integer, primary_key=True)
    submission_id = Column(Integer, ForeignKey("submissions.id", ondelete="CASCADE"))
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"))
    value = Column(Text)  # Store all values as text, convert based on field_type

    # Relationships
    submission = relationship("Submission", back_populates="answers")
    question = relationship("Question", back_populates="answers")

    # Constraints
    __table_args__ = (
        UniqueConstraint('submission_id', 'question_id', name='unique_submission_question'),
        Index('idx_answer_submission', 'submission_id'),
    )


class Template(Base):
    """Reusable form templates"""
    __tablename__ = "templates"
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"))
    name = Column(Text, nullable=False)
    category = Column(Text)  # survey, feedback, registration, etc.
    visibility = Column(Text, default="private")  # private, tenant, public
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    tenant = relationship("Tenant", back_populates="templates")
    creator = relationship("User", foreign_keys=[created_by], overlaps="created_templates")

    # Indexes
    __table_args__ = (
        Index('idx_template_tenant_visibility', 'tenant_id', 'visibility'),
    )
