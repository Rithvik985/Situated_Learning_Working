# AI Detection Testing Script for PowerShell
# Usage: ./test_ai_detection.ps1

$BACKEND_URL = "http://localhost:8000"
$FACULTY_API = "$BACKEND_URL/api/faculty"

function Write-Header {
    param([string]$Title)
    Write-Host "`n" + ("=" * 70) -ForegroundColor Cyan
    Write-Host "  $Title" -ForegroundColor Cyan
    Write-Host ("=" * 70) -ForegroundColor Cyan
}

function Write-Section {
    param([string]$Title)
    Write-Host "`n" + ("─" * 70) -ForegroundColor Yellow
    Write-Host "  $Title" -ForegroundColor Yellow
    Write-Host ("─" * 70) -ForegroundColor Yellow
}

Write-Header "AI DETECTION TESTING"

try {
    # Step 1: Check backend connectivity
    Write-Section "Step 1: Checking Backend Connectivity"
    
    try {
        $null = Invoke-WebRequest "$BACKEND_URL/docs" -TimeoutSec 5 -ErrorAction Stop
        Write-Host "✅ Backend is running on $BACKEND_URL" -ForegroundColor Green
    } catch {
        Write-Host "❌ Cannot connect to backend at $BACKEND_URL" -ForegroundColor Red
        Write-Host "   💡 Start backend with: python start_evaluation_server.py" -ForegroundColor Yellow
        exit 1
    }
    
    # Step 2: Get pending submissions
    Write-Section "Step 2: Fetching Pending Submissions"
    
    try {
        $response = Invoke-WebRequest -Uri "$FACULTY_API/pending-submissions" `
            -Method Get `
            -ContentType "application/json" `
            -TimeoutSec 10 `
            -ErrorAction Stop
        $submissions = $response.Content | ConvertFrom-Json
    } catch {
        Write-Host "❌ Failed to fetch submissions" -ForegroundColor Red
        Write-Host $_.Exception.Message -ForegroundColor Red
        exit 1
    }
    
    if ($submissions.Count -eq 0) {
        Write-Host "❌ No pending submissions found" -ForegroundColor Red
        Write-Host "   💡 Create a student submission first:" -ForegroundColor Yellow
        Write-Host "      1. Go to Student Workflow page" -ForegroundColor Yellow
        Write-Host "      2. Select an assignment" -ForegroundColor Yellow
        Write-Host "      3. Submit your response" -ForegroundColor Yellow
        exit 1
    }
    
    Write-Host "✅ Found $($submissions.Count) pending submission(s)" -ForegroundColor Green
    Write-Host "`n   Submissions:" -ForegroundColor Gray
    for ($i = 0; $i -lt $submissions.Count; $i++) {
        $sub = $submissions[$i]
        Write-Host "   $($i + 1). ID: $($sub.id)" -ForegroundColor Gray
        Write-Host "      Student: $($sub.student_id)" -ForegroundColor Gray
        Write-Host "      Status: $($sub.evaluation_status)" -ForegroundColor Gray
    }
    
    # Step 3: Test AI detection
    $submission = $submissions[0]
    $submission_id = $submission.id
    
    Write-Section "Step 3: Running AI Detection Analysis"
    Write-Host "Testing on submission: $submission_id" -ForegroundColor Gray
    Write-Host "Student: $($submission.student_id)" -ForegroundColor Gray
    
    try {
        $response = Invoke-WebRequest -Uri "$FACULTY_API/submissions/$submission_id/detect-ai" `
            -Method Post `
            -ContentType "application/json" `
            -Body "{}" `
            -TimeoutSec 120 `
            -ErrorAction Stop
        $results = $response.Content | ConvertFrom-Json
    } catch {
        if ($_.Exception.Message -match "timeout") {
            Write-Host "❌ Request timed out - AI detection might be slow" -ForegroundColor Red
            Write-Host "   💡 This can happen on first run (model loading)" -ForegroundColor Yellow
        } else {
            Write-Host "❌ HTTP Error: $($_.Exception.Message)" -ForegroundColor Red
        }
        exit 1
    }
    
    # Step 4: Display results
    Write-Section "Step 4: AI Detection Results"
    
    $aiResults = $results.'ai_detection_results'
    $riskAssessment = $results.'risk_assessment'
    $recommendations = $results.'recommendations'
    $stats = $results.'submission_stats'
    
    $aiProb = $aiResults.ai_probability
    $riskLevel = $riskAssessment.risk_level
    
    # Color code based on risk
    if ($riskLevel -eq "High") {
        $riskColor = "Red"
    } elseif ($riskLevel -eq "Medium") {
        $riskColor = "Yellow"
    } else {
        $riskColor = "Green"
    }
    
    Write-Host "`n📊 AI Detection Metrics:" -ForegroundColor Cyan
    Write-Host "   • AI Probability: $('{0:P1}' -f $aiProb)" -ForegroundColor Gray
    Write-Host "   • Is Likely AI: $($aiResults.is_likely_ai)" -ForegroundColor Gray
    Write-Host "   • Confidence: $('{0:P1}' -f $aiResults.confidence_score)" -ForegroundColor Gray
    
    Write-Host "`n⚠️  Risk Assessment:" -ForegroundColor Cyan
    Write-Host "   • Risk Level: $riskLevel" -ForegroundColor $riskColor
    Write-Host "   • Risk Score: $($riskAssessment.risk_score)/3" -ForegroundColor Gray
    Write-Host "   • Note: $($riskAssessment.explanation)" -ForegroundColor Gray
    
    Write-Host "`n💡 Recommendations:" -ForegroundColor Cyan
    if ($recommendations) {
        $recommendations | ForEach-Object { Write-Host "   • $_" -ForegroundColor Gray }
    } else {
        Write-Host "   (No specific recommendations)" -ForegroundColor Gray
    }
    
    Write-Host "`n📈 Submission Statistics:" -ForegroundColor Cyan
    Write-Host "   • Text Length: $($stats.text_length):N0 characters" -ForegroundColor Gray
    Write-Host "   • Word Count: $($stats.word_count):N0 words" -ForegroundColor Gray
    
    # Save results
    Write-Section "Step 5: Saving Results"
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $outputFile = "ai_detection_results_$timestamp.json"
    
    $results | ConvertTo-Json -Depth 10 | Out-File $outputFile -Encoding UTF8
    Write-Host "✅ Results saved to: $outputFile" -ForegroundColor Green
    
    # Summary
    Write-Header "TEST COMPLETED SUCCESSFULLY ✅"
    Write-Host "`n   Model: RADAR-Vicuna-7B" -ForegroundColor Green
    Write-Host "   Submission: $submission_id" -ForegroundColor Green
    Write-Host "   AI Probability: $('{0:P1}' -f $aiProb)" -ForegroundColor Green
    Write-Host "   Risk Level: $riskLevel" -ForegroundColor $riskColor
    
} catch {
    Write-Header "ERROR ❌"
    Write-Host "`n   $($_.Exception.GetType().Name): $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
