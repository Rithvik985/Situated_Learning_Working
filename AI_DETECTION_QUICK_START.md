# AI Detection Testing - Quick Start Guide

## 📋 Summary

The AI detection system uses the **RADAR-Vicuna-7B** machine learning model to analyze student submissions and detect if they were AI-generated. Here are the **easiest ways to test it**:

---

## 🚀 Quick Start (5 minutes)

### Option 1: Via Frontend UI (Recommended - Easiest)

1. **Start the backend**:
   ```powershell
   cd backend
   python start_evaluation_server.py
   ```

2. **Start the frontend**:
   ```powershell
   cd frontend
   npm run dev
   ```

3. **In your browser**:
   - Navigate to http://localhost:5173 (or frontend URL)
   - Click **"Faculty Evaluation"** in the header
   - Select a pending submission from the left panel
   - Click **"Run AI Evaluation"** button first
   - Then click **"Detect AI Content"** button
   - View the results showing risk level, AI probability, and recommendations

### Option 2: Via Python Script (Best for Automation)

1. **Ensure backend is running** (from Option 1, step 1)

2. **Run the test script**:
   ```powershell
   python test_ai_detection.py
   ```

3. **Output will show**:
   - ✅ Connection status
   - ✅ List of pending submissions
   - ✅ AI detection results with probability
   - ✅ Risk level assessment
   - ✅ Recommendations
   - ✅ Results saved to JSON file

### Option 3: Via PowerShell Script (Windows)

1. **Ensure backend is running** (from Option 1, step 1)

2. **Run the PowerShell script**:
   ```powershell
   .\test_ai_detection.ps1
   ```

3. **Color-coded output** shows:
   - 🟢 Green = Low risk (human written)
   - 🟡 Yellow = Medium risk (mixed/suspicious)
   - 🔴 Red = High risk (likely AI generated)

### Option 4: Direct API with curl/PowerShell

```powershell
# Get pending submissions
$subs = curl -Uri "http://localhost:8000/api/faculty/pending-submissions" | ConvertFrom-Json

# Run AI detection on first submission
$subId = $subs[0].id
curl -Uri "http://localhost:8000/api/faculty/submissions/$subId/detect-ai" -Method POST | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

---

## 📊 Understanding the Results

### Example Output
```json
{
  "ai_detection_results": {
    "ai_probability": 0.35,           // 0-1 scale, 0=human, 1=AI
    "is_likely_ai": false,             // true if > 0.8
    "confidence_score": 0.65
  },
  "risk_assessment": {
    "risk_level": "Low",               // Low/Medium/High
    "risk_score": 1,                   // 1-3 scale
    "explanation": "The submission has a low risk of being AI-generated..."
  },
  "recommendations": [
    "This submission appears to be genuine human work.",
    "Continue with normal evaluation process."
  ],
  "submission_stats": {
    "text_length": 1234,               // Characters
    "word_count": 156                  // Words
  }
}
```

### Risk Levels
| AI Probability | Level | Action |
|---|---|---|
| 0.0 - 0.7 | 🟢 **Low** | Proceed normally |
| 0.7 - 0.9 | 🟡 **Medium** | Review carefully |
| 0.9 - 1.0 | 🔴 **High** | Investigate further |

---

## ⚠️ Important Notes

1. **First Run**: The model (~7B parameters) downloads on first use - this takes time
2. **GPU Support**: Uses GPU if available, falls back to CPU automatically
3. **Timeout**: AI detection may take 30-120 seconds depending on submission length
4. **No Student Submissions?**: Create one first by going to Student Workflow → Select Assignment → Submit

---

## 🔍 Where to Find Things

| Component | Location | Purpose |
|---|---|---|
| **Service Code** | `backend/services/radar_service.py` | Core AI detection logic |
| **Endpoint** | `backend/routers/faculty.py` line ~629 | API endpoint definition |
| **Frontend Button** | `frontend/src/pages/FacultyEvaluation.jsx` | "Detect AI Content" button |
| **Test Guide** | `AI_DETECTION_TEST_GUIDE.md` | Comprehensive testing guide |
| **Python Test** | `test_ai_detection.py` | Automated test script |
| **PowerShell Test** | `test_ai_detection.ps1` | Windows PowerShell test |
| **Database** | `student_submissions.ai_detection_results` | Results stored as JSONB |

---

## 🛠️ Troubleshooting

| Issue | Solution |
|---|---|
| **"No pending submissions"** | Go to Student Workflow → Submit assignment first |
| **Connection refused** | Backend not running: `python start_evaluation_server.py` |
| **Timeout after 60s** | Model is processing - this is normal first time |
| **404 Error** | Invalid submission ID - check submission exists |
| **GPU out of memory** | Falls back to CPU automatically |

---

## 📁 Test Files Created

```
Situated_Learning/
├── test_ai_detection.py              ← Python script (recommended)
├── test_ai_detection.ps1             ← PowerShell script
├── AI_DETECTION_TEST_GUIDE.md        ← Full documentation
└── ai_detection_results_*.json       ← Generated test results
```

---

## 🎯 Recommended Testing Flow

1. ✅ **Start backend** → `python start_evaluation_server.py`
2. ✅ **Create student submission** → Student Workflow page
3. ✅ **Run test** → `python test_ai_detection.py`
4. ✅ **View in UI** → Faculty Evaluation → Click "Detect AI Content"
5. ✅ **Check database** → Query `student_submissions.ai_detection_results`

---

## 🚀 Next Steps

- **Batch Testing**: Modify `test_ai_detection.py` to test multiple submissions
- **Threshold Tuning**: Adjust AI probability threshold in `radar_service.py`
- **Model Switching**: Try different detection models from HuggingFace
- **Analytics**: Track AI detection rates across all submissions

---

**Need more help?** See `AI_DETECTION_TEST_GUIDE.md` for detailed documentation.
