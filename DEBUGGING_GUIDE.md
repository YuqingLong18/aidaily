# Debugging Guide: Empty Cards Issue

## Overview
This guide documents the changes made to add comprehensive logging and fix potential issues that could cause empty cards in production.

## Key Changes Made

### 1. Comprehensive Logging Added

#### Ingestion Pipeline (`nexus-daily/ingestion/`)
- **main.py**: Added detailed logging at every step:
  - Database connection verification
  - Item validation before saving
  - Count of items at each stage (fetched, processed, saved, duplicates, errors)
  - Sample items logged for verification
  - Logs written to both console and `ingestion.log` file

- **processor.py**: Added logging for:
  - LLM API calls and responses
  - JSON parsing errors
  - Missing fields in LLM responses
  - API key validation

- **scraper.py**: Added logging for:
  - Network requests and responses
  - Date parsing issues
  - Items filtered by date cutoff
  - Feed parsing warnings

#### Frontend (`nexus-daily/web/`)
- **app/page.tsx**: Added server-side logging:
  - Query parameters and results
  - Item counts by type
  - Sample items with key fields
  - Warnings when no items found with diagnostic info
  - Total database count verification

- **components/NewsCard.tsx**: Added development-mode warnings for empty cards

### 2. Date/Timezone Fixes

**Problem**: Date filtering was inconsistent between ingestion (UTC) and frontend (local time), causing items to be filtered out incorrectly.

**Solution**:
- **main.py**: Improved `parse_published_at()` function to robustly handle various date formats and always return UTC
- **app/page.tsx**: Changed date filtering to use UTC dates matching the ingestion pipeline
- **components/Dashboard.tsx**: Fixed date filtering to use UTC for consistency

### 3. Data Validation

**Added `validate_item()` function in main.py**:
- Checks all required fields are present
- Validates score is between 0-10
- Ensures at least one summary field has content
- Prevents saving invalid items

### 4. Database Connection Verification

- Logs database URL (truncated for security)
- Verifies connection by checking item count before and after ingestion
- Queries recent items to verify they're accessible
- Better error handling with full stack traces

## Potential Root Causes to Check

### 1. Database Connection Issues
**Symptoms**: Items saved but not visible in frontend
**Check**:
- Verify `DATABASE_URL` is the same for both ingestion and frontend
- Check if ingestion and frontend are connecting to different databases
- Look for database connection errors in logs

**Logs to check**:
```
[main.py] DATABASE_URL: ...
[main.py] Database connection established
[main.py] Current database contains X items
[main.py] Database now contains Y items
```

### 2. Date/Timezone Mismatch
**Symptoms**: Items exist in DB but don't show up due to date filtering
**Check**:
- Compare `publishedAt` dates in database with cutoff date in logs
- Verify timezone handling is consistent

**Logs to check**:
```
[page.tsx] Fetching items published after: [date]
[page.tsx] Most recent item published at: [date]
```

### 3. LLM Processing Failures
**Symptoms**: Items fetched but not processed/saved
**Check**:
- Look for LLM API errors in `processor.py` logs
- Check if `OPENROUTER_API_KEY` is set correctly
- Verify LLM responses contain required fields

**Logs to check**:
```
[processor.py] Error processing item...
[main.py] Processing complete: X processed, Y skipped
```

### 4. Empty Data Fields
**Symptoms**: Items saved but cards appear empty
**Check**:
- Verify `summaryEn`, `summaryZh`, `keywordsEn`, `keywordsZh` are populated
- Check if LLM returned empty responses

**Logs to check**:
```
[processor.py] No English summary bullets found for: ...
[NewsCard] Empty card detected for item: ...
```

### 5. Silent Failures
**Symptoms**: No errors but items not appearing
**Check**:
- Review all exception handlers - they now log full stack traces
- Check for validation failures that skip items

## How to Debug in Production

### Step 1: Check Ingestion Logs
```bash
# After running ingestion, check the log file
tail -100 nexus-daily/ingestion/ingestion.log

# Or check console output for:
# - Total items fetched
# - Items processed successfully
# - Items saved to database
# - Database connection status
```

### Step 2: Verify Database Contents
```bash
# Connect to your database and check:
SELECT COUNT(*) FROM Item;
SELECT title, type, category, publishedAt, summaryEn, summaryZh 
FROM Item 
ORDER BY publishedAt DESC 
LIMIT 10;
```

### Step 3: Check Frontend Logs
- Check server-side logs (Next.js console output)
- Look for:
  - Item count from database query
  - Date filtering information
  - Warnings about empty cards

### Step 4: Compare Dates
```bash
# In database, check publishedAt values:
SELECT 
  id, 
  title, 
  publishedAt,
  DATETIME(publishedAt) as local_time
FROM Item 
ORDER BY publishedAt DESC 
LIMIT 5;
```

Compare these with the cutoff date logged in `page.tsx`.

## Common Issues and Solutions

### Issue: Items saved but not visible
**Possible causes**:
1. Date filtering too restrictive - check cutoff date vs item dates
2. Different databases - verify DATABASE_URL matches
3. Timezone mismatch - should be fixed now, but verify

**Solution**: Check logs for date comparisons and database counts

### Issue: Empty cards (cards show but no content)
**Possible causes**:
1. LLM returned empty summaries
2. Data not properly saved to database
3. Frontend not reading correct fields

**Solution**: Check NewsCard debug logs and verify database fields are populated

### Issue: No items fetched
**Possible causes**:
1. Network issues
2. Source URLs changed
3. Date cutoff too restrictive

**Solution**: Check scraper logs for network errors and fetched item counts

## Log File Locations

- **Ingestion logs**: `nexus-daily/ingestion/ingestion.log`
- **Console logs**: Check stdout/stderr of ingestion process
- **Frontend logs**: Next.js server console output
- **Browser logs**: Check browser console for client-side warnings (development mode)

## Next Steps

1. **Run ingestion** and review the detailed logs
2. **Check database** to verify items were saved with correct data
3. **Check frontend logs** to see what items are being queried
4. **Compare dates** between ingestion and frontend filtering
5. **Review empty card warnings** in NewsCard component

## Additional Debugging Commands

```bash
# Check if database file exists and is accessible
ls -lh nexus-daily/web/prisma/dev.db

# Check database schema
cd nexus-daily/web && npx prisma studio

# Test database connection from Python
cd nexus-daily/ingestion
python3 -c "from prisma import Prisma; import asyncio; async def test(): db = Prisma(); await db.connect(); print(f'Connected! Count: {await db.item.count()}'); await db.disconnect(); asyncio.run(test())"

# Check environment variables
echo $DATABASE_URL
echo $OPENROUTER_API_KEY
```

## Summary

The codebase now has:
- ✅ Comprehensive logging at every step
- ✅ Date/timezone consistency fixes
- ✅ Data validation before saving
- ✅ Database connection verification
- ✅ Better error messages with stack traces
- ✅ Debug warnings for empty cards

Use the logs to identify exactly where the pipeline is failing in production.

