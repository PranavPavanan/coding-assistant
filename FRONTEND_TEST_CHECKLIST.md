# Frontend Testing Checklist

## Test Environment
- **Backend:** Running on http://localhost:8000
- **Frontend:** Available at http://localhost:8000/
- **Existing Index:** web-rag-service (29 files)

---

## ✅ Test 1: Tab Text Visibility

### Steps:
1. Open http://localhost:8000/ in your browser
2. Look at the three tabs in the navigation bar

### Expected Results:
- [ ] First tab shows "Search" label and "Find repositories" description
- [ ] Second tab shows "Index" label and "Index repository" description  
- [ ] Third tab shows "Query" label and "Ask questions" description
- [ ] All text is clearly visible and readable
- [ ] No text is cut off or hidden

### Actual Result:
_Check and note if tabs are visible_

---

## ✅ Test 2: Index Status Detection on Load

### Steps:
1. Open browser console (F12)
2. Reload the page (F5)
3. Check console output

### Expected Results:
- [ ] Console shows: "Loading index stats from API..."
- [ ] Console shows: "Index stats loaded:" with object
- [ ] Console shows: "✓ Repository "web-rag-service" is already indexed!"
- [ ] Console shows: "Files: 29, Vectors: [number]"
- [ ] Console shows: "Updating tab states:" with `isIndexed: true`

### Actual Result:
_Copy the console output here_

```
[Console output]
```

---

## ✅ Test 3: Green Banner Display

### Steps:
1. Page should be on "Search" tab by default
2. Look at the top of the search section

### Expected Results:
- [ ] Green banner is visible at the top
- [ ] Banner text reads: "Repository Ready!"
- [ ] Repository name "web-rag-service" is shown
- [ ] Text says "is indexed and ready for AI queries"
- [ ] Blue "Start Querying" button is visible on the right side of banner

### Actual Result:
_Describe what you see_

---

## ✅ Test 4: Chat Tab is Enabled

### Steps:
1. Look at the "Query" tab in the navigation
2. Try to click on it

### Expected Results:
- [ ] "Query" tab is NOT grayed out
- [ ] "Query" tab is clickable
- [ ] Clicking it switches to the chat interface
- [ ] No disabled state or opacity

### Actual Result:
_Can you click the Query tab?_

---

## ✅ Test 5: Banner Button Functionality

### Steps:
1. On the "Search" tab, find the green banner
2. Click the "Start Querying" button

### Expected Results:
- [ ] Page switches to "Query" tab
- [ ] Chat interface is visible
- [ ] Input field is enabled (not grayed out)
- [ ] Can type in the input field
- [ ] Submit button is enabled

### Actual Result:
_What happens when you click the button?_

---

## ✅ Test 6: Index Tab Shows Current Index

### Steps:
1. Click on the "Index" tab
2. Scroll down to see the "Current Index" section

### Expected Results:
- [ ] "Current Index" card is visible
- [ ] Shows "Repository: web-rag-service"
- [ ] Shows "Files Indexed: 29"
- [ ] Shows "Vectors: [some number]"
- [ ] "Clear Index" button is visible (red button)
- [ ] "Start Indexing" button shows as "Re-index Repository"

### Actual Result:
_What do you see in the Index tab?_

---

## ✅ Test 7: Chat Interface State

### Steps:
1. Go to "Query" tab (if not already there)
2. Check the chat interface elements

### Expected Results:
- [ ] No message saying "No repository indexed yet"
- [ ] Welcome message is visible: "Ask me anything about the code!"
- [ ] Repository info bar shows: "What do you want to know about web-rag-service?"
- [ ] Chat input placeholder says: "Ask a question about web-rag-service..."
- [ ] Input field is enabled (can type)
- [ ] Send button is enabled (not grayed out)
- [ ] Bottom stats bar shows: "Querying: web-rag-service - 29 files indexed"

### Actual Result:
_Describe the chat interface state_

---

## ✅ Test 8: Tab Navigation

### Steps:
1. Click through tabs in this order: Search → Index → Query → Search
2. Observe state changes

### Expected Results:
- [ ] Banner appears on Search tab
- [ ] Banner disappears on Index and Query tabs
- [ ] Each tab shows correct content
- [ ] Tab highlighting changes correctly (purple for active)
- [ ] Query tab never gets disabled
- [ ] Console logs tab switches

### Actual Result:
_Does tab switching work smoothly?_

---

## ✅ Test 9: Actually Query the Repository

### Steps:
1. Go to "Query" tab
2. Type: "What is this repository about?"
3. Click send or press Enter

### Expected Results:
- [ ] Message appears in chat as "user" message
- [ ] Loading spinner appears
- [ ] AI response appears after a few seconds
- [ ] Response talks about web-rag-service
- [ ] Sources are shown below the response with file names and line numbers
- [ ] No errors in console

### Actual Result:
_Copy the AI response here_

```
[AI Response]
```

---

## ✅ Test 10: Browser Console Errors

### Steps:
1. Open console (F12)
2. Check for any red errors

### Expected Results:
- [ ] No JavaScript errors
- [ ] No failed network requests to /api/index/stats
- [ ] No 404 or 500 errors
- [ ] Only INFO level logs visible

### Actual Result:
_Any errors?_

```
[Console errors if any]
```

---

## Summary

### Overall Assessment
- Visual Issues: [ ] None / [ ] Some / [ ] Many
- Functional Issues: [ ] None / [ ] Some / [ ] Many
- Index Detection: [ ] Works / [ ] Doesn't Work
- Banner Display: [ ] Works / [ ] Doesn't Work
- Chat Enabled: [ ] Yes / [ ] No

### Notes:
_Add any additional observations or issues_

---

## Known Issues (if any)

### Issue 1:
**Description:**
**Impact:** High / Medium / Low
**Workaround:**

### Issue 2:
**Description:**
**Impact:** High / Medium / Low
**Workaround:**

---

## Screenshots

### Search Tab with Banner
_Take a screenshot showing the green banner_

### Index Tab with Current Index
_Take a screenshot showing the indexed repository info_

### Query Tab with Chat Interface
_Take a screenshot showing enabled chat interface_

---

## Next Steps

If all tests pass:
- [ ] Frontend is ready for use
- [ ] Can proceed with querying repository
- [ ] Delete test files before pushing to GitHub

If tests fail:
- [ ] Note specific failures above
- [ ] Check browser console for errors
- [ ] Verify backend is running correctly
- [ ] Check network requests in DevTools

---

## Quick Fixes

### If banner doesn't show:
1. Check console for "Index stats loaded" message
2. Verify API returns `is_indexed: true`
3. Hard refresh browser (Ctrl+Shift+R)

### If tabs are still invisible:
1. Clear browser cache
2. Hard refresh (Ctrl+Shift+R)
3. Check if styles.css loaded correctly in Network tab

### If chat tab is disabled:
1. Check console for index stats
2. Verify `state.indexStats.is_indexed` is true
3. Check for JavaScript errors in console

---

## Developer Commands

### Check index stats from terminal:
```powershell
curl http://localhost:8000/api/index/stats | ConvertFrom-Json
```

### Check backend health:
```powershell
curl http://localhost:8000/api/health
```

### View backend logs:
Check the terminal where uvicorn is running

### Restart backend:
```powershell
# In backend terminal: Ctrl+C
cd c:\Users\prana\coding-assistant\backend
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000
```

---

**Tester:** ___________________  
**Date:** ___________________  
**Browser:** ___________________  
**Browser Version:** ___________________
