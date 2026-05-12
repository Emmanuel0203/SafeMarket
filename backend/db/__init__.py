"""Database configuration and models - UNIFIED
This module uses enhanced versions as primary"""

# ===== MODELS (Import first to define Base) =====
from db.models_enhanced import (
    Base,
    User, Company, Device, Session as DBSession,
    Transaction, TransactionFeature, RiskScore,
    Rule, RuleMatch, Alert, Case,
    FraudFeedback, VelocityCheck, FeatureCache,
    AuditLog,
    # Enums
    UserRoleEnum, UserStatusEnum, TransactionTypeEnum, TransactionStatusEnum,
    AlertStatusEnum, CaseStatusEnum
)

# ===== DATABASE (Uses Base from models) =====
from db.database_enhanced import (
    engine,
    SessionLocal,
    get_db,
    init_db,
    test_connection
)

__all__ = [
    # Database
    "engine",
    "SessionLocal",
    "Base",
    "get_db",
    "init_db",
    "test_connection",
    # Models
    "User", "Company", "Device", "DBSession",
    "Transaction", "TransactionFeature", "RiskScore",
    "Rule", "RuleMatch", "Alert", "Case",
    "FraudFeedback", "VelocityCheck", "FeatureCache",
    "AuditLog",
    # Enums
    "UserRoleEnum", "UserStatusEnum", "TransactionTypeEnum", "TransactionStatusEnum",
    "AlertStatusEnum", "CaseStatusEnum"
]

