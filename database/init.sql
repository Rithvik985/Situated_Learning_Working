-- Situated Learning System Database Schema
-- Initialize PostgreSQL database with required tables

-- Create database (handled by docker-compose environment variables)

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Courses table
CREATE TABLE IF NOT EXISTS courses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(255) NOT NULL,
    course_code VARCHAR(50) NOT NULL,
    academic_year VARCHAR(20) NOT NULL,
    semester INTEGER NOT NULL CHECK (semester IN (1, 2)),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(title, course_code, academic_year, semester)
);

-- Past assignments table (reference corpus)
CREATE TABLE IF NOT EXISTS past_assignments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    course_id UUID REFERENCES courses(id) ON DELETE CASCADE,
    original_file_name VARCHAR(255) NOT NULL,
    original_file_path VARCHAR(500) NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    file_size BIGINT,
    processing_status VARCHAR(50) DEFAULT 'pending',
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Assignment questions table (extracted from past assignments)
CREATE TABLE IF NOT EXISTS assignment_questions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    assignment_id UUID REFERENCES past_assignments(id) ON DELETE CASCADE,
    question_number INTEGER NOT NULL,
    question_text TEXT,
    extracted_content TEXT,
    partitioned_file_path VARCHAR(500),
    has_images BOOLEAN DEFAULT FALSE,
    processing_metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(assignment_id, question_number)
);

-- Generated assignments table
CREATE TABLE IF NOT EXISTS generated_assignments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    course_name VARCHAR(255) NOT NULL,
    course_id UUID REFERENCES courses(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    requirements TEXT[],
    industry_context TEXT,
    estimated_time INTEGER,
    difficulty_level VARCHAR(50) CHECK (difficulty_level IN ('Beginner', 'Intermediate', 'Advanced')),
    class_numbers INTEGER[],
    topics TEXT[],
    domains TEXT[],
    custom_instructions TEXT,
    tags TEXT[] DEFAULT '{"AI-Generated"}',
    version INTEGER DEFAULT 1,
    parent_assignment_id UUID REFERENCES generated_assignments(id),
    reason_for_change TEXT,
    is_selected BOOLEAN DEFAULT FALSE,
    assignment_name VARCHAR(255), -- For saving assignments with user-provided names
    created_by VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Assignment rubrics table
CREATE TABLE IF NOT EXISTS assignment_rubrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    assignment_ids UUID[] NOT NULL, -- Array of assignment IDs this rubric applies to
    rubric_name VARCHAR(255) NOT NULL,
    doc_type VARCHAR(100) DEFAULT 'Assignment',
    criteria JSONB NOT NULL, -- Full rubric structure with categories and questions
    total_points INTEGER,
    is_edited BOOLEAN DEFAULT FALSE,
    reason_for_edit TEXT, -- Reason when rubric is edited
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Student submissions table
CREATE TABLE IF NOT EXISTS student_submissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    assignment_id UUID REFERENCES generated_assignments(id) ON DELETE CASCADE,
    original_file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    file_size BIGINT,
    processing_status VARCHAR(50) DEFAULT 'pending' CHECK (processing_status IN ('pending', 'processed', 'failed')),
    extraction_method VARCHAR(50) CHECK (extraction_method IN ('standard', 'ocr', 'ocr_vision_llm', 'standard_fallback')),
    extracted_text TEXT,
    ocr_confidence DECIMAL(5,4),
    processing_metadata JSONB,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Evaluation results table
CREATE TABLE IF NOT EXISTS evaluation_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    submission_id UUID REFERENCES student_submissions(id) ON DELETE CASCADE,
    assignment_id UUID REFERENCES generated_assignments(id) ON DELETE CASCADE,
    rubric_id UUID REFERENCES assignment_rubrics(id) ON DELETE CASCADE,
    overall_score DECIMAL(5,2) NOT NULL CHECK (overall_score >= 0),
    criterion_scores JSONB,
    ai_feedback TEXT,
    faculty_feedback TEXT,
    faculty_score_adjustment DECIMAL(5,2),
    faculty_reason TEXT,
    flags TEXT[],
    evaluation_metadata JSONB,
    faculty_reviewed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Upload processing status table
CREATE TABLE IF NOT EXISTS upload_status (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    upload_type VARCHAR(50) NOT NULL,
    file_count INTEGER,
    processed_count INTEGER DEFAULT 0,
    status VARCHAR(50) DEFAULT 'pending',
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_courses_course_code ON courses(course_code);
CREATE INDEX IF NOT EXISTS idx_past_assignments_course_id ON past_assignments(course_id);
CREATE INDEX IF NOT EXISTS idx_generated_assignments_course_id ON generated_assignments(course_id);
CREATE INDEX IF NOT EXISTS idx_student_submissions_assignment_id ON student_submissions(assignment_id);
CREATE INDEX IF NOT EXISTS idx_evaluation_results_submission_id ON evaluation_results(submission_id);

-- Insert sample data for development
INSERT INTO courses (title, course_code, academic_year, semester, description) VALUES 
    ('Introduction to Computer Science', 'CS101', '2023-24', 1, 'Basic programming and computer science concepts'),
    ('Data Structures and Algorithms', 'CS201', '2023-24', 2, 'Advanced data structures and algorithmic thinking'),
    ('Business Analytics', 'BUS301', '2023-24', 1, 'Data-driven business decision making'),
    ('Digital Marketing', 'MKT201', '2023-24', 2, 'Modern digital marketing strategies and tools')
ON CONFLICT (title, course_code, academic_year, semester) DO NOTHING;
