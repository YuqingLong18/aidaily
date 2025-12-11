import React from 'react';

interface Item {
    id: string;
    title: string;
    url: string;
    source: string;
    type: string;
    summary: string;
    category: string;
    score: number;
    publishedAt: Date;
}

interface NewsCardProps {
    item: Item;
}

function parseSummary(summary: string) {
    const lines = summary
        .split('\n')
        .map(line => line.trim())
        .filter(Boolean);

    const bullets: string[] = [];
    let whyItMatters: string | null = null;

    lines.forEach(line => {
        const lower = line.toLowerCase();
        if (lower.startsWith('**why it matters')) {
            whyItMatters = line.replace(/^\*\*why it matters:\*\*\s*/i, '').trim();
            return;
        }

        if (line.startsWith('-')) {
            bullets.push(line.replace(/^-+\s*/, '').trim());
        } else {
            bullets.push(line);
        }
    });

    return { bullets, whyItMatters };
}

export function NewsCard({ item }: NewsCardProps) {
    const isAcademic = item.type === 'academic';
    const { bullets, whyItMatters } = parseSummary(item.summary || '');
    const publishedDate = new Date(item.publishedAt);

    return (
        <div className={`p-5 rounded-xl border ${isAcademic ? 'border-blue-200 bg-blue-50/70' : 'border-green-200 bg-green-50/70'} hover:shadow-md transition-shadow`}>
            <div className="flex justify-between items-start mb-3">
                <span className="text-[11px] font-semibold uppercase tracking-[0.12em] text-gray-500">
                    {item.category}
                </span>
                <span className="text-xs text-gray-400">
                    {publishedDate.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })}
                </span>
            </div>

            <h3 className="text-xl font-extrabold mb-3 leading-snug text-gray-900">
                <a href={item.url} target="_blank" rel="noopener noreferrer" className="hover:underline text-gray-900">
                    {item.title}
                </a>
            </h3>

            {bullets.length > 0 && (
                <ul className="text-sm text-gray-800 mb-4 space-y-2">
                    {bullets.map((point, idx) => (
                        <li key={idx} className="flex gap-3">
                            <span className={`mt-2 h-2 w-2 rounded-full ${isAcademic ? 'bg-blue-400' : 'bg-green-400'}`} />
                            <span className="leading-relaxed">{point}</span>
                        </li>
                    ))}
                </ul>
            )}

            {whyItMatters && (
                <div className="mt-2 rounded-lg border border-dashed border-gray-200 bg-white/70 px-4 py-3">
                    <p className={`text-[11px] font-semibold uppercase tracking-[0.1em] mb-1 ${isAcademic ? 'text-blue-700' : 'text-green-700'}`}>
                        Why it matters
                    </p>
                    <p className="text-sm text-gray-800 leading-relaxed">{whyItMatters}</p>
                </div>
            )}

            <div className="flex justify-between items-center mt-4">
                <span className="text-xs font-medium text-gray-500">
                    Source: {item.source}
                </span>
                <span className="text-xs font-bold text-gray-600">
                    Score: <span className="text-xs font-extrabold text-indigo-600">{item.score.toFixed(1)}</span>
                </span>
            </div>
        </div>
    );
}
