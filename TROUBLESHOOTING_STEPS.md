# Troubleshooting Steps for Empty Cards Issue

## Current Status

Based on the logs:
- ✅ Ingestion is working: Items are fetched, processed, and saved
- ✅ Database has 27 items
- ❌ Frontend shows empty cards
- ⚠️ Items are being skipped as duplicates (0 saved in last run)

## Enhanced Logging Added

I've added comprehensive **always-on** logging to `page.tsx` that will help diagnose the issue. The logs will now show:

1. **Database connection verification** - Total item count
2. **Date filtering details** - Cutoff date vs most recent item date
3. **Query results** - How many items found and their types
4. **Sample items** - First 3 items with full details
5. **Diagnostic queries** - If no items found, shows items from last 30 days
6. **DATABASE_URL** - To verify both services use the same database

## Next Steps

### 1. Restart the Frontend Server

The new logging will only appear when the page is actually rendered (not during build). Restart your PM2 process:

```bash
pm2 restart your-app-name
# or
pm2 restart all
```

### 2. Check the Server Logs

After restarting, visit the frontend page and check the PM2 logs:

```bash
pm2 logs your-app-name --lines 50
```

You should now see detailed `[page.tsx]` logs showing:
- Database connection status
- Total items in database
- Most recent item date
- Query results
- Sample items

### 3. Verify Database Path

Check that both services use the same `DATABASE_URL`:

**Ingestion** (from logs):
```
DATABASE_URL: file:/www/wwwroot/aidaily/nexus-daily/web/prisma/d...
```

**Frontend** (will show in new logs):
```
DATABASE_URL: file:/www/wwwroot/aidaily/nexus-daily/web/prisma/d...
```

If they differ, that's the problem! Update the environment variable to match.

### 4. Check Date Filtering

The logs will show:
- Cutoff date (8 days ago)
- Most recent item date
- Whether items are included

If the most recent item is older than 8 days, that's why nothing shows. You can:
- Increase the date range in `page.tsx` (change `- 8` to `- 30`)
- Or wait for newer items to be ingested

### 5. Verify Items Have Required Data

The logs will show sample items. Check that they have:
- `summaryEn` or `summaryZh` populated
- `keywordsEn` or `keywordsZh` populated
- Valid `publishedAt` dates

## Common Issues and Solutions

### Issue: "Total items in database: 0"
**Solution**: Database path mismatch. Verify `DATABASE_URL` is the same for both services.

### Issue: "Query result: Found 0 items" but "Total items in database: 27"
**Solution**: Date filter too restrictive. Most recent items are older than 8 days. Check the "Most recent item" date in logs.

### Issue: Items found but cards still empty
**Solution**: Check sample items in logs. If `summaryEn`, `summaryZh`, `keywordsEn`, `keywordsZh` are all empty, the LLM processing failed. Check ingestion logs for LLM errors.

### Issue: "Database connection OK" but query fails
**Solution**: Check Prisma client is generated: `cd nexus-daily/web && npx prisma generate`

## What the New Logs Will Show

When you restart and visit the page, you'll see output like:

```
[page.tsx] Query: Fetching items published after: 2025-12-05T00:00:00.000Z (current time: 2025-12-13T...)
[page.tsx] DATABASE_URL: file:/www/wwwroot/aidaily/nexus-daily/web/prisma/dev.db
[page.tsx] Database connection OK. Total items in database: 27
[page.tsx] Most recent item: "Omni-Attribute: Open-vocabulary Attribut..." published at: 2025-12-11T18:59:56.000Z
[page.tsx] Date comparison: cutoff=2025-12-05T00:00:00.000Z, mostRecent=2025-12-11T18:59:56.000Z, included=true
[page.tsx] Query result: Found 15 items (academic: 10, industry: 5)
[page.tsx] Sample items:
  - "Omni-Attribute: Open-vocabulary Attribut..." (academic, AI Theory & Architectures, published: 2025-12-11T18:59:56.000Z)
  ...
```

This will tell us exactly what's happening!

## If Still Not Working

If after seeing the new logs the issue persists, share:
1. The new `[page.tsx]` log output
2. The DATABASE_URL values from both logs
3. The "Most recent item" date vs "cutoff" date
4. The "Query result" line showing how many items were found

