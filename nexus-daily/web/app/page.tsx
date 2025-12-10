import { prisma } from '@/lib/prisma';
import { NewsCard } from '@/components/NewsCard';

// Revalidate every hour
export const revalidate = 3600;

async function getItems() {
  const items = await prisma.item.findMany({
    orderBy: { score: 'desc' },
    take: 50,
  });
  return items;
}

export default async function Home() {
  const items = await getItems();

  const academicItems = items.filter(i => i.type === 'academic');
  const industryItems = items.filter(i => i.type === 'industry');

  return (
    <main className="min-h-screen bg-gray-50 p-8 font-sans">
      <header className="mb-8 border-b pb-4">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-extrabold text-gray-900 tracking-tight">Nexus AI Daily</h1>
            <p className="text-gray-500 mt-1">Daily Intelligence Dashboard</p>
          </div>
          <div className="text-right">
            <p className="text-sm font-medium text-gray-600">{new Date().toLocaleDateString(undefined, { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}</p>
          </div>
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Academic Column */}
        <section>
          <h2 className="text-xl font-bold text-blue-800 mb-4 flex items-center border-b-2 border-blue-800 pb-2">
            <span className="mr-2">🎓</span> Academic Intelligence Hub
          </h2>
          <div className="space-y-4">
            {academicItems.length > 0 ? (
              academicItems.map(item => (
                <NewsCard key={item.id} item={item} />
              ))
            ) : (
              <p className="text-gray-500 italic">No academic items found today.</p>
            )}
          </div>
        </section>

        {/* Industry Column */}
        <section>
          <h2 className="text-xl font-bold text-green-800 mb-4 flex items-center border-b-2 border-green-800 pb-2">
            <span className="mr-2">🏢</span> Industry Intelligence Hub
          </h2>
          <div className="space-y-4">
            {industryItems.length > 0 ? (
              industryItems.map(item => (
                <NewsCard key={item.id} item={item} />
              ))
            ) : (
              <p className="text-gray-500 italic">No industry items found today.</p>
            )}
          </div>
        </section>
      </div>

      <footer className="mt-12 pt-8 border-t text-center text-gray-400 text-sm">
        <p>© {new Date().getFullYear()} Nexus AI Daily. Powered by OpenRouter.</p>
      </footer>
    </main>
  );
}
