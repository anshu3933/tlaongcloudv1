-- ============================================
-- User Management Tables
-- ============================================
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL CHECK (role IN ('admin', 'teacher', 'co_coordinator', 'coordinator')),
    is_active BOOLEAN DEFAULT true,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================
-- Approval Workflow Tables
-- ============================================
CREATE TABLE approval_hierarchies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_type VARCHAR(50) NOT NULL,
    step_order INTEGER NOT NULL,
    approver_role VARCHAR(50) NOT NULL,
    is_optional BOOLEAN DEFAULT false,
    auto_approve_timeout_hours INTEGER,
    UNIQUE(document_type, step_order)
);

CREATE TABLE approval_workflows (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_type VARCHAR(50) NOT NULL,
    document_id UUID NOT NULL,
    current_step INTEGER DEFAULT 1,
    status VARCHAR(50) DEFAULT 'pending',
    initiated_by UUID REFERENCES users(id),
    initiated_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    UNIQUE(document_type, document_id)
);

CREATE TABLE approval_steps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID REFERENCES approval_workflows(id) ON DELETE CASCADE,
    step_order INTEGER NOT NULL,
    approver_role VARCHAR(50) NOT NULL,
    assigned_to UUID REFERENCES users(id),
    status VARCHAR(50) DEFAULT 'pending',
    action_taken_at TIMESTAMP,
    comments TEXT,
    attachments JSONB,
    version_reviewed UUID,
    UNIQUE(workflow_id, step_order)
);

CREATE TABLE approval_notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID REFERENCES approval_workflows(id),
    step_id UUID REFERENCES approval_steps(id),
    recipient_id UUID REFERENCES users(id),
    notification_type VARCHAR(50),
    sent_at TIMESTAMP DEFAULT NOW(),
    read_at TIMESTAMP,
    reminder_count INTEGER DEFAULT 0,
    metadata JSONB
);

-- ============================================
-- Special Education Tables
-- ============================================
CREATE TABLE disability_types (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    accommodation_defaults JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE iep_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    disability_type_id UUID REFERENCES disability_types(id),
    grade_level VARCHAR(20),
    sections JSONB NOT NULL,
    version INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT true,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE ieps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL,
    template_id UUID REFERENCES iep_templates(id),
    academic_year VARCHAR(9) NOT NULL,
    status VARCHAR(50) DEFAULT 'draft',
    content JSONB NOT NULL,
    version INTEGER DEFAULT 1,
    parent_version_id UUID REFERENCES ieps(id),
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    approved_at TIMESTAMP,
    approved_by UUID REFERENCES users(id),
    UNIQUE(student_id, academic_year, version)
);

CREATE TABLE iep_goals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    iep_id UUID REFERENCES ieps(id) ON DELETE CASCADE,
    domain VARCHAR(100) NOT NULL,
    goal_text TEXT NOT NULL,
    baseline TEXT,
    target_criteria TEXT,
    measurement_method TEXT,
    target_date DATE,
    progress_status VARCHAR(50) DEFAULT 'not_started',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE pl_assessment_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    disability_type_id UUID REFERENCES disability_types(id),
    skill_domains JSONB NOT NULL,
    version INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE present_levels (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL,
    iep_id UUID REFERENCES ieps(id),
    template_id UUID REFERENCES pl_assessment_templates(id),
    assessment_date DATE NOT NULL,
    assessment_type VARCHAR(50),
    assessor_id UUID REFERENCES users(id),
    content JSONB NOT NULL,
    version INTEGER DEFAULT 1,
    parent_version_id UUID REFERENCES present_levels(id),
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================
-- Audit Trail Table
-- ============================================
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type VARCHAR(50) NOT NULL,
    entity_id UUID NOT NULL,
    action VARCHAR(50) NOT NULL,
    changes JSONB,
    user_id UUID NOT NULL,
    user_role VARCHAR(50),
    timestamp TIMESTAMP DEFAULT NOW(),
    ip_address INET,
    user_agent TEXT
);

-- ============================================
-- Indexes for Performance
-- ============================================
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_sessions_token ON user_sessions(token_hash);
CREATE INDEX idx_sessions_expires ON user_sessions(expires_at);
CREATE INDEX idx_workflows_status ON approval_workflows(status);
CREATE INDEX idx_workflows_document ON approval_workflows(document_type, document_id);
CREATE INDEX idx_ieps_student_year ON ieps(student_id, academic_year);
CREATE INDEX idx_ieps_status ON ieps(status);
CREATE INDEX idx_pl_student_date ON present_levels(student_id, assessment_date);
CREATE INDEX idx_audit_entity ON audit_logs(entity_type, entity_id);
CREATE INDEX idx_audit_timestamp ON audit_logs(timestamp);

-- ============================================
-- Initial Data
-- ============================================
-- Default approval hierarchies
INSERT INTO approval_hierarchies (document_type, step_order, approver_role) VALUES
('iep', 1, 'teacher'),
('iep', 2, 'co_coordinator'),
('iep', 3, 'coordinator'),
('pl_assessment', 1, 'teacher'),
('pl_assessment', 2, 'co_coordinator');

-- Common disability types
INSERT INTO disability_types (code, name, description) VALUES
('AUT', 'Autism Spectrum Disorder', 'Developmental disorder affecting communication and behavior'),
('ADHD', 'Attention Deficit Hyperactivity Disorder', 'Neurodevelopmental disorder affecting attention and activity'),
('DYS', 'Dyslexia', 'Learning disorder affecting reading and language processing'),
('ID', 'Intellectual Disability', 'Limitations in intellectual functioning and adaptive behavior'),
('PD', 'Physical Disability', 'Physical impairment affecting mobility or physical capacity'),
('MD', 'Multiple Disabilities', 'Combination of two or more disability conditions');
