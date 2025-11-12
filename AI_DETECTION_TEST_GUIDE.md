# AI Detection Testing Guide

## Overview
The AI detection system uses the **RADAR-Vicuna-7B** model to detect AI-generated content in student submissions. This guide provides multiple ways to test this functionality.

---

## Architecture

### Backend Components
- **Model**: `TrustSafeAI/RADAR-Vicuna-7B` (HuggingFace)
- **Service**: `RadarService` (`backend/services/radar_service.py`)
- **Endpoint**: `POST /api/faculty/submissions/{submission_id}/detect-ai`
- **Database**: Results stored in `student_submissions.ai_detection_results` (JSONB column)

### Frontend Components
- **Component**: `FacultyEvaluation.jsx`
- **Button**: "Detect AI Content" (appears alongside "Run AI Evaluation")
- **Display**: Shows risk level, AI probability, recommendations, and submission stats

---

## Testing Methods

### Method 1: Frontend UI Testing (Easiest)

#### Prerequisites
1. Backend server running: `python start_evaluation_server.py`
2. Frontend running: `npm run dev`
3. Have at least one student submission in `pending_faculty` status

#### Steps
1. Navigate to **Faculty Evaluation** page in the header
2. Select a pending submission from the left panel
3. Click **"Run AI Evaluation"** button first (to get the submission loaded with evaluation results)
4. Click **"Detect AI Content"** button
5. Wait for analysis to complete
6. View the results panel showing:
   - Risk Level (Low/Medium/High)
   - AI Probability (0-100%)
   - Recommendations
   - Submission Statistics (text length, word count)

#### Expected Output
```json
{
  "ai_detection_results": {
    "ai_probability": 0.45,
    "is_likely_ai": false,
    "confidence_score": 0.55,
    "analysis_details": {
      "raw_probability": 0.45,
      "model_name": "RADAR-Vicuna-7B",
      "threshold": 0.8
    }
  },
  "risk_assessment": {
    "risk_level": "Low",
    "risk_score": 1,
    "explanation": "The submission has a low risk of being AI-generated based on RADAR analysis."
  },
  "recommendations": [
    "This submission appears to be genuine human work.",
    "Continue with normal evaluation process."
  ],
  "submission_stats": {
    "text_length": 1234,
    "word_count": 156
  }
}
```

---

### Method 2: Direct API Testing (via curl/PowerShell)

#### Prerequisites
1. Backend server running
2. A student submission ID (UUID format)
3. PowerShell or curl installed

#### Using PowerShell
```powershell
# Get a pending submission first
$submissions = curl -Uri "http://localhost:8000/api/faculty/pending-submissions" `
  -ContentType "application/json" `
  -Verbose `
  -ErrorAction Stop | ConvertFrom-Json

# Get the first submission ID
$submissionId = $submissions[0].id
Write-Host "Testing with submission: $submissionId"

# Call the detect-ai endpoint
$response = curl -Uri "http://localhost:8000/api/faculty/submissions/$submissionId/detect-ai" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{}' `
  -Verbose

$response | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

#### Using curl (bash/PowerShell)
```bash
# Get pending submissions
curl http://localhost:8000/api/faculty/pending-submissions

# Detect AI in a specific submission
curl -X POST "http://localhost:8000/api/faculty/submissions/{SUBMISSION_ID}/detect-ai" \
  -H "Content-Type: application/json"
```

---

### Method 3: Python Script Testing

Create a test script: `test_ai_detection.py`

```python
import asyncio
import requests
import json
from pathlib import Path

# Configuration
BACKEND_URL = "http://localhost:8000"
FACULTY_API = f"{BACKEND_URL}/api/faculty"

async def test_ai_detection():
    """Test AI detection endpoint"""
    
    print("=" * 60)
    print("AI DETECTION TESTING")
    print("=" * 60)
    
    try:
        # Step 1: Get pending submissions
        print("\n1. Fetching pending submissions...")
        response = requests.get(f"{FACULTY_API}/pending-submissions")
        response.raise_for_status()
        submissions = response.json()
        
        if not submissions:
            print("   ❌ No pending submissions found")
            print("   💡 Create a student submission first")
            return
        
        print(f"   ✅ Found {len(submissions)} pending submission(s)")
        
        # Step 2: Test AI detection on first submission
        submission = submissions[0]
        submission_id = submission['id']
        
        print(f"\n2. Testing AI detection on submission: {submission_id}")
        print(f"   Student: {submission['student_id']}")
        print(f"   Assignment: {submission['assignment_id']}")
        
        response = requests.post(
            f"{FACULTY_API}/submissions/{submission_id}/detect-ai",
            json={}
        )
        response.raise_for_status()
        results = response.json()
        
        print("\n3. AI Detection Results:")
        print(f"   AI Probability: {results['ai_detection_results']['ai_probability']:.2%}")
        print(f"   Is Likely AI: {results['ai_detection_results']['is_likely_ai']}")
        print(f"   Risk Level: {results['risk_assessment']['risk_level']}")
        print(f"   Risk Score: {results['risk_assessment']['risk_score']}")
        print(f"\n   Explanation: {results['risk_assessment']['explanation']}")
        
        print(f"\n4. Recommendations:")
        for i, rec in enumerate(results['recommendations'], 1):
            print(f"   {i}. {rec}")
        
        print(f"\n5. Submission Statistics:")
        print(f"   Text Length: {results['submission_stats']['text_length']} characters")
        print(f"   Word Count: {results['submission_stats']['word_count']} words")
        
        print("\n" + "=" * 60)
        print("✅ AI Detection Test Completed Successfully")
        print("=" * 60)
        
        # Save results to file
        with open("ai_detection_results.json", "w") as f:
            json.dump(results, f, indent=2)
        print("\n💾 Full results saved to: ai_detection_results.json")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Failed to connect to backend")
        print("   💡 Make sure backend is running on http://localhost:8000")
    except requests.exceptions.HTTPError as e:
        print(f"\n❌ HTTP Error: {e.response.status_code}")
        print(f"   Response: {e.response.text}")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_ai_detection())
```

#### Run the test
```bash
cd backend
python ../test_ai_detection.py
```

---

### Method 4: Unit Testing (for development)

Create: `backend/tests/test_ai_detection.py`

```python
import pytest
from unittest.mock import Mock, patch
from backend.services.radar_service import RadarService

@pytest.mark.asyncio
async def test_detect_human_text():
    """Test detection of human-written text"""
    service = RadarService()
    
    human_text = """
    The greenhouse effect occurs when certain gases in Earth's atmosphere trap heat from the sun.
    This warming leads to climate change, affecting weather patterns, sea levels, and ecosystems.
    Scientists are working on solutions including renewable energy and carbon capture.
    """
    
    result = await service.detect_ai_content(human_text)
    
    assert "ai_probability" in result
    assert result["ai_probability"] < 0.8  # Should not be detected as AI
    assert result["is_likely_ai"] == False


@pytest.mark.asyncio
async def test_submission_analysis():
    """Test full submission analysis"""
    service = RadarService()
    
    submission_text = "Sample student submission text..."
    
    report = await service.analyze_submission(submission_text)
    
    assert "ai_detection_results" in report
    assert "risk_assessment" in report
    assert "recommendations" in report
    assert "submission_stats" in report
    assert report["submission_stats"]["text_length"] > 0
    assert report["submission_stats"]["word_count"] > 0


def test_risk_assessment():
    """Test risk assessment logic"""
    service = RadarService()
    
    # Test high risk
    risk_high = service._assess_risk(0.95)
    assert risk_high["risk_level"] == "High"
    assert risk_high["risk_score"] == 3
    
    # Test medium risk
    risk_medium = service._assess_risk(0.75)
    assert risk_medium["risk_level"] == "Medium"
    assert risk_medium["risk_score"] == 2
    
    # Test low risk
    risk_low = service._assess_risk(0.3)
    assert risk_low["risk_level"] == "Low"
    assert risk_low["risk_score"] == 1
```

#### Run tests
```bash
pytest backend/tests/test_ai_detection.py -v
```

---

## Risk Assessment Thresholds

| AI Probability | Risk Level | Action |
|---|---|---|
| < 0.7 | Low | Proceed with normal evaluation |
| 0.7 - 0.9 | Medium | Review submission carefully |
| > 0.9 | High | Flag for further investigation |

---

## Troubleshooting

### Issue: Model download timeout
**Solution**: Pre-download the model manually
```python
from transformers import AutoModelForSequenceClassification, AutoTokenizer
model = AutoModelForSequenceClassification.from_pretrained("TrustSafeAI/RADAR-Vicuna-7B")
tokenizer = AutoTokenizer.from_pretrained("TrustSafeAI/RADAR-Vicuna-7B")
```

### Issue: CUDA out of memory
**Solution**: The service automatically falls back to CPU if GPU memory is insufficient

### Issue: Endpoint returns 404
**Solution**: Verify submission ID exists and submission is in `pending_faculty` status
```bash
curl http://localhost:8000/api/faculty/pending-submissions
```

### Issue: "No pending submissions"
**Solution**: Create a student submission first:
1. Go to Student Workflow
2. Select assignment and submit
3. Then use Faculty Evaluation page to test

---

## Monitoring & Logging

Check backend logs for AI detection operations:
```bash
# Look for these log entries
grep -i "ai detection" backend.log
grep -i "radar" backend.log
```

---

## Next Steps

1. **Test with various submission types**: Human-written, AI-generated, mixed content
2. **Monitor model performance**: Track accuracy over time
3. **Adjust thresholds**: Fine-tune the 0.8 threshold if needed
4. **Database verification**: Check `student_submissions.ai_detection_results` column after testing

---

## Resources

- **RADAR Model**: https://huggingface.co/TrustSafeAI/RADAR-Vicuna-7B
- **Service Code**: `backend/services/radar_service.py`
- **Endpoint**: `backend/routers/faculty.py` (line ~629)
- **Frontend**: `frontend/src/pages/FacultyEvaluation.jsx` (detectAIContent function)
