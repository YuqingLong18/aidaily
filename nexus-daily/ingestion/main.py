import asyncio
import os
import time
from datetime import datetime

from prisma import Prisma

from image_utils import attach_images
from processor import LLMProcessor
from scraper import fetch_arxiv_papers, get_industry_news

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

    # 2b. Fetch visual context for the selected cards
    print("Attaching images to selected items...")
    image_start = time.time()
    processed_items = attach_images(processed_items)
    print(f"Image fetch complete in {time.time() - image_start:.2f}s; items with images: {sum(1 for i in processed_items if i.get('image_url'))}/{len(processed_items)}")
            
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
                'summary': item['summary'],
                'summaryEn': item.get('summary_en', ''),
                'summaryZh': item.get('summary_zh', ''),
                'whyItMattersEn': item.get('why_it_matters_en', ''),
                'whyItMattersZh': item.get('why_it_matters_zh', ''),
                'keywordsEn': ", ".join(item.get('keywords_en', [])),
                'keywordsZh': ", ".join(item.get('keywords_zh', [])),
                'imageUrl': item.get('image_url'),
                'imageAlt': item.get('image_alt'),
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
    asyncio.run(main())
