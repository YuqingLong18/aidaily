import { prisma } from '@/lib/prisma';
import { Dashboard } from '@/components/Dashboard';
import { Item } from '@prisma/client';

// Revalidate every hour
export const revalidate = 3600;

async function getItems(): Promise<Item[]> {
  // Use UTC dates to match ingestion pipeline
  const now = new Date();
  const eightDaysAgo = new Date(Date.UTC(
    now.getUTCFullYear(),
    now.getUTCMonth(),
    now.getUTCDate() - 8,
    0, 0, 0, 0
  ));

  console.log(`[page.tsx] Fetching items published after: ${eightDaysAgo.toISOString()}`);
  
  try {
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
    });
    
    console.log(`[page.tsx] Found ${items.length} items`);
    console.log(`[page.tsx] Items breakdown: academic=${items.filter(i => i.type === 'academic').length}, industry=${items.filter(i => i.type === 'industry').length}`);
    
    // Log sample items for debugging
    if (items.length > 0) {
      const sample = items.slice(0, 3);
      console.log(`[page.tsx] Sample items:`, sample.map(i => ({
        title: i.title.substring(0, 40),
        type: i.type,
        category: i.category,
        publishedAt: i.publishedAt.toISOString(),
        hasSummary: !!i.summary,
        summaryEnLen: i.summaryEn?.length || 0,
        summaryZhLen: i.summaryZh?.length || 0,
      })));
    } else {
      console.warn(`[page.tsx] WARNING: No items found! This could indicate:`);
      console.warn(`  - Database connection issue`);
      console.warn(`  - Date filtering too restrictive`);
      console.warn(`  - No data ingested yet`);
      
      // Check total count
      const totalCount = await prisma.item.count();
      console.log(`[page.tsx] Total items in database: ${totalCount}`);
      
      if (totalCount > 0) {
        // Get the most recent item to see what dates we have
        const mostRecent = await prisma.item.findFirst({
          orderBy: { publishedAt: 'desc' },
        });
        if (mostRecent) {
          console.log(`[page.tsx] Most recent item published at: ${mostRecent.publishedAt.toISOString()}`);
          console.log(`[page.tsx] Cutoff date: ${eightDaysAgo.toISOString()}`);
        }
      }
    }
    
    return items;
  } catch (error) {
    console.error(`[page.tsx] Error fetching items:`, error);
    throw error;
  }
}

export default async function Home() {
  const items = await getItems();
  return <Dashboard items={items} />;
}
