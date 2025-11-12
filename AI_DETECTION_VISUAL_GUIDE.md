# AI Detection System - Visual Reference

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (React)                          │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  FacultyEvaluation.jsx                                   │   │
│  │  ┌─────────────────────────────────────────────────┐    │   │
│  │  │ "Detect AI Content" Button                       │    │   │
│  │  │ Click → detectAIContent()                        │    │   │
│  │  │ Shows: Risk Level, AI %, Recommendations         │    │   │
│  │  └─────────────────────────────────────────────────┘    │   │
│  └──────────────────────────────────────────────────────────┘   │
└──────────────────────┬──────────────────────────────────────────┘
                       │ HTTP POST
                       ↓
┌──────────────────────────────────────────────────────────────────┐
│                      BACKEND (FastAPI)                           │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  faculty.py Router                                       │   │
│  │  @router.post("/submissions/{id}/detect-ai")            │   │
│  │  ↓                                                       │   │
│  │  Query submission by ID                                 │   │
│  │  ↓                                                       │   │
│  │  Call radar_service.analyze_submission(text)            │   │
│  │  └─────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  radar_service.py (ML Service)                           │   │
│  │  ┌─────────────────────────────────────────────────┐    │   │
│  │  │ RadarService.detect_ai_content()                │    │   │
│  │  │ - Load RADAR-Vicuna-7B from HuggingFace        │    │   │
│  │  │ - Tokenize submission text                      │    │   │
│  │  │ - Run through model                             │    │   │
│  │  │ - Get AI probability (0-1)                      │    │   │
│  │  │ - Assess risk (Low/Medium/High)                 │    │   │
│  │  │ - Generate recommendations                      │    │   │
│  │  └─────────────────────────────────────────────────┘    │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ↓                                                               │
│  Save results to database                                       │
└──────────────────────┬──────────────────────────────────────────┘
                       │ JSON Response
                       ↓
┌──────────────────────────────────────────────────────────────────┐
│                      DATABASE (PostgreSQL)                       │
│  student_submissions                                             │
│  ├── id (UUID)                                                   │
│  ├── student_id                                                  │
│  ├── content                                                     │
│  └── ai_detection_results (JSONB)  ←─ Results stored here       │
│      {                                                           │
│        "ai_detection_results": {...},                           │
│        "risk_assessment": {...},                                │
│        "recommendations": [...],                                │
│        "submission_stats": {...}                                │
│      }                                                           │
└──────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Data Flow Diagram

```
START
  │
  ├─→ Student submits assignment
  │     (Student Workflow page)
  │
  ├─→ Submission stored in database
  │     (status: "pending_faculty")
  │
  ├─→ Faculty opens Faculty Evaluation page
  │     │
  │     └─→ Select submission from list
  │           │
  │           ├─→ Click "Run AI Evaluation"
  │           │     (Optional: for LLM rubric scoring)
  │           │
  │           └─→ Click "Detect AI Content"  ←─ YOU ARE HERE
  │                 │
  │                 ├─→ POST /submissions/{id}/detect-ai
  │                 │     │
  │                 │     ├─→ Load RADAR model
  │                 │     │
  │                 │     ├─→ Analyze submission text
  │                 │     │
  │                 │     ├─→ Get AI probability (0-1)
  │                 │     │
  │                 │     ├─→ Assess risk level
  │                 │     │
  │                 │     └─→ Generate recommendations
  │                 │
  │                 ├─→ Save to database
  │                 │
  │                 └─→ Display results in UI
  │                       ├─ Risk Level (🟢🟡🔴)
  │                       ├─ AI Probability %
  │                       ├─ Recommendations
  │                       └─ Submission stats
  │
  └─→ Faculty decides next action based on results
        ├─ Continue evaluation (if human-written)
        ├─ Review carefully (if medium risk)
        └─ Investigate further (if high risk)

END
```

---

## 🧪 Testing Methods Comparison

```
┌─────────────┬──────────────┬─────────┬──────────┬────────────┐
│ Method      │ Speed        │ Ease    │ Detailed │ Automation │
├─────────────┼──────────────┼─────────┼──────────┼────────────┤
│ UI Testing  │ ⚡ Medium    │ 🟢 Easy │ 🟡 OK    │ ❌ No      │
│ Python      │ ⚡ Fast      │ 🟢 Easy │ 🟢 Full  │ ✅ Yes     │
│ Quick Test  │ ⚡⚡ Very Fast│ 🟢 Easy │ 🟡 OK    │ ✅ Yes     │
│ PowerShell  │ ⚡ Fast      │ 🟢 Easy │ 🟢 Good  │ ✅ Yes     │
│ curl        │ ⚡ Instant   │ 🔴 Hard │ 🔴 Raw   │ ✅ Yes     │
└─────────────┴──────────────┴─────────┴──────────┴────────────┘

RECOMMENDED: Start with "UI Testing" then use "Python" for automation
```

---

## 📊 Result Interpretation Chart

```
AI Probability (0.0 ───────────────────── 1.0)

0.0          0.3          0.5          0.7          0.9          1.0
│            │            │            │            │            │
├────🟢─LOW────┤────🟡─MEDIUM────┤────🔴─HIGH────┤
│            │            │            │            │            │
Definitely   Likely       Uncertain    Probably     Almost       Definitely
Human ← → ← → ← → Borderline ← → ← → AI

Actions:
🟢 LOW        Continue normal evaluation
🟡 MEDIUM     Review submission carefully, look for AI patterns
🔴 HIGH       Investigate further, consider request for proof/resubmission
```

---

## 🎯 Risk Assessment Matrix

```
┌──────────────┬────────────────┬─────────────┬────────────────┐
│ Risk Level   │ AI Probability │ Risk Score  │ Action         │
├──────────────┼────────────────┼─────────────┼────────────────┤
│ 🟢 LOW       │ < 0.7          │ 1/3         │ ✅ Approve     │
│ 🟡 MEDIUM    │ 0.7 - 0.9      │ 2/3         │ ⚠️ Review      │
│ 🔴 HIGH      │ > 0.9          │ 3/3         │ 🔍 Investigate │
└──────────────┴────────────────┴─────────────┴────────────────┘
```

---

## 🚀 Quick Start Flowchart

```
                    START
                      │
                      ↓
              ┌─────────────────┐
              │ Start Backend?  │
              └────────┬────────┘
                       │
        ┌──────────────┴──────────────┐
        │                             │
        ↓                             ↓
   ✅ Yes                         ❌ No
        │                             │
        ↓                             ↓
   Running?            cd backend
        │              python start_evaluation_server.py
        ↓                             │
        │ ← ← ← ← ← ← ← ← ← ← ← ← ← ┘
        │
        ↓
   ┌─────────────────────────┐
   │ Run: python quick_test_ai.py
   └────────────┬────────────┘
                │
     ┌──────────┴──────────┐
     ↓                     ↓
  ✅ Success          ❌ Error
     │                     │
     ↓                     ↓
   View Results       Check Error
     │                Message
     ↓                     │
 Check JSON            Fix Issue
     │                     │
     ↓                     ↓
  Try UI                 Retry
     │                     │
     ↓                     ↓
Faculty Evaluation   python quick_test_ai.py
"Detect AI Content"      │
     │             ← ← ← ┘
     ↓
   SUCCESS! 🎉

Key Files:
├─ quick_test_ai.py ........... Use this first!
├─ test_ai_detection.py ....... Full featured test
└─ AI_DETECTION_QUICK_START.md  Read this for help
```

---

## 📁 File Structure

```
Situated_Learning/
│
├── 📄 AI_DETECTION_README.md
│   └─ This is the main overview (you are here)
│
├── 📄 AI_DETECTION_QUICK_START.md
│   └─ Quick start for 4 testing methods
│
├── 📄 AI_DETECTION_TEST_GUIDE.md
│   └─ Comprehensive testing guide
│
├── 🐍 quick_test_ai.py
│   └─ Minimal test (RUN THIS FIRST!)
│
├── 🐍 test_ai_detection.py
│   └─ Full-featured test with detailed output
│
├── 🔧 test_ai_detection.ps1
│   └─ PowerShell test for Windows
│
└── backend/
    ├── services/
    │   └── 🧠 radar_service.py ............ AI detection service
    │       ├─ RadarService class
    │       └─ RADAR-Vicuna-7B model
    │
    └── routers/
        └── 🛣️ faculty.py ................. API endpoints
            └─ @router.post("/submissions/{id}/detect-ai")
```

---

## 🔗 API Contract

### Endpoint
```
POST /api/faculty/submissions/{submission_id}/detect-ai
```

### Request
```json
{}
```

### Response (Success)
```json
{
  "ai_detection_results": {
    "ai_probability": 0.35,
    "is_likely_ai": false,
    "confidence_score": 0.65,
    "analysis_details": {
      "raw_probability": 0.35,
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

### Errors
```json
// 404 - Submission not found
{ "detail": "Submission not found" }

// 500 - AI analysis failed
{ "detail": "Failed to analyze submission for AI content" }

// 500 - Model load failed
{ "detail": "Failed to initialize AI detection model" }
```

---

## ⏱️ Performance Expectations

```
Operation                    Time
┌────────────────────────────────────────┐
│ First run (model download)    1-5 min  │
│ Subsequent runs               30-120 s │
│ Short submission (< 500 words) 30 s    │
│ Medium submission (500-2000)   60 s    │
│ Long submission (> 2000)      120 s    │
│ Database save                  < 1 s   │
└────────────────────────────────────────┘
```

---

## 🎓 Legend

```
🟢 = Good / Low risk / Proceed
🟡 = Warning / Medium risk / Review
🔴 = Alert / High risk / Investigate

✅ = Success / Done
❌ = Error / Failed
⚠️  = Warning / Need attention
ℹ️  = Information / Note

⚡ = Fast
🧠 = Machine Learning
🛣️ = Route/Endpoint
📄 = Document
🐍 = Python
🔧 = Configuration/Tool
```

---

## 🎯 Next Steps

1. **Read**: `AI_DETECTION_QUICK_START.md`
2. **Test**: `python quick_test_ai.py`
3. **Explore**: Try other test methods
4. **Integrate**: Add to your CI/CD pipeline
5. **Monitor**: Track results in database

---

**Happy Testing!** 🚀
