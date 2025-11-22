"""SQLAlchemy models for FormMind.
Keep models readable and intentionally minimal for the competition.
"""
from sqlalchemy import (
    Column,
    Integer,
    Text,
    Boolean,
    ForeignKey,
    DateTime,
    Numeric,
)
from sqlalchemy.sql import func
from .db import Base
from sqlalchemy.orm import relationship


class Tenant(Base):
    __tablename__ = "tenants"
    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"))
    email = Column(Text, nullable=False)
    name = Column(Text)
    password_hash = Column(Text)
    role = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login_at = Column(DateTime(timezone=True))

    tenant = relationship("Tenant")


class Form(Base):
    __tablename__ = "forms"
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"))
    title = Column(Text, nullable=False)
    description = Column(Text)
    status = Column(Text, nullable=False, default="draft")
    access_type = Column(Text, nullable=False, default="public")
    single_submission = Column(Boolean, default=False)
    submission_start = Column(DateTime(timezone=True))
    submission_end = Column(DateTime(timezone=True))
    public_token = Column(Text)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    tenant = relationship("Tenant")


class FormVersion(Base):
    __tablename__ = "form_versions"
    id = Column(Integer, primary_key=True)
    form_id = Column(Integer, ForeignKey("forms.id"))
    version_number = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)

    form = relationship("Form")


class Question(Base):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True)
    form_version_id = Column(Integer, ForeignKey("form_versions.id"))
    label = Column(Text, nullable=False)
    placeholder = Column(Text)
    help_text = Column(Text)
    field_type = Column(Text)
    required = Column(Boolean, default=False)
    default_value = Column(Text)
    order_index = Column(Integer, default=0)
    validation_min = Column(Numeric)
    validation_max = Column(Numeric)
    validation_regex = Column(Text)

    form_version = relationship("FormVersion")


class QuestionOption(Base):
    __tablename__ = "question_options"
    id = Column(Integer, primary_key=True)
    question_id = Column(Integer, ForeignKey("questions.id"))
    label = Column(Text)
    value = Column(Text)
    order_index = Column(Integer, default=0)

    question = relationship("Question")


class Submission(Base):
    __tablename__ = "submissions"
    id = Column(Integer, primary_key=True)
    form_id = Column(Integer, ForeignKey("forms.id"))
    form_version_id = Column(Integer, ForeignKey("form_versions.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    guest_token = Column(Text)
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())
    completion_time_ms = Column(Integer)

    form = relationship("Form")


class Answer(Base):
    __tablename__ = "answers"
    id = Column(Integer, primary_key=True)
    submission_id = Column(Integer, ForeignKey("submissions.id"))
    question_id = Column(Integer, ForeignKey("questions.id"))
    value = Column(Text)

    submission = relationship("Submission")


class Template(Base):
    __tablename__ = "templates"
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"))
    name = Column(Text, nullable=False)
    category = Column(Text)
    visibility = Column(Text, default="private")
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
