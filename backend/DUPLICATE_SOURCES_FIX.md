# Duplicate Sources Fix

## Problem Identified

When asking "Can you list the main API endpoints?", the response showed the same source twice:

```
Sources:
main.py (lines 112-198) (93%)
main.py (lines 112-198) (93%)  ← DUPLICATE
src\indexer.py (lines 1-28) (57%)
```

## Root Cause

The `main.py` file is **indexed twice** in the metadata file (`a2a22b0a-f575-46da-b618-b146cd495b0a.json`):

```json
{
  "file_path": "main.py",
  "content_hash": "19b8e2488c8b432442c0cdb7536e5166f2b04fa76d7de2cc6789779c597a6af5",
  "size": 8193,
  "indexed_at": "2025-10-17 06:06:30.169835"
},
{
  "file_path": "main.py",  ← DUPLICATE ENTRY
  "content_hash": "19b8e2488c8b432442c0cdb7536e5166f2b04fa76d7de2cc6789779c597a6af5",
  "size": 8193,
  "indexed_at": "2025-10-17 06:06:30.278656"
}
```

**Why this happened:** The indexing process indexed the same file twice, possibly due to:
- Race condition during indexing
- File being processed twice in the file list
- Retry logic that didn't check for existing entries

## Solution Implemented

Added **deduplication logic** in `backend/src/services/rag_service.py` (lines 873-883):

```python
# Deduplicate by file path (keep highest score) before taking top 3
seen_files = {}
for file_info, score in relevant_files:
    file_path = file_info.get('file_path', '')
    if file_path not in seen_files or score > seen_files[file_path][1]:
        seen_files[file_path] = (file_info, score)

# Convert back to list and sort by score
deduplicated_files = list(seen_files.values())
deduplicated_files.sort(key=lambda x: x[1], reverse=True)
top_files = deduplicated_files[:3]  # Top 3 most relevant files
```

**How it works:**
1. Iterates through all relevant files
2. Tracks each unique file path in a dictionary
3. If a file appears multiple times, keeps the entry with the **highest score**
4. Returns deduplicated list sorted by relevance

## Testing

### Before Fix
```bash
Query: "Can you list the main API endpoints?"
Sources: 3 total
  - main.py (lines 112-198) (93%)
  - main.py (lines 112-198) (93%)  ← Duplicate
  - src\indexer.py (lines 1-28) (57%)
```

### After Fix (Expected)
```bash
Query: "Can you list the main API endpoints?"
Sources: 2 total
  - main.py (lines 112-198) (93%)
  - src\indexer.py (lines 1-28) (57%)
```

## How to Apply the Fix

The backend server needs to be restarted to load the new code:

### Option 1: Restart the running server
1. Find the terminal running uvicorn
2. Press `Ctrl+C` to stop the server
3. Run: `python -m uvicorn src.main:app --host 0.0.0.0 --port 8000`

### Option 2: Kill and restart
```powershell
# Kill the process using port 8000
Get-Process -Name python | Where-Object {$_.Id -in (Get-NetTCPConnection -LocalPort 8000 -State Listen).OwningProcess} | Stop-Process -Force

# Start server
cd c:\Users\prana\coding-assistant\backend
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000
```

## Verification

After restarting, test with:
```powershell
$body = @{query='Can you list the main API endpoints?'} | ConvertTo-Json
$response = Invoke-RestMethod -Uri 'http://localhost:8000/api/chat/query' -Method Post -Body $body -ContentType 'application/json'
Write-Host "Number of sources: $($response.sources.Count)"
$response.sources | ForEach-Object { 
    Write-Host "  - $($_.file) (lines $($_.line_start)-$($_.line_end))" 
}
```

**Expected output:**
```
Number of sources: 2
  - main.py (lines 112-198)
  - src\indexer.py (lines 1-28)
```

## Long-Term Fix

To prevent duplicate indexing in the future, consider:

### Option 1: Fix the indexing process
Add deduplication logic in the indexer service before saving metadata:
```python
# In indexer_service.py
seen_files = set()
unique_files = []
for file_entry in files:
    if file_entry['file_path'] not in seen_files:
        seen_files.add(file_entry['file_path'])
        unique_files.append(file_entry)
```

### Option 2: Re-index the repository
This will create fresh metadata without duplicates:
1. Go to the frontend
2. Click "Index" tab
3. Click "Clear Index"
4. Re-index the web-rag-service repository

## Impact

✅ **Immediate:** Duplicate sources eliminated from responses  
✅ **Performance:** Slightly faster (fewer duplicate file reads)  
✅ **UX:** Cleaner source lists without confusion  
✅ **Reliability:** More accurate relevance scoring (no duplicate votes)

## Files Modified

```
backend/src/services/rag_service.py (lines 873-883)
  - Added deduplication logic in _retrieve_relevant_content method
```

## Status

- [x] Fix implemented
- [x] Code documented
- [ ] Server restarted (pending)
- [ ] Fix verified with test query
- [ ] Consider re-indexing to prevent future issues

---

**Note:** The deduplication fix is a runtime solution. The underlying issue (duplicate entries in metadata) still exists but is now handled gracefully.
