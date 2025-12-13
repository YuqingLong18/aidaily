import asyncio
import os
import sys
import time
import logging
from datetime import datetime, timezone

from prisma import Prisma

from image_utils import attach_images
from processor import LLMProcessor
from scraper import fetch_arxiv_papers, get_industry_news

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('ingestion.log')
    ]
)
logger = logging.getLogger(__name__)

def validate_item(item: dict):
    """Validate that an item has all required fields before saving."""
    required_fields = ['title', 'url', 'source', 'type', 'summary', 'category', 'score', 'published_at']
    for field in required_fields:
        if field not in item:
            return False, f"Missing required field: {field}"
        if not item[field]:
            if field != 'summary':  # summary can be empty if summaryEn/summaryZh exist
                return False, f"Empty required field: {field}"
    
    # At least one summary field must have content
    if not item.get('summary') and not item.get('summary_en') and not item.get('summary_zh'):
        return False, "All summary fields are empty"
    
    # Validate score is a number
    try:
        score = float(item['score'])
        if score < 0 or score > 10:
            return False, f"Invalid score: {score} (must be 0-10)"
    except (ValueError, TypeError):
        return False, f"Invalid score value: {item['score']}"
    
    return True, "OK"

def parse_published_at(date_str: str) -> datetime:
    """Robustly parse published_at string to UTC datetime."""
    try:
        # Try ISO format with Z
        if 'Z' in date_str:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        # Try ISO format with timezone
        if '+' in date_str or date_str.endswith('00:00'):
            return datetime.fromisoformat(date_str)
        # Try ISO format without timezone (assume UTC)
        if 'T' in date_str:
            dt = datetime.fromisoformat(date_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        # Fallback to current time
        logger.warning(f"Could not parse date '{date_str}', using current UTC time")
        return datetime.now(timezone.utc)
    except Exception as e:
        logger.error(f"Error parsing date '{date_str}': {e}, using current UTC time")
        return datetime.now(timezone.utc)

async def main():
    logger.info("=" * 80)
    logger.info("Starting ingestion pipeline...")
    logger.info(f"DATABASE_URL: {os.getenv('DATABASE_URL', 'NOT SET')[:50]}...")
    start_time = time.time()
    
    # 1. Fetch Data
    logger.info("Step 1: Fetching academic papers...")
    papers = fetch_arxiv_papers(max_results=10)
    logger.info(f"Fetched {len(papers)} academic papers")
    if papers:
        logger.info(f"Sample paper: {papers[0].get('title', 'N/A')[:60]}...")
    
    logger.info("Step 2: Fetching industry news...")
    news = get_industry_news()
    logger.info(f"Fetched {len(news)} industry news items")
    if news:
        logger.info(f"Sample news: {news[0].get('title', 'N/A')[:60]}...")
    
    all_items = papers + news
    logger.info(f"Total items fetched: {len(all_items)} (papers: {len(papers)}, news: {len(news)})")
    
    if len(all_items) == 0:
        logger.warning("No items fetched! Check network connectivity and source availability.")
        return
    
    # 2. Process with LLM
    logger.info("Step 3: Processing items with LLM...")
    processor = LLMProcessor()
    processed_items = []
    skipped_items = []
    
    for idx, item in enumerate(all_items, 1):
        item_title = item.get('title', 'Unknown')[:60]
        
        # Skip if summary is too short (likely garbage)
        summary_len = len(item.get('summary', ''))
        if summary_len < 50:
            logger.warning(f"[{idx}/{len(all_items)}] Skipping '{item_title}' - summary too short ({summary_len} chars)")
            skipped_items.append({'title': item_title, 'reason': f'summary too short ({summary_len} chars)'})
            continue
        
        logger.info(f"[{idx}/{len(all_items)}] Processing: {item_title}")
        try:
            processed = processor.process_item(item)
            if processed:
                # Validate processed item
                is_valid, validation_msg = validate_item(processed)
                if is_valid:
                    processed_items.append(processed)
                    logger.info(f"[{idx}/{len(all_items)}] ✓ Processed successfully: {item_title}")
                else:
                    logger.error(f"[{idx}/{len(all_items)}] ✗ Validation failed: {item_title} - {validation_msg}")
                    skipped_items.append({'title': item_title, 'reason': f'validation failed: {validation_msg}'})
            else:
                logger.warning(f"[{idx}/{len(all_items)}] ✗ LLM processing returned None: {item_title}")
                skipped_items.append({'title': item_title, 'reason': 'LLM processing returned None'})
        except Exception as e:
            logger.error(f"[{idx}/{len(all_items)}] ✗ Exception processing {item_title}: {e}", exc_info=True)
            skipped_items.append({'title': item_title, 'reason': f'exception: {str(e)}'})

    logger.info(f"Processing complete: {len(processed_items)} processed, {len(skipped_items)} skipped")
    if skipped_items:
        logger.info(f"Skipped items: {skipped_items}")

    if len(processed_items) == 0:
        logger.error("No items successfully processed! Cannot continue.")
        return

    # 2b. Fetch visual context for the selected cards
    logger.info("Step 4: Attaching images to selected items...")
    image_start = time.time()
    processed_items = attach_images(processed_items)
    items_with_images = sum(1 for i in processed_items if i.get('image_url'))
    logger.info(f"Image fetch complete in {time.time() - image_start:.2f}s; items with images: {items_with_images}/{len(processed_items)}")
            
    # 3. Save to DB
    logger.info("Step 5: Saving to database...")
    db = Prisma()
    
    try:
        logger.info("Connecting to database...")
        await db.connect()
        logger.info("Database connection established")
        
        # Verify connection by checking item count
        total_count = await db.item.count()
        logger.info(f"Current database contains {total_count} items")
        
        saved_count = 0
        duplicate_count = 0
        error_count = 0
        
        for idx, item in enumerate(processed_items, 1):
            item_title = item.get('title', 'Unknown')[:60]
            try:
                # Check if exists
                exists = await db.item.find_unique(where={'url': item['url']})
                if exists:
                    logger.info(f"[{idx}/{len(processed_items)}] Skipping duplicate: {item_title} (URL: {item['url'][:50]}...)")
                    duplicate_count += 1
                    continue
                
                # Parse published_at to UTC
                published_at = parse_published_at(item['published_at'])
                logger.debug(f"Parsed published_at: {item['published_at']} -> {published_at.isoformat()}")
                
                # Prepare data
                db_data = {
                    'title': item['title'],
                    'url': item['url'],
                    'source': item['source'],
                    'type': item['type'],
                    'summary': item.get('summary', ''),
                    'summaryEn': item.get('summary_en', ''),
                    'summaryZh': item.get('summary_zh', ''),
                    'whyItMattersEn': item.get('why_it_matters_en', ''),
                    'whyItMattersZh': item.get('why_it_matters_zh', ''),
                    'keywordsEn': ", ".join(item.get('keywords_en', [])) if item.get('keywords_en') else '',
                    'keywordsZh': ", ".join(item.get('keywords_zh', [])) if item.get('keywords_zh') else '',
                    'imageUrl': item.get('image_url'),
                    'imageAlt': item.get('image_alt'),
                    'category': item['category'],
                    'score': float(item['score']),
                    'publishedAt': published_at,
                }
                
                # Log data being saved (truncated for readability)
                logger.debug(f"Saving item data: title={db_data['title'][:40]}..., category={db_data['category']}, score={db_data['score']}, publishedAt={db_data['publishedAt']}")
                
                created = await db.item.create(data=db_data)
                saved_count += 1
                logger.info(f"[{idx}/{len(processed_items)}] ✓ Saved: {item_title} (ID: {created.id})")
                
            except Exception as e:
                error_count += 1
                logger.error(f"[{idx}/{len(processed_items)}] ✗ Error saving {item_title}: {e}", exc_info=True)
        
        logger.info(f"Database save complete: {saved_count} saved, {duplicate_count} duplicates, {error_count} errors")
        
        # Verify final count
        final_count = await db.item.count()
        logger.info(f"Database now contains {final_count} items (added {final_count - total_count})")
        
        # Query recent items to verify they're accessible
        recent_items = await db.item.find_many(
            take=5,
            order_by={'publishedAt': 'desc'}
        )
        logger.info(f"Recent items in DB: {[(i.title[:40], i.publishedAt.isoformat()) for i in recent_items]}")
        
    except Exception as e:
        logger.error(f"Database connection error: {e}", exc_info=True)
        raise
    finally:
        await db.disconnect()
        logger.info("Database connection closed")
    
    elapsed = time.time() - start_time
    logger.info("=" * 80)
    logger.info(f"Ingestion complete! Total time: {elapsed:.2f}s")
    logger.info(f"Summary: {len(all_items)} fetched, {len(processed_items)} processed, {saved_count} saved")
    logger.info("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())
