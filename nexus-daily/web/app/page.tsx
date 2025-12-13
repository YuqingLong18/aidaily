import { prisma } from '@/lib/prisma';
import { Dashboard } from '@/components/Dashboard';
import { Item } from '@prisma/client';

// Use dynamic rendering to avoid build-time database connection issues
// Revalidate every hour in production
export const dynamic = 'force-dynamic';
export const revalidate = 3600;

// Always log critical diagnostics, even in production
async function getItems(): Promise<Item[]> {
  // Use UTC dates to match ingestion pipeline
  const now = new Date();
  const eightDaysAgo = new Date(Date.UTC(
    now.getUTCFullYear(),
    now.getUTCMonth(),
    now.getUTCDate() - 8,
    0, 0, 0, 0
  ));

  // Always log query parameters for debugging
  console.log(`[page.tsx] Query: Fetching items published after: ${eightDaysAgo.toISOString()} (current time: ${now.toISOString()})`);
  console.log(`[page.tsx] DATABASE_URL: ${process.env.DATABASE_URL ? process.env.DATABASE_URL.substring(0, 60) + '...' : 'NOT SET'}`);
  
  try {
    // First, check total count to verify database connection
    const totalCount = await prisma.item.count();
    console.log(`[page.tsx] Database connection OK. Total items in database: ${totalCount}`);
    
    // Get the most recent item to see what dates we have
    const mostRecent = await prisma.item.findFirst({
      orderBy: { publishedAt: 'desc' },
      select: { publishedAt: true, title: true },
    });
    
    if (mostRecent) {
      console.log(`[page.tsx] Most recent item: "${mostRecent.title?.substring(0, 50)}..." published at: ${mostRecent.publishedAt.toISOString()}`);
      console.log(`[page.tsx] Date comparison: cutoff=${eightDaysAgo.toISOString()}, mostRecent=${mostRecent.publishedAt.toISOString()}, included=${mostRecent.publishedAt >= eightDaysAgo}`);
    } else {
      console.warn(`[page.tsx] WARNING: No items found in database at all!`);
    }
    
    // Query items
    const items = await prisma.item.findMany({
      where: {
        publishedAt: {
          gte: eightDaysAgo,
        },
      },
      orderBy: [
        { publishedAt: 'desc' },
        { score: 'desc' },
      ],
      take: 100, // Limit to prevent build-time memory issues
    });
    
    const academicCount = items.filter(i => i.type === 'academic').length;
    const industryCount = items.filter(i => i.type === 'industry').length;
    console.log(`[page.tsx] Query result: Found ${items.length} items (academic: ${academicCount}, industry: ${industryCount})`);
    
    // Always log sample items for debugging
    if (items.length > 0) {
      const sample = items.slice(0, 3);
      console.log(`[page.tsx] Sample items:`);
      for (const item of sample) {
        console.log(`  - "${item.title.substring(0, 50)}..." (${item.type}, ${item.category}, published: ${item.publishedAt.toISOString()})`);
      }
    } else {
      console.warn(`[page.tsx] WARNING: Query returned 0 items!`);
      console.warn(`[page.tsx] This could mean:`);
      console.warn(`  1. Date filter is too restrictive (cutoff: ${eightDaysAgo.toISOString()})`);
      console.warn(`  2. All items are older than 8 days`);
      console.warn(`  3. Database query issue`);
      
      // Get items from last 30 days to see what we have
      const thirtyDaysAgo = new Date(Date.UTC(
        now.getUTCFullYear(),
        now.getUTCMonth(),
        now.getUTCDate() - 30,
        0, 0, 0, 0
      ));
      const recentItems = await prisma.item.findMany({
        where: {
          publishedAt: {
            gte: thirtyDaysAgo,
          },
        },
        orderBy: { publishedAt: 'desc' },
        take: 5,
        select: { title: true, publishedAt: true, type: true },
      });
      
      if (recentItems.length > 0) {
        console.log(`[page.tsx] Items from last 30 days (${recentItems.length} found):`);
        for (const item of recentItems) {
          console.log(`  - "${item.title?.substring(0, 50)}..." (${item.type}, ${item.publishedAt.toISOString()})`);
        }
      }
    }
    
    return items;
  } catch (error) {
    console.error(`[page.tsx] ERROR fetching items:`, error);
    // Log full error details
    if (error instanceof Error) {
      console.error(`[page.tsx] Error message: ${error.message}`);
      console.error(`[page.tsx] Error stack: ${error.stack}`);
    }
    throw error;
  }
}

export default async function Home() {
  const items = await getItems();
  return <Dashboard items={items} />;
}
