-- Add AI detection results column to student_submissions table
ALTER TABLE student_submissions 
ADD COLUMN IF NOT EXISTS ai_detection_results JSONB;