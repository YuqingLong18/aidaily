# Fix Database Path Issue

## Problem Identified

Your frontend and ingestion are using **different databases**:

- **Frontend**: `file:../web/prisma/dev.db` (relative path, resolves incorrectly)
- **Ingestion**: `file:/www/wwwroot/aidaily/nexus-daily/web/prisma/dev.db` (absolute path)

This is why:
- Ingestion shows 27 items
- Frontend shows 0 items

## Solution

### Option 1: Set Absolute Path in Environment Variable (Recommended)

Set the `DATABASE_URL` environment variable to use the **same absolute path** that ingestion uses:

```bash
# In your PM2 ecosystem file or .env file:
DATABASE_URL="file:/www/wwwroot/aidaily/nexus-daily/web/prisma/dev.db"
```

Or if using PM2 directly:
```bash
pm2 restart your-app-name --update-env
# Then set the env var in your PM2 config
```

### Option 2: Use the Code Fix (Already Applied)

I've updated `lib/prisma.ts` to automatically resolve relative paths to absolute paths. However, you still need to ensure the relative path is correct.

If your `DATABASE_URL` is `file:../web/prisma/dev.db`, it should be:
- `file:./prisma/dev.db` (if running from web/ directory)
- Or use the absolute path from Option 1

### Option 3: Verify Database File Location

First, verify where the actual database file is:

```bash
# Find the database file
find /www/wwwroot/aidaily -name "dev.db" -type f

# Check its size (should be > 0 if it has data)
ls -lh /www/wwwroot/aidaily/nexus-daily/web/prisma/dev.db
```

Then set `DATABASE_URL` to point to that exact location.

## Steps to Fix

1. **Stop your PM2 process**:
   ```bash
   pm2 stop your-app-name
   ```

2. **Set the correct DATABASE_URL**:
   
   If using a `.env` file in `nexus-daily/web/`:
   ```bash
   cd /www/wwwroot/aidaily/nexus-daily/web
   echo 'DATABASE_URL="file:/www/wwwroot/aidaily/nexus-daily/web/prisma/dev.db"' >> .env.production
   ```
   
   Or if using PM2 ecosystem file, add:
   ```json
   {
     "env": {
       "DATABASE_URL": "file:/www/wwwroot/aidaily/nexus-daily/web/prisma/dev.db"
     }
   }
   ```

3. **Restart PM2**:
   ```bash
   pm2 restart your-app-name
   ```

4. **Verify the fix**:
   Check the logs - you should now see:
   ```
   [page.tsx] DATABASE_URL: file:/www/wwwroot/aidaily/nexus-daily/web/prisma/dev.db...
   [page.tsx] Database connection OK. Total items in database: 27
   ```

## Verification

After fixing, the logs should show:
- ✅ Same DATABASE_URL in both frontend and ingestion logs
- ✅ Frontend shows 27 items (or whatever ingestion has)
- ✅ Items appear in the frontend

## Why This Happened

Relative paths like `file:../web/prisma/dev.db` resolve differently depending on:
- Where the Node.js process is started from
- The current working directory when Prisma initializes
- PM2's working directory

Absolute paths are always reliable and consistent.

