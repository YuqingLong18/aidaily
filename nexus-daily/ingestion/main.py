import asyncio
from scraper import fetch_arxiv_papers, get_industry_news
from processor import LLMProcessor
from prisma import Prisma
import os

async def main():
    print("Starting ingestion pipeline...")
    
    # 1. Fetch Data
    print("Fetching academic papers...")
    papers = fetch_arxiv_papers(max_results=10)
    
    print("Fetching industry news...")
    news = get_industry_news()
    
    all_items = papers + news
    print(f"Total items fetched: {len(all_items)}")
    
    # 2. Process with LLM
    processor = LLMProcessor()
    processed_items = []
    
    print("Processing items with LLM...")
    for item in all_items:
        # Skip if summary is too short (likely garbage)
        if len(item['summary']) < 50:
            continue
            
        processed = processor.process_item(item)
        if processed:
            processed_items.append(processed)
            print(f"Processed: {processed['title']}")
            
    # 3. Save to DB
    print("Saving to database...")
    db = Prisma()
    await db.connect()
    
    for item in processed_items:
        try:
            # Check if exists
            exists = await db.item.find_unique(where={'url': item['url']})
            if exists:
                print(f"Skipping duplicate: {item['title']}")
                continue
                
            await db.item.create(data={
                'title': item['title'],
                'url': item['url'],
                'source': item['source'],
                'type': item['type'],
                'summary': item['summary'] + "\n\n**Why it matters:** " + item.get('why_it_matters', ''),
                'category': item['category'],
                'score': float(item['score']),
                'publishedAt': datetime.fromisoformat(item['published_at'].replace('Z', '+00:00')) if 'T' in item['published_at'] else datetime.now(), # Simple parsing fix needed for robust prod
            })
            print(f"Saved: {item['title']}")
            
        except Exception as e:
            print(f"Error saving {item['title']}: {e}")
            
    await db.disconnect()
    print("Ingestion complete!")

if __name__ == "__main__":
    from datetime import datetime
    asyncio.run(main())
