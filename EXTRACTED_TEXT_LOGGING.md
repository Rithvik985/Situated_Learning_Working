# 📝 Extracted Text Logging Guide

## Overview
The system now logs extracted text at three key points during the submission workflow. Logs show either:
- **Preview mode** (default): First 200 characters + indication of full length
- **Full mode** (when env var enabled): Complete extracted text content

---

## 🔧 Control via Environment Variable

### Enable Full Text Logging
Set the environment variable and restart your backend server:

**Windows PowerShell:**
```powershell
$env:SHOW_FULL_EXTRACTED_LOGS = 'true'
# Then restart your backend (however you start it)
```

**Linux/Mac:**
```bash
export SHOW_FULL_EXTRACTED_LOGS=true
# Then restart backend
```

**Docker/Docker-Compose:**
Add to your `docker-compose.yml`:
```yaml
services:
  backend:
    environment:
      - SHOW_FULL_EXTRACTED_LOGS=true
```

**Acceptable values:**
- `true`, `1`, `yes` → Enable full text logging
- `false`, `0`, `no` (or not set) → Preview mode (default)

---

## 📍 Three Logging Points

### 1. **After Upload & OCR Processing** (`/submissions/upload`)
Logs extracted text **immediately after** the file is processed and text is extracted.

**Preview mode (default):**
```
[EXTRACTED TEXT] File: MSD_SLA_Jayakumar_2023HT30252.pdf, Submission: 5d6696a5-08e0-40a9-a3ec-622c791ddb77, Length: 15847 chars, Preview: 'Chapter 1: Introduction to Software Architecture\n\nSoftware...'
```

**Full mode (SHOW_FULL_EXTRACTED_LOGS=true):**
```
[EXTRACTED TEXT - FULL] File: MSD_SLA_Jayakumar_2023HT30252.pdf, Submission: 5d6696a5-08e0-40a9-a3ec-622c791ddb77, Length: 15847 chars
Content:
Chapter 1: Introduction to Software Architecture

Software architecture is the foundational set of structures needed to reason about...
(full text)
```

---

### 2. **When Retrieving Submissions** (`/assignments/{assignment_id}/submissions`)
Logs stored extracted text for **each submission** when the assignment is fetched.

**Preview mode (default):**
```
[STORED TEXT] Submission: 5d6696a5-08e0-40a9-a3ec-622c791ddb77, Length: 15847 chars, Preview: 'Chapter 1: Introduction to Software Architecture\n\nSoftware...'
```

**Full mode (SHOW_FULL_EXTRACTED_LOGS=true):**
```
[STORED TEXT - FULL] Submission: 5d6696a5-08e0-40a9-a3ec-622c791ddb77, Length: 15847 chars
Content:
(full text)
```

---

### 3. **Before Evaluation** (`/evaluate`)
Logs the extracted text **right before** it's sent to the evaluation engine.

**Preview mode (default):**
```
[EVALUATION TEXT] Submission: 5d6696a5-08e0-40a9-a3ec-622c791ddb77, Length: 15847 chars, Preview: 'Chapter 1: Introduction to Software Architecture\n\nSoftware...'
```

**Full mode (SHOW_FULL_EXTRACTED_LOGS=true):**
```
[EVALUATION TEXT - FULL] Submission: 5d6696a5-08e0-40a9-a3ec-622c791ddb77, Length: 15847 chars
Content:
(full text)
```

---

## 📊 Log Format Reference

All extracted text logs follow this pattern:

```
[EXTRACTED TEXT] File: <filename>, Submission: <UUID>, Length: <num> chars, Preview: '<first 200 chars>'
```

or

```
[EXTRACTED TEXT - FULL] File: <filename>, Submission: <UUID>, Length: <num> chars
Content:
<full text>
```

**Tags used:**
- `[EXTRACTED TEXT]` → Text just extracted from file
- `[STORED TEXT]` → Text retrieved from database
- `[EVALUATION TEXT]` → Text being sent to evaluation engine

---

## ⚠️ Security & Privacy Considerations

### Default Behavior (Recommended for Production)
- Only **first 200 characters** are logged
- Character count is logged (helps debug truncation issues)
- Logs remain compact and manageable
- **Safe for production** — minimal risk of leaking large documents

### Full Text Mode (Development/Debugging Only)
- **Entire extracted text is logged**
- Use only for short-term debugging
- **NOT recommended for production** — may leak sensitive student content
- Automatically disabled if env var is not explicitly set

### Best Practice
- **Production:** Leave `SHOW_FULL_EXTRACTED_LOGS` unset or set to `false`
- **Development:** Set to `true` only when debugging specific submissions
- **Sensitive data:** Review student submissions before enabling full logging

---

## 🔍 Troubleshooting

### Logs Not Appearing?

**Problem:** No extracted text logs show up after upload.

**Solutions:**

1. **Check logger level** - Ensure your logging configuration captures INFO level:
   ```python
   # In backend/routers/evaluation.py or your logging config:
   logger.setLevel(logging.DEBUG)  # or INFO minimum
   ```

2. **Verify extraction succeeded** - Look for `SUCCESS` in submission processor logs:
   ```
   services.submission_processor - INFO - Successfully processed ...
   ```

3. **Check environment variable** - The default is preview mode, so you should see logs WITHOUT setting the env var

4. **Increase verbosity temporarily:**
   ```bash
   # Add to your logging config to see all INFO-level logs
   logging.basicConfig(level=logging.INFO)
   ```

---

## 📋 Examples

### Example 1: Upload with Preview Logs
```
2025-11-12 12:09:00,075 - evaluation_server.router - INFO - [EXTRACTED TEXT] File: MSD_SLA_Jayakumar_2023HT30252.pdf, Submission: 5d6696a5-08e0-40a9-a3ec-622c791ddb77, Length: 15847 chars, Preview: 'Chapter 1: Introduction to Software Architecture...'

2025-11-12 12:09:00,263 - evaluation_server.router - INFO - SUBMISSION DETAILS:
2025-11-12 12:09:00,269 - evaluation_server.router - INFO - → submission_id: '5d6696a5-08e0-40a9-a3ec-622c791ddb77'
```

### Example 2: Retrieving Submissions with Stored Text Logs
```
2025-11-12 12:09:15,200 - evaluation_server.router - INFO - [STORED TEXT] Submission: 5d6696a5-08e0-40a9-a3ec-622c791ddb77, Length: 15847 chars, Preview: 'Chapter 1: Introduction to Software Architecture...'

2025-11-12 12:09:15,201 - evaluation_server.router - INFO - Retrieved 5 submissions for assignment 02d65c09-9f6b-4a51-a5a6-4f0bf7bc950e
```

### Example 3: Evaluation with Full Logs (SHOW_FULL_EXTRACTED_LOGS=true)
```
2025-11-12 12:09:30,500 - evaluation_server.router - INFO - [EVALUATION TEXT - FULL] Submission: 5d6696a5-08e0-40a9-a3ec-622c791ddb77, Length: 15847 chars
2025-11-12 12:09:30,501 - evaluation_server.router - INFO - Content:
Chapter 1: Introduction to Software Architecture

Software architecture is the foundational set of structures needed to reason about a software system.

It encompasses the set of significant decisions made on how the software is organized.

[... full text continues ...]
```

---

## 🚀 Quick Setup

### For Development (See Full Text)
```powershell
# Windows
$env:SHOW_FULL_EXTRACTED_LOGS = 'true'
python backend/main.py

# Linux/Mac
export SHOW_FULL_EXTRACTED_LOGS=true
python backend/main.py
```

### For Production (Preview Only)
```powershell
# Windows - default (no env var needed)
python backend/main.py

# Linux/Mac - default (no env var needed)
python backend/main.py
```

---

## 📈 What to Look For

### Healthy Extraction
```
INFO - [EXTRACTED TEXT] ... Length: 15847 chars, Preview: 'Chapter 1: Introduction...'
```
✅ Text extracted successfully, preview shows meaningful content

### Empty Extraction
```
WARNING - [EXTRACTED TEXT] File: ... extracted but text is empty or None
```
⚠️ File processed but no text extracted (possible OCR failure)

### Extraction Error
```
ERROR - [EXTRACTED TEXT] File: ... Error during extraction: ...
```
❌ Something failed during OCR/text extraction

---

## 📞 Support

If extracted text logs aren't appearing:
1. Check that the file was uploaded successfully (look for "Uploaded ... to MinIO" logs)
2. Verify `SHOW_FULL_EXTRACTED_LOGS` is set correctly if you expect full text
3. Check logger level is set to INFO or DEBUG
4. Ensure text extraction succeeded (look for "Successfully processed" message)

For questions, check the logs with keyword: `[EXTRACTED TEXT]`, `[STORED TEXT]`, or `[EVALUATION TEXT]`
