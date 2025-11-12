# 🔔 Notification System Guide

## Overview

I've created a **reusable notification system** that you can use across all pages. Notifications automatically appear when buttons are clicked, operations complete, errors occur, etc.

---

## 📁 Files Created

### 1. **NotificationContainer.jsx** (Component)
```
frontend/src/components/NotificationContainer.jsx
```
- Displays notifications in the top-right corner
- Supports 4 types: success, error, warning, info
- Auto-dismisses after 5 seconds (customizable)
- Manual close button on each notification

### 2. **notifications.css** (Styles)
```
frontend/src/styles/notifications.css
```
- Beautiful notification styling
- Color-coded by type
- Smooth animations (slide in/out)
- Mobile responsive

### 3. **useNotifications.js** (Hook)
```
frontend/src/hooks/useNotifications.js
```
- Custom React hook
- Easy to use in any component
- Auto-manages notification lifecycle

---

## 🚀 How to Use

### Step 1: Import the Hook and Component

```jsx
import { useNotifications } from '../hooks/useNotifications'
import NotificationContainer from '../components/NotificationContainer'
```

### Step 2: Initialize in Your Component

```jsx
const MyComponent = () => {
  const { notifications, showNotification, removeNotification } = useNotifications()

  return (
    <>
      {/* Add notification container */}
      <NotificationContainer 
        notifications={notifications} 
        onRemove={removeNotification} 
      />

      {/* Rest of your component */}
    </>
  )
}
```

### Step 3: Show Notifications When Needed

```jsx
// Success
showNotification('Assignment saved successfully!', 'success')

// Error
showNotification('Failed to save assignment', 'error')

// Warning
showNotification('Please fill all required fields', 'warning')

// Info
showNotification('Processing your request...', 'info')
```

---

## 💡 Complete Example

```jsx
import React, { useState } from 'react'
import { useNotifications } from '../hooks/useNotifications'
import NotificationContainer from '../components/NotificationContainer'

const MyPage = () => {
  const { notifications, showNotification, removeNotification } = useNotifications()
  const [loading, setLoading] = useState(false)

  const handleSave = async () => {
    setLoading(true)
    try {
      // Your API call here
      await saveData()
      showNotification('✅ Save successful!', 'success')
    } catch (error) {
      showNotification(`❌ Error: ${error.message}`, 'error')
    } finally {
      setLoading(false)
    }
  }

  const handleGenerate = async () => {
    setLoading(true)
    try {
      showNotification('⏳ Generating assignment...', 'info')
      // Your generation logic here
      await generateAssignment()
      showNotification('✅ Assignment generated!', 'success')
    } catch (error) {
      showNotification(`❌ Generation failed: ${error.message}`, 'error')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      {/* Notification Container */}
      <NotificationContainer 
        notifications={notifications} 
        onRemove={removeNotification} 
      />

      {/* Your content */}
      <button onClick={handleSave} disabled={loading}>
        Save Assignment
      </button>

      <button onClick={handleGenerate} disabled={loading}>
        Generate Assignment
      </button>
    </div>
  )
}

export default MyPage
```

---

## 📊 Notification Types

### 1. **Success** (✅ Green)
```jsx
showNotification('Operation completed successfully!', 'success')
```
Use for: Saved, created, updated, deleted successfully

### 2. **Error** (❌ Red)
```jsx
showNotification('Something went wrong!', 'error')
```
Use for: Failed operations, API errors, validation errors

### 3. **Warning** (⚠️ Orange)
```jsx
showNotification('Please review this before proceeding', 'warning')
```
Use for: Important info, confirmations, cautions

### 4. **Info** (ℹ️ Blue)
```jsx
showNotification('Processing your request...', 'info')
```
Use for: General information, loading states, updates

---

## ⚙️ Customization

### Change Auto-Dismiss Duration

```jsx
// Show for 10 seconds
showNotification('Message', 'success', 10000)

// Don't auto-dismiss (set to 0)
showNotification('Message', 'info', 0)

// Then manually close
const notifId = showNotification('Message', 'info', 0)
removeNotification(notifId)
```

### Customize Notification Position

Edit `notifications.css`:
```css
.notification-container {
  top: 20px;      /* Change this */
  right: 20px;    /* Change this */
}
```

Options:
- Top-right: `top: 20px; right: 20px;`
- Top-left: `top: 20px; left: 20px;`
- Bottom-right: `bottom: 20px; right: 20px;`
- Bottom-left: `bottom: 20px; left: 20px;`

---

## 🎯 Common Use Cases

### When Button is Clicked

```jsx
<button onClick={() => {
  showNotification('Button clicked!', 'info')
}}>
  Click Me
</button>
```

### When API Request Starts

```jsx
const handleFetch = async () => {
  showNotification('Loading data...', 'info')
  // Your code
}
```

### When API Request Completes

```jsx
const handleFetch = async () => {
  try {
    const response = await fetch(url)
    const data = await response.json()
    showNotification('Data loaded successfully!', 'success')
  } catch (error) {
    showNotification(`Error: ${error.message}`, 'error')
  }
}
```

### When Validation Fails

```jsx
const handleSubmit = (formData) => {
  if (!formData.name) {
    showNotification('Name is required', 'warning')
    return
  }
  // Submit form
}
```

### When Saving

```jsx
const handleSave = async () => {
  setLoading(true)
  try {
    await saveToDatabase(data)
    showNotification('✅ Saved successfully!', 'success')
  } catch (error) {
    showNotification(`❌ Save failed: ${error.message}`, 'error')
  } finally {
    setLoading(false)
  }
}
```

---

## 🎨 Styling Examples

### Success Notification
- 🟢 Green background
- ✅ Check icon
- Use for: Successful operations

### Error Notification
- 🔴 Red background
- ❌ Error icon
- Use for: Failed operations

### Warning Notification
- 🟡 Orange background
- ⚠️ Warning icon
- Use for: Cautions

### Info Notification
- 🔵 Blue background
- ℹ️ Info icon
- Use for: Information

---

## 📱 Mobile Support

The notification system is **fully responsive**:
- Adapts to mobile screen sizes
- Readable on all devices
- Touch-friendly close button
- Optimized animations

---

## 🔗 Quick Integration Checklist

For each page where you want notifications:

- [ ] Import hook: `import { useNotifications } from '../hooks/useNotifications'`
- [ ] Import component: `import NotificationContainer from '../components/NotificationContainer'`
- [ ] Initialize hook: `const { notifications, showNotification, removeNotification } = useNotifications()`
- [ ] Add component: `<NotificationContainer notifications={notifications} onRemove={removeNotification} />`
- [ ] Call `showNotification()` when needed

---

## 📝 Implementation Checklist for Your Pages

### StudentEvaluation.jsx
- [ ] Add notification hook
- [ ] Add NotificationContainer
- [ ] Show notification when submission starts
- [ ] Show notification when submission completes
- [ ] Show notification on errors

### FacultyDashboard.jsx
- [ ] Add notification hook
- [ ] Add NotificationContainer
- [ ] Show notification on data load
- [ ] Show notification on filter changes
- [ ] Show notification on actions

### FacultyEvaluation.jsx
- [ ] Add notification hook
- [ ] Show notification when evaluation starts
- [ ] Show notification when evaluation completes
- [ ] Show notification on finalize
- [ ] Show notification on AI detection

---

## 🚀 Next Steps

1. ✅ Files created (done!)
2. Add to `StudentEvaluation.jsx`
3. Add to `FacultyDashboard.jsx`
4. Add to `FacultyEvaluation.jsx`
5. Add to other pages as needed
6. Test all notifications

---

## 📞 Quick Reference

```jsx
// Import
import { useNotifications } from '../hooks/useNotifications'
import NotificationContainer from '../components/NotificationContainer'

// Use
const { notifications, showNotification, removeNotification } = useNotifications()

// Add to JSX
<NotificationContainer notifications={notifications} onRemove={removeNotification} />

// Show
showNotification('Success!', 'success')
showNotification('Error!', 'error')
showNotification('Warning!', 'warning')
showNotification('Info!', 'info')

// Customize duration
showNotification('Message', 'success', 10000)  // 10 seconds
showNotification('Message', 'info', 0)        // Never auto-dismiss
```

---

That's it! You now have a complete, reusable notification system ready to use across your entire application! 🎉
