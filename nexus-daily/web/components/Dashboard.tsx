'use client';

import { useMemo, useState } from 'react';
import { Item } from '@prisma/client';
import { NewsCard } from './NewsCard';

type Language = 'en' | 'zh';
const MAX_DAYS = 7;

const labels = {
  en: {
    title: 'Nexus AI Daily',
    subtitle: 'Daily Intelligence Dashboard',
    academicHub: 'Academic Intelligence Hub',
    industryHub: 'Industry Intelligence Hub',
    noAcademic: 'No academic items found today.',
    noIndustry: 'No industry items found today.',
    language: 'Language',
    english: 'English',
    chinese: '中文',
    selectDay: 'Select Day',
  },
  zh: {
    title: 'Nexus AI 每日情报',
    subtitle: '每日情报看板',
    academicHub: '学术情报中心',
    industryHub: '产业情报中心',
    noAcademic: '今天暂无学术更新。',
    noIndustry: '今天暂无产业更新。',
    language: '语言',
    english: 'English',
    chinese: '中文',
    selectDay: '选择日期',
  },
};

export function Dashboard({ items }: { items: Item[] }) {
  const [language, setLanguage] = useState<Language>('en');
  const [daysAgo, setDaysAgo] = useState<number>(0);
  const locale = language === 'zh' ? 'zh-CN' : 'en-US';
  const headerFormatter = useMemo(
    () =>
      new Intl.DateTimeFormat(locale, {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        timeZone: 'UTC',
      }),
    [locale]
  );
  const dayChipFormatter = useMemo(
    () =>
      new Intl.DateTimeFormat(locale, {
        month: 'short',
        day: 'numeric',
        timeZone: 'UTC',
      }),
    [locale]
  );
  const publishedDateFormatter = useMemo(
    () =>
      new Intl.DateTimeFormat(locale, {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        timeZone: 'UTC',
      }),
    [locale]
  );

  const filteredItems = useMemo(() => {
    // Use UTC dates to match server-side filtering
    const now = new Date();
    const target = new Date(Date.UTC(
      now.getUTCFullYear(),
      now.getUTCMonth(),
      now.getUTCDate() - daysAgo,
      0, 0, 0, 0
    ));
    const nextDay = new Date(Date.UTC(
      now.getUTCFullYear(),
      now.getUTCMonth(),
      now.getUTCDate() - daysAgo + 1,
      0, 0, 0, 0
    ));

    const filtered = items.filter(item => {
      const itemDate = new Date(item.publishedAt);
      // Check if item is within the target day (UTC)
      return itemDate >= target && itemDate < nextDay;
    });
    
    // Debug logging in development
    if (process.env.NODE_ENV === 'development') {
      console.log(`[Dashboard] Filtering items: daysAgo=${daysAgo}, target=${target.toISOString()}, found=${filtered.length} items`);
    }
    
    return filtered;
  }, [items, daysAgo]);

  const academicItems = useMemo(() => filteredItems.filter(i => i.type === 'academic'), [filteredItems]);
  const industryItems = useMemo(() => filteredItems.filter(i => i.type === 'industry'), [filteredItems]);
  const t = labels[language];

  return (
    <main className="min-h-screen bg-gray-50 p-8 font-sans">
      <header className="mb-8 border-b pb-4">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-3xl font-extrabold text-gray-900 tracking-tight">{t.title}</h1>
            <p className="text-gray-500 mt-1">{t.subtitle}</p>
          </div>
          <div className="flex items-center gap-3">
            <p className="text-sm font-medium text-gray-600">
              {headerFormatter.format(new Date())}
            </p>
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold uppercase tracking-[0.08em] text-gray-500">
                {t.selectDay}
              </span>
              <div className="flex flex-wrap gap-2">
                {Array.from({ length: MAX_DAYS }, (_, idx) => {
                  const now = new Date();
                  const target = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate() - idx));
                  const label =
                    idx === 0
                      ? language === 'zh' ? '今天' : 'Today'
                      : dayChipFormatter.format(target);

                  return (
                    <button
                      key={idx}
                      onClick={() => setDaysAgo(idx)}
                      className={`px-3 py-1 text-xs font-semibold rounded-full border transition ${
                        daysAgo === idx
                          ? 'bg-gray-900 text-white border-gray-900 shadow'
                          : 'bg-white text-gray-700 border-gray-200 hover:border-gray-400'
                      }`}
                    >
                      {label}
                    </button>
                  );
                })}
              </div>
            </div>
            <div className="flex rounded-full border border-gray-200 bg-white shadow-sm">
              <button
                className={`px-3 py-1 text-sm font-semibold rounded-full transition ${
                  language === 'en' ? 'bg-gray-900 text-white shadow' : 'text-gray-600'
                }`}
                onClick={() => setLanguage('en')}
                aria-label="Switch to English"
              >
                {t.english}
              </button>
              <button
                className={`px-3 py-1 text-sm font-semibold rounded-full transition ${
                  language === 'zh' ? 'bg-gray-900 text-white shadow' : 'text-gray-600'
                }`}
                onClick={() => setLanguage('zh')}
                aria-label="切换到中文"
              >
                {t.chinese}
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <section>
          <h2 className="text-xl font-bold text-blue-800 mb-4 flex items-center border-b-2 border-blue-800 pb-2">
            <span className="mr-2">🎓</span> {t.academicHub}
          </h2>
          <div className="space-y-4">
            {academicItems.length > 0 ? (
              academicItems.map(item => <NewsCard key={item.id} item={item} language={language} dateFormatter={publishedDateFormatter} />)
            ) : (
              <p className="text-gray-500 italic">{t.noAcademic}</p>
            )}
          </div>
        </section>

        <section>
          <h2 className="text-xl font-bold text-green-800 mb-4 flex items-center border-b-2 border-green-800 pb-2">
            <span className="mr-2">🏢</span> {t.industryHub}
          </h2>
          <div className="space-y-4">
            {industryItems.length > 0 ? (
              industryItems.map(item => <NewsCard key={item.id} item={item} language={language} dateFormatter={publishedDateFormatter} />)
            ) : (
              <p className="text-gray-500 italic">{t.noIndustry}</p>
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
