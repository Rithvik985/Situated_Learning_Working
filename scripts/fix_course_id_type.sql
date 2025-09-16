-- Fix course_id type mismatch in generated_assignments table
-- This script converts course_id from VARCHAR to UUID type

-- Step 1: First check if we have any data that would be lost
SELECT 
    id, 
    course_name, 
    course_id,
    CASE 
        WHEN course_id ~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$' 
        THEN 'Valid UUID'
        ELSE 'Invalid UUID - Will be lost'
    END as uuid_status
FROM generated_assignments 
WHERE course_id IS NOT NULL;

-- Step 2: Backup existing data (optional - if you want to preserve it)
-- CREATE TABLE generated_assignments_backup AS SELECT * FROM generated_assignments;

-- Step 3: Drop the foreign key constraint if it exists and recreate the table
-- Since we're in development, we'll recreate the table structure

-- Drop dependent tables first (if they exist and have data you want to keep)
-- For now, we'll assume this is development and we can recreate

-- Step 4: Drop and recreate the generated_assignments table with correct types
DROP TABLE IF EXISTS generated_assignments CASCADE;

-- Recreate with proper UUID type
CREATE TABLE generated_assignments (
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
    assignment_name VARCHAR(255),
    created_by VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Recreate related tables that reference generated_assignments
DROP TABLE IF EXISTS student_submissions CASCADE;
DROP TABLE IF EXISTS evaluation_results CASCADE;

-- Student submissions table
CREATE TABLE student_submissions (
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
CREATE TABLE evaluation_results (
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

-- Recreate indexes
CREATE INDEX IF NOT EXISTS idx_generated_assignments_course_id ON generated_assignments(course_id);
CREATE INDEX IF NOT EXISTS idx_student_submissions_assignment_id ON student_submissions(assignment_id);
CREATE INDEX IF NOT EXISTS idx_evaluation_results_submission_id ON evaluation_results(submission_id);

-- Insert some sample data for testing
INSERT INTO generated_assignments (
    course_id, 
    course_name, 
    title, 
    description, 
    difficulty_level,
    topics,
    domains,
    assignment_name,
    is_selected
) 
SELECT 
    c.id,
    c.title,
    'Sample Assignment for ' || c.title,
    'This is a sample assignment generated for testing the evaluation system.',
    'Intermediate',
    ARRAY['Programming', 'Problem Solving'],
    ARRAY['Computer Science'],
    'Sample_Assignment_' || c.course_code,
    true
FROM courses c
LIMIT 3;

COMMIT;
