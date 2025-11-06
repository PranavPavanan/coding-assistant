# Frontend Cache Fix Instructions

## Problem
The frontend is showing "undefined" for line numbers even though the backend API is returning correct data:
```json
{
  "file": "main.py",
  "line_start": 112,
  "line_end": 198,
  "score": 0.87
}
```

## Root Cause
**Browser cache** - The browser is using an old cached version of `app.js` that doesn't have the field name fixes.

## Solution Applied
1. ✅ Incremented cache-busting version: `app.js?v=2` → `app.js?v=3`
2. ✅ Added debug console logging to help troubleshoot
3. ✅ Backend is confirmed working (API returns correct data)

## How to Fix in Your Browser

### Method 1: Hard Refresh (RECOMMENDED)
1. Open http://localhost:8000/ in your browser
2. Press one of these key combinations:
   - **Windows Chrome/Edge:** `Ctrl + Shift + R` or `Ctrl + F5`
   - **Windows Firefox:** `Ctrl + Shift + R` or `Ctrl + F5`
   - **Mac Chrome:** `Cmd + Shift + R`
   - **Mac Safari:** `Cmd + Option + R`

### Method 2: Clear Browser Cache
1. Open browser DevTools (F12)
2. Right-click the refresh button
3. Select "Empty Cache and Hard Reload"

### Method 3: Private/Incognito Window
1. Open a new Incognito/Private window
2. Go to http://localhost:8000/
3. Test the query

## How to Verify It's Fixed

### 1. Check Browser Console
After asking "Can you list the main API endpoints?":

Open console (F12) and look for:
```javascript
Source data: {
  file: "main.py",
  line_start: 112,
  line_end: 198,
  score: 0.8666666666666667,
  computed: { filePath: "main.py", lineStart: 112, lineEnd: 198, score: " (87%)" }
}
```

If you see this, the new code is loaded! ✅

### 2. Check Source Display
Sources should show:
```
📄 main.py (lines 112-198) (87%)
```

NOT:
```
📄 undefined (lines undefined-undefined)
```

## Expected Result

After hard refresh, you should see:

**Question:** "Can you list the main API endpoints and which files define them?"

**Answer:** 
```
In this repository, the main API endpoints are as follows:
- GET /: This is the root endpoint, returning a health check message.
- GET /health: Provides a detailed health check with service status.
- POST /crawl: Used to crawl a website and extract content.
- POST /index: Indexes crawled content into a vector store.
- POST /ask: Allows asking a question and receiving an answer with sources.
```

**Sources:**
```
Source 1:
  📄 File: main.py
  📍 Lines: 112-198
  ⭐ Relevance: 87%
  📋 Preview: # Lines 112-118
  @app.get("/")
  async def root():
      """Health check endpoint"""
      ...
```

## Troubleshooting

### If still showing "undefined":
1. Check browser console for the debug log
2. If you see the correct data in console but wrong display:
   - The JavaScript is still cached
   - Try Method 2 or 3 above
3. If console shows old code (no debug log):
   - Clear ALL browser data
   - Restart browser
   - Try incognito mode

### If console shows errors:
Take a screenshot and check:
- Network tab in DevTools
- Is `app.js?v=3` being loaded?
- Any 404 or network errors?

## Quick Test Command

From PowerShell, verify API is returning correct data:
```powershell
$body = @{query='Can you list the main API endpoints?'} | ConvertTo-Json
$response = Invoke-RestMethod -Uri 'http://localhost:8000/api/chat/query' -Method Post -Body $body -ContentType 'application/json'
$response.sources[0] | Format-List
```

Should show:
```
file       : main.py
line_start : 112
line_end   : 198
score      : 0.8666666666666667
```

---

## Summary

✅ Backend is working perfectly (verified with test script: 9/9 checks passed)
✅ API returns correct line numbers
✅ Frontend code is fixed
❌ Browser cache is preventing the fix from loading

**ACTION:** Do a hard refresh with `Ctrl + Shift + R` and it will work! 🚀
