import { prisma } from '@/lib/prisma';
import { Dashboard } from '@/components/Dashboard';
import { Item } from '@prisma/client';

// Use dynamic rendering to avoid build-time database connection issues
// Revalidate every hour in production
export const dynamic = 'force-dynamic';
export const revalidate = 3600;

// Only log in development or when DEBUG is enabled
const isDebug = process.env.NODE_ENV === 'development' || process.env.DEBUG === 'true';

async function getItems(): Promise<Item[]> {
  // Use UTC dates to match ingestion pipeline
  const now = new Date();
  const eightDaysAgo = new Date(Date.UTC(
    now.getUTCFullYear(),
    now.getUTCMonth(),
    now.getUTCDate() - 8,
    0, 0, 0, 0
  ));

  if (isDebug) {
    console.log(`[page.tsx] Fetching items published after: ${eightDaysAgo.toISOString()}`);
  }
  
  try {
    // Limit items during build to prevent memory issues
    // In production, this will be revalidated hourly anyway
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
    
    if (isDebug) {
      const academicCount = items.filter(i => i.type === 'academic').length;
      const industryCount = items.filter(i => i.type === 'industry').length;
      console.log(`[page.tsx] Found ${items.length} items (academic: ${academicCount}, industry: ${industryCount})`);
      
      // Log sample items for debugging (simplified to avoid memory issues)
      if (items.length > 0) {
        const sample = items.slice(0, 2);
        for (const item of sample) {
          console.log(`[page.tsx] Sample: ${item.title.substring(0, 50)}... (${item.type}, ${item.category})`);
        }
      }
    }
    
    // Only do additional queries if no items found (to avoid build-time overhead)
    if (items.length === 0 && isDebug) {
      console.warn(`[page.tsx] WARNING: No items found!`);
      
      try {
        const totalCount = await prisma.item.count();
        console.log(`[page.tsx] Total items in database: ${totalCount}`);
        
        if (totalCount > 0) {
          const mostRecent = await prisma.item.findFirst({
            orderBy: { publishedAt: 'desc' },
            select: { publishedAt: true },
          });
          if (mostRecent) {
            console.log(`[page.tsx] Most recent: ${mostRecent.publishedAt.toISOString()}, Cutoff: ${eightDaysAgo.toISOString()}`);
          }
        }
      } catch (dbError) {
        // Don't fail build if diagnostic query fails
        if (isDebug) {
          console.warn(`[page.tsx] Could not run diagnostic queries:`, dbError);
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
