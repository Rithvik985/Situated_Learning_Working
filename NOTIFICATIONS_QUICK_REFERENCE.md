# 🔔 Notification System - Quick Reference Card

## 3-Step Integration

### Step 1: Import
```jsx
import { useNotifications } from '../hooks/useNotifications'
import NotificationContainer from '../components/NotificationContainer'
```

### Step 2: Initialize
```jsx
const { notifications, showNotification, removeNotification } = useNotifications()
```

### Step 3: Use
```jsx
<NotificationContainer notifications={notifications} onRemove={removeNotification} />
showNotification('Success!', 'success')
```

---

## Notification Types

```
Success (Green)    | Error (Red)        | Warning (Orange)   | Info (Blue)
✅ Complete!      | ❌ Failed!         | ⚠️ Review this     | ℹ️ Loading...

showNotification('Done!', 'success')
showNotification('Error!', 'error')
showNotification('Warning!', 'warning')
showNotification('Info!', 'info')
```

---

## Common Patterns

### API Call with Notifications
```jsx
const handleSubmit = async () => {
  showNotification('📤 Submitting...', 'info', 0)
  try {
    const result = await fetch(url)
    showNotification('✅ Submitted!', 'success')
  } catch (error) {
    showNotification(`❌ Error: ${error.message}`, 'error')
  }
}
```

### Form Validation
```jsx
if (!email) {
  showNotification('Email is required', 'warning')
  return
}
```

### Long Operation
```jsx
showNotification('🔄 Processing (this may take a while)...', 'info')
await processLongTask()
showNotification('✅ Processing complete!', 'success')
```

---

## Duration Options

```javascript
// Auto-dismiss after 5 seconds (default)
showNotification('Message', 'info')
showNotification('Message', 'info', 5000)

// Auto-dismiss after 10 seconds
showNotification('Message', 'warning', 10000)

// Don't auto-dismiss
showNotification('Message', 'error', 0)
```

---

## Real Examples from Your App

### ✅ Already Implemented

**StudentEvaluation.jsx - Analyze:**
```jsx
showNotification('📊 Analyzing...', 'info', 0)  // Start
showNotification('✅ Analysis complete!', 'success')  // Success
showNotification(`❌ Analysis failed: ${e.message}`, 'error')  // Error
```

**StudentEvaluation.jsx - Submit:**
```jsx
showNotification('📤 Submitting...', 'info', 0)  // Start
showNotification('✅ Submitted!', 'success')  // Success
showNotification(`❌ Submission failed: ${e.message}`, 'error')  // Error
```

### 🔄 Add to Other Pages

**FacultyEvaluation.jsx - Evaluate:**
```jsx
showNotification('⏳ Evaluating...', 'info', 0)
// ... evaluation logic ...
showNotification('✅ Evaluation complete!', 'success')
```

**FacultyEvaluation.jsx - Finalize:**
```jsx
showNotification('💾 Finalizing...', 'info', 0)
// ... finalize logic ...
showNotification('✅ Finalized!', 'success')
```

**FacultyEvaluation.jsx - AI Detection:**
```jsx
showNotification('🤖 Detecting AI...', 'info', 0)
// ... detection logic ...
showNotification('✅ Detection complete!', 'success')
```

**FacultyDashboard.jsx - Load:**
```jsx
showNotification('📊 Loading dashboard...', 'info', 0)
// ... load logic ...
showNotification('✅ Dashboard loaded!', 'success')
```

---

## Files Reference

| File | Location | Purpose |
|------|----------|---------|
| Component | `frontend/src/components/NotificationContainer.jsx` | Display notifications |
| Styles | `frontend/src/styles/notifications.css` | Styling & animations |
| Hook | `frontend/src/hooks/useNotifications.js` | State management |
| Guide | `NOTIFICATIONS_GUIDE.md` | Full documentation |
| Implementation | `NOTIFICATIONS_IMPLEMENTATION.md` | Integration details |

---

## Notification Positions

Currently set to **top-right** (you can change in `notifications.css`):

```css
.notification-container {
  top: 20px;    /* Distance from top */
  right: 20px;  /* Distance from right */
}
```

Change to:
- **Top-left**: `top: 20px; left: 20px;`
- **Bottom-right**: `bottom: 20px; right: 20px;`
- **Bottom-left**: `bottom: 20px; left: 20px;`

---

## Features

✅ Auto-dismiss (customizable)
✅ Manual close button
✅ 4 types (success, error, warning, info)
✅ Smooth animations
✅ Mobile responsive
✅ Stackable (multiple at once)
✅ Accessible (ARIA labels)

---

## Testing

1. Go to StudentEvaluation page ✅
2. Click "Analyze" button
3. You should see:
   - Blue info notification: "📊 Analyzing..."
   - Then green success: "✅ Analysis complete!"
4. Try submitting to see more notifications!

---

## Next: Add to Other Pages

```jsx
// Copy-paste for each page:

import { useNotifications } from '../hooks/useNotifications'
import NotificationContainer from '../components/NotificationContainer'

const MyComponent = () => {
  const { notifications, showNotification, removeNotification } = useNotifications()

  return (
    <>
      <NotificationContainer notifications={notifications} onRemove={removeNotification} />
      {/* Your content */}
    </>
  )
}
```

Then wrap your async operations:
```jsx
showNotification('Starting...', 'info', 0)
try {
  // Your code
  showNotification('Done!', 'success')
} catch (error) {
  showNotification(`Error: ${error.message}`, 'error')
}
```

---

## Emojis for Notifications

```
✅ Success/Complete
❌ Error/Failed
📊 Analyzing/Loading
📤 Submitting/Uploading
⏳ Processing/Waiting
🤖 AI/Detection
💾 Saving
🔄 Refreshing
📈 Generating
⚠️ Warning
ℹ️ Information
🎉 Celebration
```

---

**That's it! You have a complete notification system ready to use!** 🎉
