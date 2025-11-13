-- Situated Learning System Database Schema (PostgreSQL)
-- Generated to match backend/database/models.py

-- Enable extensions for UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================
-- Courses
-- =====================================================
CREATE TABLE IF NOT EXISTS courses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(255) NOT NULL,
    course_code VARCHAR(50) NOT NULL,
    academic_year VARCHAR(20) NOT NULL,
    semester INTEGER NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT unique_course UNIQUE (title, course_code, academic_year, semester),
    CONSTRAINT check_semester CHECK (semester IN (1,2))
);

-- =====================================================
-- Past Assignments
-- =====================================================
CREATE TABLE IF NOT EXISTS past_assignments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    original_file_name VARCHAR(255) NOT NULL,
    original_file_path VARCHAR(500) NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    file_size BIGINT,
    processing_status VARCHAR(50) DEFAULT 'pending',
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- =====================================================
-- Assignment Questions (extracted from past assignments)
-- =====================================================
CREATE TABLE IF NOT EXISTS assignment_questions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    assignment_id UUID NOT NULL REFERENCES past_assignments(id) ON DELETE CASCADE,
    question_number INTEGER NOT NULL,
    question_text TEXT,
    extracted_content TEXT,
    partitioned_file_path VARCHAR(500),
    has_images BOOLEAN DEFAULT FALSE,
    processing_metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT unique_assignment_question UNIQUE (assignment_id, question_number)
);

-- =====================================================
-- Generated Assignments
-- =====================================================
CREATE TABLE IF NOT EXISTS generated_assignments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    course_name VARCHAR(255) NOT NULL,
    course_id UUID REFERENCES courses(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    requirements TEXT[],
    industry_context TEXT,
    estimated_time INTEGER,
    difficulty_level VARCHAR(50),
    class_numbers INTEGER[],
    topics TEXT[],
    domains TEXT[],
    custom_instructions TEXT,
    tags TEXT[] DEFAULT '{"AI-Generated"}',
    version INTEGER DEFAULT 1,
    parent_assignment_id UUID REFERENCES generated_assignments(id),
    reason_for_change TEXT,
    is_selected BOOLEAN DEFAULT FALSE,
    assignment_name VARCHAR(255),
    created_by VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT check_difficulty_level CHECK (difficulty_level IN ('Beginner','Intermediate','Advanced'))
);

-- =====================================================
-- Assignment Rubrics
-- =====================================================
CREATE TABLE IF NOT EXISTS assignment_rubrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    assignment_ids UUID[] NOT NULL,
    rubric_name VARCHAR(255) NOT NULL,
    doc_type VARCHAR(100) DEFAULT 'Assignment',
    criteria JSONB NOT NULL,
    total_points INTEGER,
    is_edited BOOLEAN DEFAULT FALSE,
    reason_for_edit TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- =====================================================
-- Student Submissions
-- =====================================================
CREATE TABLE IF NOT EXISTS student_submissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id VARCHAR(255) NOT NULL,
    assignment_id UUID NOT NULL REFERENCES generated_assignments(id) ON DELETE CASCADE,
    course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    original_file_name VARCHAR(255),
    file_path VARCHAR(500),
    file_type VARCHAR(50),
    file_size BIGINT,
    content TEXT,
    extracted_text TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    submission_date TIMESTAMPTZ DEFAULT NOW(),
    processing_status VARCHAR(50) DEFAULT 'pending',
    evaluation_status VARCHAR(50) DEFAULT 'draft',
    extraction_method VARCHAR(50),
    ocr_confidence DOUBLE PRECISION,
    processing_metadata JSONB,
    evaluation_score DOUBLE PRECISION,
    rejection_reason TEXT,
    rejection_date TIMESTAMPTZ,
    faculty_feedback TEXT,
    swot_analysis JSONB,
    ai_detection_results JSONB,
    error_message TEXT
);

-- =====================================================
-- Faculty Evaluation Results
-- =====================================================
CREATE TABLE IF NOT EXISTS faculty_evaluation_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    submission_id UUID NOT NULL REFERENCES student_submissions(id) ON DELETE CASCADE,
    faculty_id VARCHAR(255),
    rubric_scores JSONB NOT NULL,
    comments TEXT,
    evaluation_date TIMESTAMPTZ DEFAULT NOW()
);

-- =====================================================
-- Student SWOT Results
-- =====================================================
CREATE TABLE IF NOT EXISTS student_swot_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    submission_id UUID NOT NULL REFERENCES student_submissions(id) ON DELETE CASCADE,
    strengths TEXT[] NOT NULL,
    weaknesses TEXT[] NOT NULL,
    opportunities TEXT[] NOT NULL,
    threats TEXT[] NOT NULL,
    suggestions TEXT[] NOT NULL,
    analysis_date TIMESTAMPTZ DEFAULT NOW()
);

-- =====================================================
-- Evaluation Results (AI-based auto evaluations)
-- =====================================================
CREATE TABLE IF NOT EXISTS evaluation_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    submission_id UUID NOT NULL REFERENCES student_submissions(id) ON DELETE CASCADE,
    assignment_id UUID NOT NULL REFERENCES generated_assignments(id) ON DELETE CASCADE,
    rubric_id UUID NOT NULL REFERENCES assignment_rubrics(id) ON DELETE CASCADE,
    overall_score DOUBLE PRECISION NOT NULL CHECK (overall_score >= 0),
    criterion_scores JSONB,
    ai_feedback TEXT,
    faculty_feedback TEXT,
    faculty_score_adjustment DOUBLE PRECISION,
    faculty_reason TEXT,
    flags TEXT[],
    evaluation_metadata JSONB,
    faculty_reviewed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- =====================================================
-- Student Question Sets
-- =====================================================
CREATE TABLE IF NOT EXISTS student_question_sets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    course_id UUID REFERENCES courses(id) ON DELETE SET NULL,
    assignment_id UUID REFERENCES generated_assignments(id) ON DELETE SET NULL,
    student_id VARCHAR(255) NOT NULL,
    domain VARCHAR(255) NOT NULL,
    service_category VARCHAR(255),
    department VARCHAR(255),
    contextual_inputs JSONB,
    generated_questions TEXT[] NOT NULL,
    selected_question TEXT,
    approval_status VARCHAR(50) DEFAULT 'pending',
    approved_by VARCHAR(255),
    faculty_remarks TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT check_approval_status CHECK (approval_status IN ('pending','approved','rejected'))
);

-- =====================================================
-- Independent SWOT Submissions
-- =====================================================
CREATE TABLE IF NOT EXISTS swot_submissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id VARCHAR(255) NOT NULL,
    submission_id UUID,
    content TEXT NOT NULL,
    swot_analysis JSONB,
    processing_status VARCHAR(50) DEFAULT 'pending',
    evaluation_status VARCHAR(50) DEFAULT 'draft',
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- =====================================================
-- Indexes
-- =====================================================
CREATE INDEX IF NOT EXISTS idx_courses_code ON courses(course_code);
CREATE INDEX IF NOT EXISTS idx_past_assignments_course ON past_assignments(course_id);
CREATE INDEX IF NOT EXISTS idx_generated_assignments_course ON generated_assignments(course_id);
CREATE INDEX IF NOT EXISTS idx_student_submissions_assignment ON student_submissions(assignment_id);
CREATE INDEX IF NOT EXISTS idx_student_submissions_student ON student_submissions(student_id);
CREATE INDEX IF NOT EXISTS idx_student_submissions_status ON student_submissions(evaluation_status);
CREATE INDEX IF NOT EXISTS idx_faculty_eval_submission ON faculty_evaluation_results(submission_id);
CREATE INDEX IF NOT EXISTS idx_student_swot_submission ON student_swot_results(submission_id);
CREATE INDEX IF NOT EXISTS idx_eval_results_submission ON evaluation_results(submission_id);
CREATE INDEX IF NOT EXISTS idx_question_sets_student ON student_question_sets(student_id);
CREATE INDEX IF NOT EXISTS idx_question_sets_status ON student_question_sets(approval_status);
CREATE INDEX IF NOT EXISTS idx_question_sets_assignment ON student_question_sets(assignment_id);

-- End of schema
