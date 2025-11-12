# AI Detection Testing - Summary

## ✅ What I've Created

I've created **4 comprehensive testing resources** for the AI detection system:

### 1. **Quick Start Guide** (`AI_DETECTION_QUICK_START.md`)
   - 📖 Best place to start
   - 🎯 4 different testing methods (UI, Python, PowerShell, curl)
   - 🔍 Understanding results & thresholds
   - ⚠️ Troubleshooting tips

### 2. **Comprehensive Guide** (`AI_DETECTION_TEST_GUIDE.md`)
   - 📚 Deep dive documentation
   - 🏗️ Full architecture explanation
   - 🧪 4 testing methods with code examples
   - 🐛 Troubleshooting for each issue
   - 📊 Risk assessment thresholds
   - 🔗 Resource links

### 3. **Python Test Script** (`test_ai_detection.py`)
   - 🐍 Full-featured test automation
   - ✅ Connection validation
   - 📊 Detailed result display
   - 💾 Saves results to JSON file
   - 🎨 Pretty-printed output

### 4. **Quick Test Script** (`quick_test_ai.py`)
   - ⚡ Minimal, fast test
   - 🎨 Color-coded results
   - 📏 Just 3 steps
   - 💾 Auto-saves results

---

## 🚀 Fastest Way to Test (2 minutes)

### Prerequisites
1. Backend running: 
   ```powershell
   cd backend
   python start_evaluation_server.py
   ```

2. Have a student submission (create one via Student Workflow page)

### Then Run
```powershell
python quick_test_ai.py
```

**Done!** You'll see:
- ✅ Connection status
- ✅ AI probability (0-100%)
- ✅ Risk level (Low/Medium/High)
- ✅ Recommendations

---

## 🎯 Three Testing Approaches

### Approach 1: UI Testing (Visual)
```
Frontend → Faculty Evaluation page → Select submission → "Detect AI Content" button
```
**Best for**: Manual testing, seeing UI in action

### Approach 2: Automated Testing (Python)
```
python test_ai_detection.py
```
**Best for**: Batch testing, CI/CD integration, detailed logs

### Approach 3: API Testing (curl/PowerShell)
```powershell
curl http://localhost:8000/api/faculty/pending-submissions
curl -X POST http://localhost:8000/api/faculty/submissions/{id}/detect-ai
```
**Best for**: Manual API exploration, debugging

---

## 📊 How the System Works

```
Student Submission (text)
    ↓
RADAR-Vicuna-7B Model (HuggingFace)
    ↓
AI Probability (0.0 - 1.0)
    ↓
Risk Assessment:
  - Low (< 0.7)     → Human written
  - Medium (0.7-0.9) → Review carefully  
  - High (> 0.9)    → Likely AI
    ↓
Saved to Database (student_submissions.ai_detection_results)
```

---

## 🔑 Key Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/faculty/pending-submissions` | List submissions awaiting evaluation |
| POST | `/api/faculty/submissions/{id}/detect-ai` | Run AI detection analysis |

---

## 📋 What You Can Test

1. ✅ **Human-written text** → Low AI probability (< 0.7)
2. ✅ **AI-generated text** → High AI probability (> 0.8)
3. ✅ **Mixed content** → Medium probability (0.7-0.8)
4. ✅ **Different lengths** → Works with any submission size
5. ✅ **Database persistence** → Results saved to DB

---

## 🛠️ Files to Check

| File | Purpose | Key Info |
|---|---|---|
| `backend/services/radar_service.py` | Core detection logic | Lines 14-50 for model config |
| `backend/routers/faculty.py` | API endpoint | Line ~629 for detect-ai endpoint |
| `frontend/src/pages/FacultyEvaluation.jsx` | UI button | `detectAIContent` function ~line 168 |
| `database/models.py` | DB schema | `ai_detection_results` column in StudentSubmission |

---

## ⚡ Common Issues & Fixes

| Issue | Fix |
|---|---|
| **"No pending submissions"** | Create one in Student Workflow first |
| **"Connection refused"** | Start backend: `python start_evaluation_server.py` |
| **"Timeout"** | Normal on first run (model loads) - wait 1-2 min |
| **"404 Error"** | Invalid submission ID |
| **Slow GPU memory** | Falls back to CPU auto |

---

## 📈 Next Steps

1. ✅ Run `python quick_test_ai.py` (2 min)
2. ✅ Try UI testing in Faculty Evaluation page
3. ✅ Run `python test_ai_detection.py` for automation
4. ✅ Check database: query `ai_detection_results` column
5. ✅ Customize thresholds in `radar_service.py` if needed

---

## 🎓 Learning Resources

- **RADAR Model**: https://huggingface.co/TrustSafeAI/RADAR-Vicuna-7B
- **Transformers Library**: https://huggingface.co/docs/transformers/
- **PyTorch**: https://pytorch.org/
- **FastAPI**: https://fastapi.tiangolo.com/

---

## 💡 Pro Tips

1. **First run takes time** - Model downloads (~7GB) on first execution
2. **GPU optional** - Works fine on CPU if GPU not available
3. **Batch testing** - Modify test scripts to loop through multiple submissions
4. **Customize thresholds** - Edit threshold in `radar_service.py` line 43
5. **Monitor logs** - Check backend console for detailed debug info

---

## 🎯 Summary

You now have **multiple ways** to test AI detection:

- 📖 **Read**: `AI_DETECTION_QUICK_START.md` (best place to start)
- 🚀 **Quick Test**: `python quick_test_ai.py` (2 minutes)
- 🔬 **Full Test**: `python test_ai_detection.py` (automated)
- 🖥️ **UI Test**: Faculty Evaluation page "Detect AI Content" button
- 📚 **Learn**: `AI_DETECTION_TEST_GUIDE.md` (comprehensive guide)

**Recommendation**: Start with `quick_test_ai.py` to see it work, then explore other methods!
