"""
AI Detection Testing Script
Run this to test the AI detection functionality against your running backend
"""
import requests
import json
import sys
from pathlib import Path
from datetime import datetime

# Configuration
BACKEND_URL = "http://localhost:8000"
FACULTY_API = f"{BACKEND_URL}/api/faculty"

def print_header(title):
    """Print a formatted header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def print_section(title):
    """Print a formatted section"""
    print(f"\n{'─' * 70}")
    print(f"  {title}")
    print(f"{'─' * 70}")

def test_ai_detection():
    """Main test function"""
    print_header("AI DETECTION TESTING")
    
    try:
        # Step 1: Check backend connectivity
        print_section("Step 1: Checking Backend Connectivity")
        try:
            response = requests.get(f"{BACKEND_URL}/docs", timeout=5)
            print(f"✅ Backend is running on {BACKEND_URL}")
        except:
            print(f"❌ Cannot connect to backend at {BACKEND_URL}")
            print(f"   💡 Start backend with: python start_evaluation_server.py")
            return False
        
        # Step 2: Get pending submissions
        print_section("Step 2: Fetching Pending Submissions")
        response = requests.get(f"{FACULTY_API}/pending-submissions", timeout=10)
        response.raise_for_status()
        submissions = response.json()
        
        if not submissions:
            print("❌ No pending submissions found")
            print("   💡 Create a student submission first:")
            print("      1. Go to Student Workflow page")
            print("      2. Select an assignment")
            print("      3. Submit your response")
            print("      4. Return to Faculty Evaluation")
            return False
        
        print(f"✅ Found {len(submissions)} pending submission(s)")
        print("\n   Submissions:")
        for i, sub in enumerate(submissions, 1):
            print(f"   {i}. ID: {sub['id']}")
            print(f"      Student: {sub['student_id']}")
            print(f"      Assignment: {sub['assignment_id']}")
            print(f"      Status: {sub['evaluation_status']}")
        
        # Step 3: Test AI detection on first submission
        submission = submissions[0]
        submission_id = submission['id']
        
        print_section(f"Step 3: Running AI Detection Analysis")
        print(f"Testing on submission ID: {submission_id}")
        print(f"Student ID: {submission['student_id']}")
        
        try:
            response = requests.post(
                f"{FACULTY_API}/submissions/{submission_id}/detect-ai",
                json={},
                timeout=60  # AI detection might take a while
            )
            response.raise_for_status()
            results = response.json()
        except requests.exceptions.Timeout:
            print("❌ Request timed out - AI detection might be slow")
            print("   💡 This can happen on first run (model loading)")
            return False
        except requests.exceptions.HTTPError as e:
            print(f"❌ HTTP Error {e.response.status_code}")
            print(f"   Response: {e.response.text}")
            return False
        
        # Step 4: Display AI Detection Results
        print_section("Step 4: AI Detection Results")
        
        ai_results = results.get('ai_detection_results', {})
        risk_assessment = results.get('risk_assessment', {})
        recommendations = results.get('recommendations', [])
        submission_stats = results.get('submission_stats', {})
        
        print(f"\n📊 AI Detection Metrics:")
        ai_prob = ai_results.get('ai_probability', 0)
        print(f"   • AI Probability: {ai_prob:.1%}")
        print(f"   • Is Likely AI: {ai_results.get('is_likely_ai', False)}")
        print(f"   • Confidence Score: {ai_results.get('confidence_score', 0):.1%}")
        
        print(f"\n⚠️  Risk Assessment:")
        print(f"   • Risk Level: {risk_assessment.get('risk_level', 'Unknown')}")
        print(f"   • Risk Score: {risk_assessment.get('risk_score', 'N/A')}/3")
        print(f"   • Explanation: {risk_assessment.get('explanation', 'N/A')}")
        
        print(f"\n💡 Recommendations:")
        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                print(f"   {i}. {rec}")
        else:
            print("   (No specific recommendations)")
        
        print(f"\n📈 Submission Statistics:")
        print(f"   • Text Length: {submission_stats.get('text_length', 0):,} characters")
        print(f"   • Word Count: {submission_stats.get('word_count', 0):,} words")
        
        # Step 5: Display Analysis Details
        print_section("Step 5: Detailed Analysis")
        analysis_details = ai_results.get('analysis_details', {})
        print(f"\n   Model Information:")
        print(f"   • Model Name: {analysis_details.get('model_name', 'Unknown')}")
        print(f"   • Threshold: {analysis_details.get('threshold', 'N/A')}")
        print(f"   • Raw Probability: {analysis_details.get('raw_probability', 'N/A'):.3f}")
        
        # Step 6: Save results
        print_section("Step 6: Saving Results")
        output_file = f"ai_detection_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)
        print(f"✅ Results saved to: {output_file}")
        
        # Summary
        print_header("TEST COMPLETED SUCCESSFULLY ✅")
        print(f"\n   Model: RADAR-Vicuna-7B")
        print(f"   Submission: {submission_id}")
        print(f"   AI Probability: {ai_prob:.1%}")
        print(f"   Risk Level: {risk_assessment.get('risk_level', 'Unknown')}")
        
        return True
        
    except requests.exceptions.ConnectionError as e:
        print_header("CONNECTION ERROR ❌")
        print(f"\n   Failed to connect to backend: {str(e)}")
        print(f"   Backend URL: {BACKEND_URL}")
        print(f"\n   💡 Make sure backend is running:")
        print(f"      cd backend")
        print(f"      python start_evaluation_server.py")
        return False
    except requests.exceptions.Timeout:
        print_header("TIMEOUT ERROR ❌")
        print(f"\n   Request timed out after 60 seconds")
        print(f"   💡 AI detection might be processing large text")
        return False
    except Exception as e:
        print_header("ERROR ❌")
        print(f"\n   {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        success = test_ai_detection()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
