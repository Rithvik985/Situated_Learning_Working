# 🔄 How to Switch Between Toast & Modal

## Current Setup

Your **StudentEvaluation.jsx** is currently using **MODAL notifications** (center popup).

```
StudentEvaluation.jsx:
  ✅ Using: NotificationModal
  ✅ Style: Center popup with backdrop
  ✅ Status: Fully working
```

---

## 🍞 Switch to TOAST (Corner Notification)

If you want the **top-right corner toast style** instead:

### Step 1: Open StudentEvaluation.jsx

### Step 2: Change Import (Line 12)
```jsx
// FROM:
import NotificationModal from '../components/NotificationModal'

// TO:
import NotificationContainer from '../components/NotificationContainer'
```

### Step 3: Change JSX (Line 136)
```jsx
// FROM:
<NotificationModal 
  notifications={notifications} 
  onRemove={removeNotification} 
/>

// TO:
<NotificationContainer 
  notifications={notifications} 
  onRemove={removeNotification} 
/>
```

### Step 4: Done!
Save and refresh. Notifications will now appear in top-right corner.

---

## 🎯 Switch Back to MODAL (Center Popup)

If you switched to toast and want to switch back:

### Step 1: Open StudentEvaluation.jsx

### Step 2: Change Import (Line 12)
```jsx
// FROM:
import NotificationContainer from '../components/NotificationContainer'

// TO:
import NotificationModal from '../components/NotificationModal'
```

### Step 3: Change JSX (Line 136)
```jsx
// FROM:
<NotificationContainer 
  notifications={notifications} 
  onRemove={removeNotification} 
/>

// TO:
<NotificationModal 
  notifications={notifications} 
  onRemove={removeNotification} 
/>
```

### Step 4: Done!
Save and refresh. Notifications will now appear in center.

---

## ⚡ Quick Comparison

| Aspect | Toast | Modal |
|--------|-------|-------|
| Import | `NotificationContainer` | `NotificationModal` |
| Component Tag | `<NotificationContainer />` | `<NotificationModal />` |
| Location | Top-right | Center |
| Appearance | Horizontal bar | Large box |
| Auto-dismiss | Yes (5 sec) | No |
| Backdrop | No | Yes |
| Interruption | Low | High |

---

## 🎨 Visual Difference

### Toast (Corner)
```
┌──────────────────────────────┐
│ Your Page                    │
│                              │
│                 ┌─────────┐  │
│                 │ ✅ Done │✕ │
│                 └─────────┘  │
│                              │
└──────────────────────────────┘
```

### Modal (Center)
```
┌──────────────────────────────┐
│ ⬜⬜ Backdrop ⬜⬜              │
│ ⬜ Your Page   ⬜              │
│ ⬜  ┌─────────┐ ⬜              │
│ ⬜  │✅ Done  │ ⬜              │
│ ⬜  └─────────┘ ⬜              │
│ ⬜⬜⬜⬜⬜⬜⬜⬜              │
└──────────────────────────────┘
```

---

## 📝 Code Changes Required

Only **2 places** need to change:

### Place 1: Import Statement
**File:** `frontend/src/pages/StudentEvaluation.jsx` (Line 12)
```jsx
// Toast:
import NotificationContainer from '../components/NotificationContainer'

// Modal:
import NotificationModal from '../components/NotificationModal'
```

### Place 2: JSX Component
**File:** `frontend/src/pages/StudentEvaluation.jsx` (Line 136)
```jsx
// Toast:
<NotificationContainer 
  notifications={notifications} 
  onRemove={removeNotification} 
/>

// Modal:
<NotificationModal 
  notifications={notifications} 
  onRemove={removeNotification} 
/>
```

---

## ✅ No Other Changes Needed!

The following remain **exactly the same**:

```jsx
✅ Hook usage:
   const { notifications, showNotification, removeNotification } = useNotifications()

✅ Function calls:
   showNotification('✅ Success!', 'success')
   showNotification('❌ Error!', 'error')
   showNotification('⚠️ Warning!', 'warning')
   showNotification('ℹ️ Info', 'info')

✅ Notification types:
   'success', 'error', 'warning', 'info'

✅ CSS styling:
   Automatically applied by the component
```

---

## 🧪 Test After Switching

### To Test Toast
1. Change imports
2. Save file
3. Go to StudentEvaluation page
4. Click "Analyze" button
5. Watch for **top-right corner** notification

### To Test Modal
1. Change imports
2. Save file
3. Go to StudentEvaluation page
4. Click "Analyze" button
5. Watch for **center screen** popup

---

## 🎯 Which Should I Use?

### Use Toast When:
- You want quick, non-intrusive feedback
- Multiple notifications might appear
- Auto-dismiss is good
- User doesn't need to acknowledge
- Background notifications are OK
- Examples: "Saved!", "Deleted!", "Complete"

### Use Modal When:
- You want user attention
- Important alerts or errors
- User should acknowledge
- Should block interaction
- Single notification at a time
- Examples: "Error!", "Failed!", "Important info"

---

## 🔧 Advanced Customization

### For Toast Notifications
**File:** `frontend/src/styles/notifications.css`
- Change position (top, right, left, bottom)
- Change colors
- Change animation duration
- Change auto-dismiss time

### For Modal Notifications
**File:** `frontend/src/styles/notificationModal.css`
- Change backdrop color/opacity
- Change modal size
- Change border colors
- Change animation timing
- Change icon size

---

## 📁 File Reference

### Toast Files
- Component: `frontend/src/components/NotificationContainer.jsx`
- Styles: `frontend/src/styles/notifications.css`
- Hook: `frontend/src/hooks/useNotifications.js`

### Modal Files
- Component: `frontend/src/components/NotificationModal.jsx`
- Styles: `frontend/src/styles/notificationModal.css`
- Hook: `frontend/src/hooks/useNotifications.js`

### Documentation
- Toast Guide: `NOTIFICATIONS_GUIDE.md`
- Modal Guide: `NOTIFICATIONS_MODAL_GUIDE.md`
- Comparison: `TOAST_vs_MODAL_GUIDE.md`
- Quick Reference: `NOTIFICATIONS_QUICK_REFERENCE.md`

---

## ⚡ One-Minute Swap

```
1. Open: StudentEvaluation.jsx
2. Line 12: Change import name
3. Line 136: Change component tag
4. Save
5. Refresh page
6. Done! ✅
```

---

## 💾 Current State

```
✅ NotificationModal.jsx         - Modal component (NEW)
✅ notificationModal.css         - Modal styles (NEW)
✅ NotificationContainer.jsx     - Toast component (still available)
✅ notifications.css             - Toast styles (still available)
✅ useNotifications.js           - Hook (works with both)
✅ StudentEvaluation.jsx         - Using Modal (current)
```

---

## 🚀 Next Steps

### Option A: Keep Modal
- Default for StudentEvaluation
- Already set up and working
- Good for important alerts

### Option B: Switch to Toast
- 2 lines of code
- Quick feedback style
- Good for quick messages

### Option C: Use Both
- Different pages use different styles
- FacultyEvaluation = Modal
- StudentEvaluation = Toast
- Flexibility!

---

**You now have full control over notification styles!** Pick whichever works best for your use case. 🎉
