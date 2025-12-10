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

export function NewsCard({ item }: NewsCardProps) {
    const isAcademic = item.type === 'academic';

    return (
        <div className={`p-4 rounded-lg border ${isAcademic ? 'border-blue-200 bg-blue-50' : 'border-green-200 bg-green-50'} hover:shadow-md transition-shadow`}>
            <div className="flex justify-between items-start mb-2">
                <span className="text-xs font-semibold uppercase tracking-wider text-gray-500">
                    {item.category}
                </span>
                <span className="text-xs text-gray-400">
                    {new Date(item.publishedAt).toLocaleDateString()}
                </span>
            </div>

            <h3 className="text-lg font-bold mb-2 leading-tight">
                <a href={item.url} target="_blank" rel="noopener noreferrer" className="hover:underline text-gray-900">
                    {item.title}
                </a>
            </h3>

            <div className="text-sm text-gray-700 mb-3 whitespace-pre-line">
                {item.summary}
            </div>

            <div className="flex justify-between items-center mt-4">
                <span className="text-xs font-medium text-gray-500">
                    Source: {item.source}
                </span>
                <div className="flex items-center space-x-1">
                    <span className="text-xs font-bold text-gray-600">Score:</span>
                    <span className="text-xs font-bold text-indigo-600">{item.score.toFixed(1)}</span>
                </div>
            </div>
        </div>
    );
}
