import { prisma } from '@/lib/prisma';
import { Dashboard } from '@/components/Dashboard';
import { Item } from '@prisma/client';

// Revalidate every hour
export const revalidate = 3600;

async function getItems(): Promise<Item[]> {
  const eightDaysAgo = new Date();
  eightDaysAgo.setDate(eightDaysAgo.getDate() - 8);

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
  return items;
}

export default async function Home() {
  const items = await getItems();
  return <Dashboard items={items} />;
}
