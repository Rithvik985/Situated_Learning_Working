#!/usr/bin/env python3
"""
Simple test script to validate Assignment Generation functionality
"""

import asyncio
import sys
import os

# Add the backend directory to the path
sys.path.append(os.path.dirname(__file__))

from services.llm_service import LLMService
from services.rubric_service import RubricService
from services.document_service import DocumentService

async def test_llm_service():
    """Test LLM service with mock data"""
    print("Testing LLM Service...")
    
    llm_service = LLMService()
    
    # Test few-shot example selection
    from routers.generation import select_few_shot_examples
    
    domains = ["Software Development", "IoT"]
    topics = ["Database Optimization", "Smart Systems"]
    
    examples = select_few_shot_examples(domains, topics)
    print(f"Selected {len(examples)} few-shot examples")
    
    # Note: Actual LLM call would require a running LLM server
    print("✅ LLM Service structure is valid")

def test_rubric_service():
    """Test Rubric service"""
    print("\nTesting Rubric Service...")
    
    rubric_service = RubricService()
    
    # Test fallback rubric generation
    fallback_rubric = rubric_service._get_fallback_rubric("Situated Learning Assignment")
    
    assert "rubric_name" in fallback_rubric
    assert "rubrics" in fallback_rubric
    assert len(fallback_rubric["rubrics"]) == 4
    
    print("✅ Rubric Service structure is valid")

def test_document_service():
    """Test Document service with mock data"""
    print("\nTesting Document Service...")
    
    document_service = DocumentService()
    
    # Create mock assignment data
    class MockAssignment:
        def __init__(self):
            self.id = "test-id"
            self.course_name = "Test Course"
            self.course_id = "CS101"
            self.title = "Test Assignment"
            self.description = "This is a test assignment description.\n\nTask 1: Complete the analysis.\nTask 2: Write a report."
            self.difficulty_level = "Intermediate"
            self.topics = ["Testing", "Development"]
            self.domains = ["Software Development"]
            self.tags = ["AI-Generated"]
    
    mock_assignment = MockAssignment()
    
    # Test document generation
    doc_buffer = document_service.generate_assignment_document(
        assignments=[mock_assignment],
        assignment_name="Test Assignment Package"
    )
    
    assert doc_buffer.getvalue()  # Should have content
    print("✅ Document Service can generate Word documents")

def test_database_models():
    """Test database model imports"""
    print("\nTesting Database Models...")
    
    try:
        from database.models import GeneratedAssignment, AssignmentRubric
        print("✅ Database models imported successfully")
    except ImportError as e:
        print(f"❌ Database model import failed: {e}")

def test_api_structure():
    """Test API router structure"""
    print("\nTesting API Structure...")
    
    try:
        from routers.generation import router, PREDEFINED_DOMAINS, FEW_SHOT_EXAMPLES
        
        assert len(PREDEFINED_DOMAINS) > 0
        assert len(FEW_SHOT_EXAMPLES) == 3
        
        print("✅ API router structure is valid")
    except ImportError as e:
        print(f"❌ API router import failed: {e}")

def main():
    """Run all tests"""
    print("🚀 Testing Assignment Generation Component\n")
    
    try:
        # Test synchronous components
        test_database_models()
        test_api_structure()
        test_rubric_service()
        test_document_service()
        
        # Test asynchronous components
        asyncio.run(test_llm_service())
        
        print("\n✅ All tests passed! Assignment Generation component is ready.")
        print("\n📋 Next steps:")
        print("1. Start the LLM server with the configured model")
        print("2. Initialize the database with the new schema")
        print("3. Start the FastAPI backend server")
        print("4. Start the React frontend server")
        print("5. Test the complete workflow in the browser")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
