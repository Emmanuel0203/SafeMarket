"""
Enhanced SQLAlchemy Models - SafeMarket
Compatible with improved PostgreSQL schema
"""

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text,
    ForeignKey, UniqueConstraint, CheckConstraint, Index, Enum,
    DECIMAL, CHAR, JSON, TIMESTAMP, func
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid
import enum

Base = declarative_base()


# ==========================================
# ENUMS
# ==========================================

class UserRoleEnum(str, enum.Enum):
    ADMIN = "ADMIN"
    ANALYST = "ANALYST"
    REVIEWER = "REVIEWER"
    VIEWER = "VIEWER"


class UserStatusEnum(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"


class TransactionTypeEnum(str, enum.Enum):
    PURCHASE = "PURCHASE"
    TRANSFER = "TRANSFER"
    WITHDRAWAL = "WITHDRAWAL"
    DEPOSIT = "DEPOSIT"


class TransactionStatusEnum(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    DECLINED = "DECLINED"
    REVIEW = "REVIEW"


class RiskLevelEnum(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class DeviceTypeEnum(str, enum.Enum):
    DESKTOP = "DESKTOP"
    MOBILE = "MOBILE"
    TABLET = "TABLET"


class SessionStatusEnum(str, enum.Enum):
    ACTIVE = "ACTIVE"
    TERMINATED = "TERMINATED"
    SUSPICIOUS = "SUSPICIOUS"


class SourceTypeEnum(str, enum.Enum):
    CARD = "CARD"
    BANK = "BANK"
    WALLET = "WALLET"


class AuthMethodEnum(str, enum.Enum):
    PASSWORD = "PASSWORD"
    MFA = "MFA"
    SSO = "SSO"
    BIOMETRIC = "BIOMETRIC"


class AlertStatusEnum(str, enum.Enum):
    OPEN = "OPEN"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"
    FALSE_POSITIVE = "FALSE_POSITIVE"
    CLOSED = "CLOSED"


class CaseStatusEnum(str, enum.Enum):
    OPEN = "OPEN"
    INVESTIGATING = "INVESTIGATING"
    CONFIRMED = "CONFIRMED"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


# ==========================================
# MODELS
# ==========================================

class Company(Base):
    """Multi-tenant company information"""
    __tablename__ = "companies"

    company_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), unique=True, nullable=False)
    industry = Column(String(100))
    country_code = Column(CHAR(2))
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)
    extra_metadata = Column("metadata", JSONB)

    # Relationships
    users = relationship("User", back_populates="company")

    __table_args__ = (
        Index('idx_companies_active', is_active),
        Index('idx_companies_name', name),
    )


class User(Base):
    """Enhanced user model with authentication and authorization"""
    __tablename__ = "users"

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    phone = Column(String(20))
    document_id = Column(String(50))
    country_code = Column(CHAR(2))
    
    # Authorization
    role = Column(String(50), default=UserRoleEnum.VIEWER)
    department = Column(String(100))
    company_id = Column(UUID(as_uuid=True), ForeignKey('companies.company_id', ondelete='SET NULL'))
    
    # Status
    status = Column(String(50), default=UserStatusEnum.ACTIVE)
    is_email_verified = Column(Boolean, default=False)
    is_phone_verified = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(TIMESTAMP)
    
    # Metadata
    extra_metadata = Column("metadata", JSONB)

    # Relationships
    company = relationship("Company", back_populates="users")
    devices = relationship("Device", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")
    alerts_assigned = relationship("Alert", back_populates="assigned_user")
    cases_investigating = relationship("Case", back_populates="investigator_user")
    feedback_given = relationship("FraudFeedback", back_populates="reviewer")
    
    __table_args__ = (
        CheckConstraint("role IN ('ADMIN', 'ANALYST', 'REVIEWER', 'VIEWER')"),
        CheckConstraint("status IN ('ACTIVE', 'INACTIVE', 'SUSPENDED')"),
        Index('idx_users_email', email),
        Index('idx_users_company', company_id),
        Index('idx_users_status', status),
        Index('idx_users_role', role),
        Index('idx_users_created', created_at.desc()),
    )


class Device(Base):
    """Device fingerprinting and tracking"""
    __tablename__ = "devices"

    device_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    
    # Fingerprinting
    device_fingerprint = Column(String(255), unique=True)
    device_name = Column(String(100))
    device_type = Column(String(50))
    os = Column(String(50))
    os_version = Column(String(50))
    browser = Column(String(50))
    browser_version = Column(String(50))
    
    # Network
    ip = Column(INET)
    country = Column(String(100))
    city = Column(String(100))
    latitude = Column(DECIMAL(10, 8))
    longitude = Column(DECIMAL(11, 8))
    
    # Risk
    is_trusted = Column(Boolean, default=False)
    trust_score = Column(DECIMAL(3, 2), default=0.50)
    last_used_at = Column(TIMESTAMP)
    risk_level = Column(String(50), default=RiskLevelEnum.MEDIUM)
    
    # Temporal
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    extra_metadata = Column("metadata", JSONB)

    # Relationships
    user = relationship("User", back_populates="devices")
    sessions = relationship("Session", back_populates="device")
    transactions = relationship("Transaction", back_populates="device")

    __table_args__ = (
        CheckConstraint("risk_level IN ('LOW', 'MEDIUM', 'HIGH')"),
        Index('idx_devices_user', user_id),
        Index('idx_devices_fp', device_fingerprint),
        Index('idx_devices_trust', is_trusted, user_id),
        Index('idx_devices_risk', risk_level),
    )


class Session(Base):
    """User session tracking"""
    __tablename__ = "sessions"

    session_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    device_id = Column(UUID(as_uuid=True), ForeignKey('devices.device_id', ondelete='CASCADE'), nullable=False)
    
    # Temporal
    login_time = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    logout_time = Column(TIMESTAMP)
    duration_seconds = Column(Integer)
    
    # Context
    ip_address = Column(INET)
    user_agent = Column(Text)
    authentication_method = Column(String(50))
    mfa_used = Column(Boolean, default=False)
    anomaly_detected = Column(Boolean, default=False)
    
    # Risk
    risk_level = Column(String(50), default=RiskLevelEnum.MEDIUM)
    risk_score = Column(DECIMAL(3, 2))
    risk_factors = Column(ARRAY(String))
    
    # Status
    status = Column(String(50), default=SessionStatusEnum.ACTIVE)
    
    extra_metadata = Column("metadata", JSONB)

    # Relationships
    user = relationship("User", back_populates="sessions")
    device = relationship("Device", back_populates="sessions")
    transactions = relationship("Transaction", back_populates="session")

    __table_args__ = (
        CheckConstraint("risk_level IN ('LOW', 'MEDIUM', 'HIGH')"),
        CheckConstraint("status IN ('ACTIVE', 'TERMINATED', 'SUSPICIOUS')"),
        CheckConstraint("authentication_method IN ('PASSWORD', 'MFA', 'SSO', 'BIOMETRIC')"),
        Index('idx_sessions_user_time', user_id, login_time.desc()),
        Index('idx_sessions_device_time', device_id, login_time.desc()),
        Index('idx_sessions_status', status),
        Index('idx_sessions_risk', risk_level),
    )


class Transaction(Base):
    """Enhanced transaction model with fraud detection features"""
    __tablename__ = "transactions"

    transaction_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    device_id = Column(UUID(as_uuid=True), ForeignKey('devices.device_id', ondelete='CASCADE'), nullable=False)
    session_id = Column(UUID(as_uuid=True), ForeignKey('sessions.session_id', ondelete='SET NULL'))
    
    # Origin
    source_account = Column(String(50))
    source_type = Column(String(50))
    
    # Transaction
    amount = Column(DECIMAL(14, 2), nullable=False)
    currency = Column(CHAR(3), default='USD')
    
    # Destination
    destination_account = Column(String(50))
    destination_merchant = Column(String(255))
    merchant_category = Column(String(10))
    merchant_id = Column(String(50))
    merchant_risk_level = Column(String(50))
    
    # Details
    transaction_type = Column(String(50), nullable=False)
    description = Column(Text)
    reference_number = Column(String(100), unique=True)
    
    # Risk & Status
    status = Column(String(50), default=TransactionStatusEnum.PENDING)
    risk_level = Column(String(50), default=RiskLevelEnum.MEDIUM)
    risk_score = Column(DECIMAL(3, 2))
    is_fraud = Column(Boolean, default=False)
    fraud_type = Column(String(100))
    
    # Temporal
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)
    processed_at = Column(TIMESTAMP)
    
    extra_metadata = Column("metadata", JSONB)

    # Relationships
    user = relationship("User", back_populates="transactions")
    device = relationship("Device", back_populates="transactions")
    session = relationship("Session", back_populates="transactions")
    features = relationship("TransactionFeature", back_populates="transaction", cascade="all, delete-orphan")
    risk_scores = relationship("RiskScore", back_populates="transaction", cascade="all, delete-orphan")
    rule_matches = relationship("RuleMatch", back_populates="transaction", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="transaction", cascade="all, delete-orphan")
    cases = relationship("Case", back_populates="transaction", cascade="all, delete-orphan")
    feedback = relationship("FraudFeedback", back_populates="transaction", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("transaction_type IN ('PURCHASE', 'TRANSFER', 'WITHDRAWAL', 'DEPOSIT')"),
        CheckConstraint("status IN ('PENDING', 'APPROVED', 'DECLINED', 'REVIEW')"),
        CheckConstraint("source_type IN ('CARD', 'BANK', 'WALLET')"),
        CheckConstraint("amount > 0"),
        Index('idx_tx_user_time', user_id, created_at.desc()),
        Index('idx_tx_device_time', device_id, created_at.desc()),
        Index('idx_tx_status', status),
        Index('idx_tx_merchant', merchant_id),
        Index('idx_tx_fraud', is_fraud),
        Index('idx_tx_reference', reference_number),
        Index('idx_tx_risk', risk_level),
    )


class TransactionFeature(Base):
    """Feature store for ML"""
    __tablename__ = "transaction_features"

    feature_id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_id = Column(UUID(as_uuid=True), ForeignKey('transactions.transaction_id', ondelete='CASCADE'), nullable=False)
    
    feature_category = Column(String(50))
    feature_name = Column(String(100), nullable=False)
    feature_value = Column(DECIMAL)
    
    calculation_method = Column(String(50))
    confidence = Column(DECIMAL(3, 2))
    
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    # Relationships
    transaction = relationship("Transaction", back_populates="features")

    __table_args__ = (
        CheckConstraint("feature_category IN ('BEHAVIORAL', 'NETWORK', 'TRANSACTION', 'DEVICE')"),
        Index('idx_features_tx', transaction_id),
        Index('idx_features_category', feature_category),
    )


class RiskScore(Base):
    """ML-generated risk scores"""
    __tablename__ = "risk_scores"

    score_id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_id = Column(UUID(as_uuid=True), ForeignKey('transactions.transaction_id', ondelete='CASCADE'), nullable=False)
    
    # Model
    model_name = Column(String(100), nullable=False)
    model_version = Column(String(50))
    
    # Score
    overall_score = Column(DECIMAL(3, 2), nullable=False)
    fraud_probability = Column(DECIMAL(3, 2))
    anomaly_score = Column(DECIMAL(3, 2))
    
    # Components
    score_components = Column(JSONB)
    risk_factors = Column(ARRAY(String))
    
    # Decision
    decision = Column(String(50), nullable=False)
    confidence_level = Column(DECIMAL(3, 2))
    
    # Explainability
    explanation = Column(JSONB)
    
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    # Relationships
    transaction = relationship("Transaction", back_populates="risk_scores")

    __table_args__ = (
        CheckConstraint("decision IN ('APPROVE', 'DECLINE', 'MANUAL_REVIEW')"),
        CheckConstraint("overall_score >= 0 AND overall_score <= 1"),
        Index('idx_risk_scores_tx', transaction_id),
        Index('idx_risk_scores_decision', decision),
        Index('idx_risk_scores_model', model_name, created_at.desc()),
    )


class Rule(Base):
    """Fraud detection rules"""
    __tablename__ = "rules"

    rule_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rule_name = Column(String(255), nullable=False)
    description = Column(Text)
    risk_weight = Column(DECIMAL(3, 2))
    is_active = Column(Boolean, default=True)
    rule_type = Column(String(50))
    condition = Column(JSONB)
    action = Column(JSONB)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    matches = relationship("RuleMatch", back_populates="rule")

    __table_args__ = (
        Index('idx_rules_active', is_active),
        Index('idx_rules_name', rule_name),
    )


class RuleMatch(Base):
    """Rule matches on transactions"""
    __tablename__ = "rule_matches"

    match_id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_id = Column(UUID(as_uuid=True), ForeignKey('transactions.transaction_id', ondelete='CASCADE'), nullable=False)
    rule_id = Column(UUID(as_uuid=True), ForeignKey('rules.rule_id', ondelete='CASCADE'), nullable=False)
    
    # Context
    rule_name = Column(String(255), nullable=False)
    matched_field = Column(String(100))
    matched_value = Column(String(255))
    expected_value = Column(String(255))
    
    # Risk
    risk_contribution = Column(DECIMAL(3, 2))
    severity = Column(String(50))
    
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    # Relationships
    transaction = relationship("Transaction", back_populates="rule_matches")
    rule = relationship("Rule", back_populates="matches")

    __table_args__ = (
        CheckConstraint("severity IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')"),
        Index('idx_rule_matches_tx', transaction_id),
        Index('idx_rule_matches_rule', rule_id),
        Index('idx_rule_severity', severity),
    )


class Alert(Base):
    """Fraud alerts"""
    __tablename__ = "alerts"

    alert_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_id = Column(UUID(as_uuid=True), ForeignKey('transactions.transaction_id', ondelete='CASCADE'), nullable=False)
    
    alert_level = Column(String(50), nullable=False)
    status = Column(String(50), default='OPEN')
    
    assigned_to = Column(UUID(as_uuid=True), ForeignKey('users.user_id', ondelete='SET NULL'))
    
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    resolved_at = Column(TIMESTAMP)
    
    extra_metadata = Column("metadata", JSONB)

    # Relationships
    transaction = relationship("Transaction", back_populates="alerts")
    assigned_user = relationship("User", back_populates="alerts_assigned")
    cases = relationship("Case", back_populates="alert")

    __table_args__ = (
        CheckConstraint("alert_level IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')"),
        CheckConstraint("status IN ('OPEN', 'IN_REVIEW', 'RESOLVED', 'DISMISSED')"),
        Index('idx_alerts_tx', transaction_id),
        Index('idx_alerts_status', status),
        Index('idx_alerts_assigned', assigned_to),
        Index('idx_alerts_created', created_at.desc()),
    )


class Case(Base):
    """Fraud case management"""
    __tablename__ = "cases"

    case_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    alert_id = Column(UUID(as_uuid=True), ForeignKey('alerts.alert_id', ondelete='SET NULL'))
    transaction_id = Column(UUID(as_uuid=True), ForeignKey('transactions.transaction_id', ondelete='CASCADE'), nullable=False)
    
    # Investigation
    investigator = Column(UUID(as_uuid=True), ForeignKey('users.user_id', ondelete='SET NULL'))
    status = Column(String(50), default='OPEN')
    
    # Resolution
    resolution = Column(Text)
    resolution_notes = Column(Text)
    
    # Temporal
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    closed_at = Column(TIMESTAMP)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    extra_metadata = Column("metadata", JSONB)

    # Relationships
    alert = relationship("Alert", back_populates="cases")
    transaction = relationship("Transaction", back_populates="cases")
    investigator_user = relationship("User", back_populates="cases_investigating")

    __table_args__ = (
        CheckConstraint("status IN ('OPEN', 'IN_PROGRESS', 'ESCALATED', 'CLOSED')"),
        Index('idx_cases_tx', transaction_id),
        Index('idx_cases_investigator', investigator),
        Index('idx_cases_status', status),
    )


class FraudFeedback(Base):
    """Ground truth feedback for ML model improvement"""
    __tablename__ = "fraud_feedback"

    feedback_id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_id = Column(UUID(as_uuid=True), ForeignKey('transactions.transaction_id', ondelete='CASCADE'), nullable=False)
    
    # Ground truth
    is_fraud = Column(Boolean, nullable=False)
    fraud_type = Column(String(100))
    
    # Review
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey('users.user_id', ondelete='RESTRICT'), nullable=False)
    reviewed_at = Column(TIMESTAMP, default=datetime.utcnow)
    
    # Context
    notes = Column(Text)
    confidence = Column(DECIMAL(3, 2))
    
    # ML Feedback
    predicted_fraud = Column(Boolean)
    was_model_correct = Column(Boolean)
    
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    # Relationships
    transaction = relationship("Transaction", back_populates="feedback")
    reviewer = relationship("User", back_populates="feedback_given")

    __table_args__ = (
        CheckConstraint("confidence >= 0 AND confidence <= 1"),
        UniqueConstraint('transaction_id', 'reviewed_by', name='unique_feedback'),
        Index('idx_feedback_tx', transaction_id),
        Index('idx_feedback_fraud', is_fraud),
        Index('idx_feedback_accuracy', was_model_correct),
        Index('idx_feedback_reviewer', reviewed_by),
    )


class VelocityCheck(Base):
    """Velocity-based fraud detection"""
    __tablename__ = "velocity_checks"

    check_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    
    check_type = Column(String(50), nullable=False)
    
    current_value = Column(DECIMAL)
    threshold_value = Column(DECIMAL)
    exceeded = Column(Boolean)
    
    window_start = Column(TIMESTAMP)
    window_end = Column(TIMESTAMP)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    __table_args__ = (
        CheckConstraint("""check_type IN (
            'TXN_COUNT_1H', 'TXN_COUNT_24H', 
            'AMOUNT_1H', 'AMOUNT_24H', 
            'LOCATION_30M', 'IP_30M', 'CARD_MULT_MERCHANTS'
        )"""),
        Index('idx_velocity_user_type', user_id, check_type, created_at.desc()),
    )


class FeatureCache(Base):
    """ML feature cache for performance"""
    __tablename__ = "feature_cache"

    cache_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    
    feature_set = Column(JSONB, nullable=False)
    
    time_window = Column(String(20))
    window_start = Column(TIMESTAMP)
    window_end = Column(TIMESTAMP)
    
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    ttl = Column(TIMESTAMP)

    __table_args__ = (
        CheckConstraint("time_window IN ('1H', '24H', '7D', '30D')"),
        UniqueConstraint('user_id', 'time_window', name='unique_cache'),
        Index('idx_cache_user', user_id),
        Index('idx_cache_ttl', ttl),
    )


class AuditLog(Base):
    """Audit trail for compliance"""
    __tablename__ = "audit_logs"

    log_id = Column(Integer, primary_key=True, autoincrement=True)
    
    entity_type = Column(String(100), nullable=False)
    entity_id = Column(String(255))
    action = Column(String(50), nullable=False)
    
    old_value = Column(JSONB)
    new_value = Column(JSONB)
    
    actor = Column(UUID(as_uuid=True), ForeignKey('users.user_id', ondelete='SET NULL'))
    
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    __table_args__ = (
        CheckConstraint("action IN ('CREATE', 'READ', 'UPDATE', 'DELETE', 'APPROVE', 'REJECT')"),
        Index('idx_audit_entity', entity_type, entity_id),
        Index('idx_audit_actor', actor),
        Index('idx_audit_action', action),
        Index('idx_audit_created', created_at.desc()),
    )
