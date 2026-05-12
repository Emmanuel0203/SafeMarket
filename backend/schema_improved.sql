-- ==========================================
-- SafeMarket - Enhanced Database Schema
-- PostgreSQL 13+
-- ==========================================
-- Instrucciones:
-- 1. Copiar todo este script
-- 2. Conectar a PostgreSQL: psql -U postgres -h localhost
-- 3. Crear BD: CREATE DATABASE safemarket;
-- 4. Ejecutar: \i schema_improved.sql
-- ==========================================

-- =========================
-- EXTENSIONS
-- =========================
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =========================
-- COMPANIES (Multi-tenancy)
-- =========================
CREATE TABLE companies (
    company_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL UNIQUE,
    industry TEXT,
    country_code CHAR(2),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB,
    
    CONSTRAINT company_name_length CHECK (char_length(name) > 0)
);

CREATE INDEX idx_companies_active ON companies(is_active);
CREATE INDEX idx_companies_name ON companies(name);


-- =========================
-- USERS
-- =========================
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Identificación
    email TEXT UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    phone TEXT,
    document_id TEXT,
    country_code CHAR(2),
    
    -- Autorización
    role TEXT DEFAULT 'VIEWER',
    department TEXT,
    company_id UUID REFERENCES companies(company_id) ON DELETE SET NULL,
    
    -- Estado
    status TEXT DEFAULT 'ACTIVE',
    is_email_verified BOOLEAN DEFAULT FALSE,
    is_phone_verified BOOLEAN DEFAULT FALSE,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP,
    
    -- Metadata
    metadata JSONB,
    
    CONSTRAINT valid_role CHECK (role IN ('ADMIN', 'ANALYST', 'REVIEWER', 'VIEWER')),
    CONSTRAINT valid_status CHECK (status IN ('ACTIVE', 'INACTIVE', 'SUSPENDED')),
    CONSTRAINT email_format CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$')
);

CREATE UNIQUE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_company ON users(company_id);
CREATE INDEX idx_users_status ON users(status);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_created ON users(created_at DESC);


-- =========================
-- DEVICES (Device Fingerprinting)
-- =========================
CREATE TABLE devices (
    device_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    
    -- Fingerprinting
    device_fingerprint TEXT UNIQUE,
    device_name TEXT,
    device_type TEXT,
    os TEXT,
    os_version TEXT,
    browser TEXT,
    browser_version TEXT,
    
    -- Network
    ip INET,
    country TEXT,
    city TEXT,
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    
    -- Riesgo
    is_trusted BOOLEAN DEFAULT FALSE,
    trust_score NUMERIC(3, 2) DEFAULT 0.50,
    last_used_at TIMESTAMP,
    risk_level TEXT DEFAULT 'MEDIUM',
    
    -- Temporal
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    metadata JSONB,
    
    CONSTRAINT risk_level_check CHECK (risk_level IN ('LOW', 'MEDIUM', 'HIGH')),
    CONSTRAINT trust_score_range CHECK (trust_score >= 0.00 AND trust_score <= 1.00)
);

CREATE INDEX idx_devices_user ON devices(user_id);
CREATE INDEX idx_devices_fp ON devices(device_fingerprint);
CREATE INDEX idx_devices_trust ON devices(is_trusted, user_id);
CREATE INDEX idx_devices_risk ON devices(risk_level);


-- =========================
-- SESSIONS
-- =========================
CREATE TABLE sessions (
    session_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    device_id UUID NOT NULL REFERENCES devices(device_id) ON DELETE CASCADE,
    
    -- Temporal
    login_time TIMESTAMP NOT NULL DEFAULT NOW(),
    logout_time TIMESTAMP,
    duration_seconds INT,
    
    -- Contexto
    ip_address INET,
    user_agent TEXT,
    authentication_method TEXT,
    mfa_used BOOLEAN DEFAULT FALSE,
    anomaly_detected BOOLEAN DEFAULT FALSE,
    
    -- Riesgo
    risk_level TEXT DEFAULT 'MEDIUM',
    risk_score NUMERIC(3, 2),
    risk_factors TEXT[],
    
    -- Estado
    status TEXT DEFAULT 'ACTIVE',
    
    metadata JSONB,
    
    CONSTRAINT risk_level_check CHECK (risk_level IN ('LOW', 'MEDIUM', 'HIGH')),
    CONSTRAINT status_check CHECK (status IN ('ACTIVE', 'TERMINATED', 'SUSPICIOUS')),
    CONSTRAINT valid_auth CHECK (authentication_method IN ('PASSWORD', 'MFA', 'SSO', 'BIOMETRIC'))
);

CREATE INDEX idx_sessions_user_time ON sessions(user_id, login_time DESC);
CREATE INDEX idx_sessions_device_time ON sessions(device_id, login_time DESC);
CREATE INDEX idx_sessions_status ON sessions(status);
CREATE INDEX idx_sessions_risk ON sessions(risk_level);


-- =========================
-- TRANSACTIONS
-- =========================
CREATE TABLE transactions (
    transaction_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    device_id UUID NOT NULL REFERENCES devices(device_id) ON DELETE CASCADE,
    session_id UUID REFERENCES sessions(session_id) ON DELETE SET NULL,
    
    -- Origen
    source_account TEXT,
    source_type TEXT,
    
    -- Transacción
    amount NUMERIC(14, 2) NOT NULL,
    currency CHAR(3) DEFAULT 'USD',
    
    -- Destino
    destination_account TEXT,
    destination_merchant TEXT,
    merchant_category TEXT,
    merchant_id TEXT,
    merchant_risk_level TEXT,
    
    -- Detalles
    transaction_type TEXT NOT NULL,
    description TEXT,
    reference_number TEXT UNIQUE,
    
    -- Riesgo y Estado
    status TEXT DEFAULT 'PENDING',
    risk_level TEXT DEFAULT 'MEDIUM',
    risk_score NUMERIC(3, 2),
    is_fraud BOOLEAN DEFAULT FALSE,
    fraud_type TEXT,
    
    -- Temporal
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    processed_at TIMESTAMP,
    
    metadata JSONB,
    
    CONSTRAINT valid_type CHECK (transaction_type IN ('PURCHASE', 'TRANSFER', 'WITHDRAWAL', 'DEPOSIT')),
    CONSTRAINT valid_status CHECK (status IN ('PENDING', 'APPROVED', 'DECLINED', 'REVIEW')),
    CONSTRAINT valid_source CHECK (source_type IN ('CARD', 'BANK', 'WALLET')),
    CONSTRAINT amount_positive CHECK (amount > 0)
);

CREATE INDEX idx_tx_user_time ON transactions(user_id, created_at DESC);
CREATE INDEX idx_tx_device_time ON transactions(device_id, created_at DESC);
CREATE INDEX idx_tx_status ON transactions(status);
CREATE INDEX idx_tx_merchant ON transactions(merchant_id);
CREATE INDEX idx_tx_fraud ON transactions(is_fraud) WHERE is_fraud = TRUE;
CREATE INDEX idx_tx_reference ON transactions(reference_number);
CREATE INDEX idx_tx_risk ON transactions(risk_level);


-- =========================
-- TRANSACTION FEATURES (Feature Store)
-- =========================
CREATE TABLE transaction_features (
    feature_id BIGSERIAL PRIMARY KEY,
    transaction_id UUID NOT NULL REFERENCES transactions(transaction_id) ON DELETE CASCADE,
    
    feature_category TEXT,
    feature_name TEXT NOT NULL,
    feature_value NUMERIC,
    
    calculation_method TEXT,
    confidence NUMERIC(3, 2),
    
    created_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT valid_category CHECK (feature_category IN ('BEHAVIORAL', 'NETWORK', 'TRANSACTION', 'DEVICE'))
);

CREATE INDEX idx_features_tx ON transaction_features(transaction_id);
CREATE INDEX idx_features_category ON transaction_features(feature_category);


-- =========================
-- RISK SCORES (ML Output)
-- =========================
CREATE TABLE risk_scores (
    score_id BIGSERIAL PRIMARY KEY,
    transaction_id UUID NOT NULL REFERENCES transactions(transaction_id) ON DELETE CASCADE,
    
    -- Modelo
    model_name TEXT NOT NULL,
    model_version TEXT,
    
    -- Puntuación
    overall_score NUMERIC(3, 2) NOT NULL,
    fraud_probability NUMERIC(3, 2),
    anomaly_score NUMERIC(3, 2),
    
    -- Componentes
    score_components JSONB,
    risk_factors TEXT[],
    
    -- Decisión
    decision TEXT NOT NULL,
    confidence_level NUMERIC(3, 2),
    
    -- Explicabilidad
    explanation JSONB,
    
    created_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT valid_decision CHECK (decision IN ('APPROVE', 'DECLINE', 'MANUAL_REVIEW')),
    CONSTRAINT score_range CHECK (overall_score >= 0 AND overall_score <= 1)
);

CREATE INDEX idx_risk_scores_tx ON risk_scores(transaction_id);
CREATE INDEX idx_risk_scores_decision ON risk_scores(decision);
CREATE INDEX idx_risk_scores_model ON risk_scores(model_name, created_at DESC);


-- =========================
-- RULES ENGINE
-- =========================
CREATE TABLE rules (
    rule_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    rule_name TEXT NOT NULL,
    description TEXT,
    risk_weight NUMERIC(3, 2),
    is_active BOOLEAN DEFAULT TRUE,
    rule_type TEXT,
    condition JSONB,
    action JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT rule_name_length CHECK (char_length(rule_name) > 0)
);

CREATE INDEX idx_rules_active ON rules(is_active);
CREATE INDEX idx_rules_name ON rules(rule_name);


-- =========================
-- RULE MATCHES
-- =========================
CREATE TABLE rule_matches (
    match_id BIGSERIAL PRIMARY KEY,
    transaction_id UUID NOT NULL REFERENCES transactions(transaction_id) ON DELETE CASCADE,
    rule_id UUID NOT NULL REFERENCES rules(rule_id) ON DELETE CASCADE,
    
    -- Contexto del match
    rule_name TEXT NOT NULL,
    matched_field TEXT,
    matched_value TEXT,
    expected_value TEXT,
    
    -- Riesgo
    risk_contribution NUMERIC(3, 2),
    severity TEXT,
    
    created_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT severity_check CHECK (severity IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL'))
);

CREATE INDEX idx_rule_matches_tx ON rule_matches(transaction_id);
CREATE INDEX idx_rule_matches_rule ON rule_matches(rule_id);
CREATE INDEX idx_rule_severity ON rule_matches(severity);


-- =========================
-- ALERTS
-- =========================
CREATE TABLE alerts (
    alert_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    transaction_id UUID NOT NULL REFERENCES transactions(transaction_id) ON DELETE CASCADE,
    
    alert_level TEXT NOT NULL,
    status TEXT DEFAULT 'OPEN',
    
    -- Assignment
    assigned_to UUID REFERENCES users(user_id) ON DELETE SET NULL,
    
    -- Temporal
    created_at TIMESTAMP DEFAULT NOW(),
    resolved_at TIMESTAMP,
    
    metadata JSONB,
    
    CONSTRAINT valid_level CHECK (alert_level IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    CONSTRAINT valid_status CHECK (status IN ('OPEN', 'IN_REVIEW', 'RESOLVED', 'DISMISSED'))
);

CREATE INDEX idx_alerts_tx ON alerts(transaction_id);
CREATE INDEX idx_alerts_status ON alerts(status);
CREATE INDEX idx_alerts_assigned ON alerts(assigned_to);
CREATE INDEX idx_alerts_created ON alerts(created_at DESC);


-- =========================
-- FRAUD CASE MANAGEMENT
-- =========================
CREATE TABLE cases (
    case_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    alert_id UUID REFERENCES alerts(alert_id) ON DELETE SET NULL,
    transaction_id UUID NOT NULL REFERENCES transactions(transaction_id) ON DELETE CASCADE,
    
    -- Investigación
    investigator UUID REFERENCES users(user_id) ON DELETE SET NULL,
    status TEXT DEFAULT 'OPEN',
    
    -- Resolución
    resolution TEXT,
    resolution_notes TEXT,
    
    -- Temporal
    created_at TIMESTAMP DEFAULT NOW(),
    closed_at TIMESTAMP,
    updated_at TIMESTAMP DEFAULT NOW(),
    
    metadata JSONB,
    
    CONSTRAINT valid_status CHECK (status IN ('OPEN', 'IN_PROGRESS', 'ESCALATED', 'CLOSED'))
);

CREATE INDEX idx_cases_tx ON cases(transaction_id);
CREATE INDEX idx_cases_investigator ON cases(investigator);
CREATE INDEX idx_cases_status ON cases(status);


-- =========================
-- FRAUD FEEDBACK / GROUND TRUTH
-- =========================
CREATE TABLE fraud_feedback (
    feedback_id BIGSERIAL PRIMARY KEY,
    transaction_id UUID NOT NULL REFERENCES transactions(transaction_id) ON DELETE CASCADE,
    
    -- Ground truth
    is_fraud BOOLEAN NOT NULL,
    fraud_type TEXT,
    
    -- Quién lo validó
    reviewed_by UUID NOT NULL REFERENCES users(user_id) ON DELETE RESTRICT,
    reviewed_at TIMESTAMP DEFAULT NOW(),
    
    -- Contexto
    notes TEXT,
    confidence NUMERIC(3, 2),
    
    -- ML feedback
    predicted_fraud BOOLEAN,
    was_model_correct BOOLEAN,
    
    created_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT unique_feedback UNIQUE(transaction_id, reviewed_by),
    CONSTRAINT confidence_range CHECK (confidence >= 0 AND confidence <= 1)
);

CREATE INDEX idx_feedback_tx ON fraud_feedback(transaction_id);
CREATE INDEX idx_feedback_fraud ON fraud_feedback(is_fraud);
CREATE INDEX idx_feedback_accuracy ON fraud_feedback(was_model_correct);
CREATE INDEX idx_feedback_reviewer ON fraud_feedback(reviewed_by);


-- =========================
-- VELOCITY CHECKS
-- =========================
CREATE TABLE velocity_checks (
    check_id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    
    -- Tipo de chequeo
    check_type TEXT NOT NULL,
    
    -- Valores
    current_value NUMERIC,
    threshold_value NUMERIC,
    exceeded BOOLEAN,
    
    -- Temporal
    window_start TIMESTAMP,
    window_end TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT valid_type CHECK (check_type IN ('TXN_COUNT_1H', 'TXN_COUNT_24H', 'AMOUNT_1H', 'AMOUNT_24H', 'LOCATION_30M', 'IP_30M', 'CARD_MULT_MERCHANTS'))
);

CREATE INDEX idx_velocity_user_type ON velocity_checks(user_id, check_type, created_at DESC);


-- =========================
-- FEATURE CACHE
-- =========================
CREATE TABLE feature_cache (
    cache_id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    
    feature_set JSONB NOT NULL,
    
    -- Ventana temporal
    time_window TEXT,
    window_start TIMESTAMP,
    window_end TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT NOW(),
    ttl TIMESTAMP,
    
    CONSTRAINT unique_cache UNIQUE(user_id, time_window),
    CONSTRAINT valid_window CHECK (time_window IN ('1H', '24H', '7D', '30D'))
);

CREATE INDEX idx_cache_user ON feature_cache(user_id);
CREATE INDEX idx_cache_ttl ON feature_cache(ttl) WHERE ttl > NOW();


-- =========================
-- AUDIT LOGS
-- =========================
CREATE TABLE audit_logs (
    log_id BIGSERIAL PRIMARY KEY,
    
    entity_type TEXT NOT NULL,
    entity_id TEXT,
    action TEXT NOT NULL,
    
    old_value JSONB,
    new_value JSONB,
    
    actor UUID REFERENCES users(user_id) ON DELETE SET NULL,
    
    created_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT valid_action CHECK (action IN ('CREATE', 'READ', 'UPDATE', 'DELETE', 'APPROVE', 'REJECT'))
);

CREATE INDEX idx_audit_entity ON audit_logs(entity_type, entity_id);
CREATE INDEX idx_audit_actor ON audit_logs(actor);
CREATE INDEX idx_audit_action ON audit_logs(action);
CREATE INDEX idx_audit_created ON audit_logs(created_at DESC);


-- =========================
-- SEED DATA
-- =========================

-- Companies
INSERT INTO companies (name, industry, country_code, metadata)
VALUES
  ('SafeMarket Inc', 'FinTech', 'US', '{"tier": "enterprise", "region": "LATAM"}'),
  ('Test Company SA', 'Retail', 'AR', '{"tier": "pro", "region": "LATAM"}'),
  ('Demo Corp', 'Banking', 'CO', '{"tier": "starter", "region": "LATAM"}')
ON CONFLICT (name) DO NOTHING;

-- Users (con contraseñas hasheadas usando bcrypt)
-- Contraseña de ejemplo: SecurePass123! (bcrypt hash)
INSERT INTO users (email, hashed_password, role, department, company_id, status, is_email_verified, metadata)
VALUES
  (
    'admin@safemarket.io',
    '$2b$12$J2R1vEE/0TE4CrWVkVBH/u.3G6AW6B7p8cHVV4K5nE8Dt9nDWmRdC',
    'ADMIN',
    'Management',
    (SELECT company_id FROM companies WHERE name = 'SafeMarket Inc'),
    'ACTIVE',
    TRUE,
    '{"name": "Admin User", "last_login": "2026-04-14T10:00:00Z"}'
  ),
  (
    'analyst@safemarket.io',
    '$2b$12$J2R1vEE/0TE4CrWVkVBH/u.3G6AW6B7p8cHVV4K5nE8Dt9nDWmRdC',
    'ANALYST',
    'Fraud Detection',
    (SELECT company_id FROM companies WHERE name = 'SafeMarket Inc'),
    'ACTIVE',
    TRUE,
    '{"name": "Analyst User", "teams": ["fraud_detection", "risk"]}'
  ),
  (
    'reviewer@safemarket.io',
    '$2b$12$J2R1vEE/0TE4CrWVkVBH/u.3G6AW6B7p8cHVV4K5nE8Dt9nDWmRdC',
    'REVIEWER',
    'Case Management',
    (SELECT company_id FROM companies WHERE name = 'SafeMarket Inc'),
    'ACTIVE',
    TRUE,
    '{"name": "Reviewer User", "expertise": ["fraud_investigation", "chargebacks"]}'
  ),
  (
    'customer1@example.com',
    '$2b$12$J2R1vEE/0TE4CrWVkVBH/u.3G6AW6B7p8cHVV4K5nE8Dt9nDWmRdC',
    'VIEWER',
    'Sales',
    (SELECT company_id FROM companies WHERE name = 'Test Company SA'),
    'ACTIVE',
    TRUE,
    '{"name": "Customer One", "region": "Buenos Aires"}'
  ),
  (
    'customer2@example.com',
    '$2b$12$J2R1vEE/0TE4CrWVkVBH/u.3G6AW6B7p8cHVV4K5nE8Dt9nDWmRdC',
    'VIEWER',
    'Operations',
    (SELECT company_id FROM companies WHERE name = 'Demo Corp'),
    'ACTIVE',
    TRUE,
    '{"name": "Customer Two", "region": "Bogotá"}'
  )
ON CONFLICT (email) DO NOTHING;

-- Devices (Fingerprinting)
INSERT INTO devices (user_id, device_fingerprint, device_name, device_type, os, browser, ip, country, city, risk_level, is_trusted, trust_score)
SELECT
  u.user_id,
  md5(u.email || 'device1')::text,
  'MacBook Pro 13',
  'DESKTOP',
  'macOS 14.4',
  'Chrome 124',
  '192.168.1.100'::inet,
  'Argentina',
  'Buenos Aires',
  'LOW',
  true,
  0.95
FROM users u WHERE u.email = 'customer1@example.com'
ON CONFLICT (device_fingerprint) DO NOTHING;

INSERT INTO devices (user_id, device_fingerprint, device_name, device_type, os, browser, ip, country, city, risk_level, is_trusted, trust_score)
SELECT
  u.user_id,
  md5(u.email || 'device2')::text,
  'iPhone 14 Pro',
  'MOBILE',
  'iOS 17.0',
  'Safari',
  '203.45.67.200'::inet,
  'Argentina',
  'Buenos Aires',
  'MEDIUM',
  false,
  0.65
FROM users u WHERE u.email = 'customer1@example.com'
ON CONFLICT (device_fingerprint) DO NOTHING;

INSERT INTO devices (user_id, device_fingerprint, device_name, device_type, os, browser, ip, country, city, risk_level, is_trusted, trust_score)
SELECT
  u.user_id,
  md5(u.email || 'device1')::text,
  'Dell XPS 15',
  'DESKTOP',
  'Windows 11',
  'Edge 124',
  '201.134.56.89'::inet,
  'Colombia',
  'Bogotá',
  'MEDIUM',
  false,
  0.60
FROM users u WHERE u.email = 'customer2@example.com'
ON CONFLICT (device_fingerprint) DO NOTHING;

-- Sessions
INSERT INTO sessions (user_id, device_id, login_time, authentication_method, risk_level, mfa_used)
SELECT
  u.user_id,
  d.device_id,
  NOW() - INTERVAL '2 hours',
  'PASSWORD',
  'LOW',
  false
FROM users u
JOIN devices d ON u.user_id = d.user_id
WHERE u.email = 'customer1@example.com' AND d.device_name = 'MacBook Pro 13'
LIMIT 1;

INSERT INTO sessions (user_id, device_id, login_time, authentication_method, risk_level, mfa_used)
SELECT
  u.user_id,
  d.device_id,
  NOW() - INTERVAL '1 hour',
  'PASSWORD',
  'MEDIUM',
  false
FROM users u
JOIN devices d ON u.user_id = d.user_id
WHERE u.email = 'customer2@example.com' AND d.device_name = 'Dell XPS 15'
LIMIT 1;

-- Transactions (Datos realistas de prueba)
INSERT INTO transactions (
  user_id, device_id, session_id,
  source_account, source_type, amount, currency,
  destination_merchant, merchant_id, merchant_category,
  transaction_type, description, status, risk_level, risk_score
)
SELECT
  u.user_id,
  d.device_id,
  s.session_id,
  'ACC-12345678',
  'CARD',
  ARRAY[150.00, 250.50, 75.99, 500.00, 1200.00][floor(random()*5 + 1)],
  'USD',
  'Amazon.com',
  'MERCHANT-001',
  '5411',
  'PURCHASE',
  'Online shopping',
  'PENDING',
  'LOW',
  0.15
FROM users u
JOIN devices d ON u.user_id = d.user_id
JOIN sessions s ON u.user_id = s.user_id
WHERE u.email = 'customer1@example.com'
LIMIT 1;

INSERT INTO transactions (
  user_id, device_id, session_id,
  source_account, source_type, amount, currency,
  destination_merchant, merchant_id, merchant_category,
  transaction_type, description, status, risk_level, risk_score
)
SELECT
  u.user_id,
  d.device_id,
  s.session_id,
  'ACC-87654321',
  'CARD',
  ARRAY[100.00, 300.00, 450.50, 2500.00][floor(random()*4 + 1)],
  'USD',
  'Microsoft Corporation',
  'MERCHANT-002',
  '5733',
  'PURCHASE',
  'Software subscription',
  'APPROVED',
  'MEDIUM',
  0.35
FROM users u
JOIN devices d ON u.user_id = d.user_id
JOIN sessions s ON u.user_id = s.user_id
WHERE u.email = 'customer2@example.com'
LIMIT 1;

-- Agregar transacciones adicionales con riesgo variable
INSERT INTO transactions (
  user_id, device_id,
  source_account, source_type, amount, currency,
  destination_merchant, merchant_id, merchant_category,
  transaction_type, description, status, risk_level, risk_score, is_fraud
)
SELECT
  u.user_id,
  (SELECT device_id FROM devices WHERE user_id = u.user_id LIMIT 1),
  'ACC-11111111',
  'CARD',
  (RANDOM() * 5000 + 100)::numeric(14,2),
  'USD',
  'Unknown Merchant ' || i,
  'MERCHANT-' || i,
  '5411',
  'PURCHASE',
  'Random transaction ' || i,
  CASE WHEN i % 3 = 0 THEN 'REVIEW' WHEN i % 2 = 0 THEN 'APPROVED' ELSE 'PENDING' END,
  CASE WHEN i % 4 = 0 THEN 'HIGH' WHEN i % 3 = 0 THEN 'MEDIUM' ELSE 'LOW' END,
  (RANDOM() * 0.8)::numeric(3,2),
  (i % 10 = 0)  -- 10% are fraud
FROM users u
CROSS JOIN generate_series(1, 15) AS i
WHERE u.email IN ('customer1@example.com', 'customer2@example.com');

-- Rules
INSERT INTO rules (rule_name, description, risk_weight, rule_type)
VALUES
  ('High Amount', 'Transaction amount above $5000', 0.30, 'AMOUNT_BASED'),
  ('Velocity Check', 'More than 5 transactions in 1 hour', 0.40, 'VELOCITY_BASED'),
  ('New Device', 'Transaction from untrusted device', 0.25, 'DEVICE_BASED'),
  ('Merchant Mismatch', 'Unusual merchant for user', 0.20, 'BEHAVIORAL'),
  ('Location Anomaly', 'Transaction from unusual location', 0.35, 'LOCATION_BASED')
ON CONFLICT (rule_name) DO NOTHING;

-- Audit Logs
INSERT INTO audit_logs (entity_type, entity_id, action, actor)
SELECT
  'TRANSACTION',
  t.transaction_id::text,
  'CREATE',
  u.user_id
FROM transactions t
JOIN users u ON t.user_id = u.user_id
WHERE u.email = 'admin@safemarket.io'
LIMIT 5;

-- Print confirmación
SELECT '✅ Database schema and seed data loaded successfully!' AS status;
SELECT format('Users created: %s', COUNT(*)) FROM users;
SELECT format('Transactions created: %s', COUNT(*)) FROM transactions;
SELECT format('Devices created: %s', COUNT(*)) FROM devices;
SELECT format('Sessions created: %s', COUNT(*)) FROM sessions;
