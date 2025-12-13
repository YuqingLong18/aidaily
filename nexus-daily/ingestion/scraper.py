import requests
import feedparser
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
import time
import logging

logger = logging.getLogger(__name__)

def fetch_arxiv_papers(categories=['cs.LG', 'cs.AI', 'cs.CL', 'cs.CV', 'stat.ML'], max_results=50):
    """
    Fetches recent papers from arXiv for the given categories.
    """
    base_url = 'http://export.arxiv.org/api/query'
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=1)
    
    logger.info(f"Fetching arXiv papers from categories: {categories}, max_results={max_results}")
    logger.info(f"Cutoff date: {cutoff.isoformat()}")
    
    # Construct query
    # cat:cs.LG OR cat:cs.AI ...
    query = ' OR '.join([f'cat:{cat}' for cat in categories])
    
    params = {
        'search_query': query,
        'start': 0,
        'max_results': max_results,
        'sortBy': 'submittedDate',
        'sortOrder': 'descending'
    }
    
    try:
        logger.debug(f"Requesting: {base_url} with params: {params}")
        response = requests.get(base_url, params=params, timeout=30)
        response.raise_for_status()
        logger.debug(f"Response status: {response.status_code}, content length: {len(response.content)}")
        
        root = ET.fromstring(response.content)
        ns = {'atom': 'http://www.w3.org/2005/Atom', 'arxiv': 'http://arxiv.org/schemas/atom'}
        
        papers = []
        entries = root.findall('atom:entry', ns)
        logger.info(f"Found {len(entries)} entries in arXiv response")
        
        for idx, entry in enumerate(entries, 1):
            try:
                title = entry.find('atom:title', ns).text.strip().replace('\n', ' ')
                summary = entry.find('atom:summary', ns).text.strip().replace('\n', ' ')
                url = entry.find('atom:id', ns).text.strip()
                published = entry.find('atom:published', ns).text.strip()
                
                try:
                    published_dt = datetime.fromisoformat(published.replace('Z', '+00:00')).astimezone(timezone.utc)
                except Exception as e:
                    logger.warning(f"Error parsing date '{published}' for entry {idx}: {e}, using current time")
                    published_dt = now
                
                if published_dt < cutoff:
                    logger.debug(f"Skipping entry {idx} '{title[:40]}...' - published {published_dt.isoformat()} is before cutoff")
                    continue
                
                # Get primary category
                primary_cat = entry.find('arxiv:primary_category', ns).attrib['term']
                
                papers.append({
                    'title': title,
                    'url': url,
                    'summary': summary,
                    'source': 'arXiv',
                    'category': primary_cat,
                    'published_at': published_dt.isoformat(),
                    'type': 'academic'
                })
                logger.debug(f"Added paper {idx}: {title[:50]}... (published: {published_dt.isoformat()})")
            except Exception as e:
                logger.error(f"Error processing arXiv entry {idx}: {e}", exc_info=True)
                continue
            
        logger.info(f"Successfully fetched {len(papers)} papers from arXiv")
        return papers
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error fetching arXiv papers: {e}", exc_info=True)
        return []
    except Exception as e:
        logger.error(f"Error fetching arXiv papers: {e}", exc_info=True)
        return []

def fetch_rss_feed(url, source_name):
    """
    Fetches items from an RSS feed.
    """
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=1)
    
    logger.info(f"Fetching RSS feed: {url} (source: {source_name})")
    logger.debug(f"Cutoff date: {cutoff.isoformat()}")

    try:
        feed = feedparser.parse(url)
        logger.debug(f"Feed status: {feed.get('status', 'unknown')}, entries: {len(feed.entries)}")
        
        if feed.bozo:
            logger.warning(f"Feed parsing warnings for {url}: {feed.bozo_exception}")
        
        items = []
        
        for idx, entry in enumerate(feed.entries, 1):
            try:
                published_dt = None
                if getattr(entry, 'published_parsed', None):
                    published_dt = datetime.fromtimestamp(time.mktime(entry.published_parsed), tz=timezone.utc)
                elif getattr(entry, 'updated_parsed', None):
                    published_dt = datetime.fromtimestamp(time.mktime(entry.updated_parsed), tz=timezone.utc)
                elif getattr(entry, 'published', None):
                    try:
                        published_dt = parsedate_to_datetime(entry.published).astimezone(timezone.utc)
                    except Exception as e:
                        logger.debug(f"Error parsing date for entry {idx}: {e}")
                        published_dt = None

                if not published_dt:
                    logger.debug(f"Skipping entry {idx} - no valid published date")
                    continue

                if published_dt < cutoff:
                    logger.debug(f"Skipping entry {idx} '{entry.title[:40]}...' - published {published_dt.isoformat()} is before cutoff")
                    continue
                
                summary = getattr(entry, 'summary', '') or getattr(entry, 'description', '')
                items.append({
                    'title': entry.title,
                    'url': entry.link,
                    'summary': summary,
                    'source': source_name,
                    'published_at': published_dt.isoformat(),
                    'type': 'industry'
                })
                logger.debug(f"Added news item {idx}: {entry.title[:50]}... (published: {published_dt.isoformat()})")
            except Exception as e:
                logger.error(f"Error processing RSS entry {idx} from {source_name}: {e}", exc_info=True)
                continue
            
        logger.info(f"Successfully fetched {len(items)} items from {source_name}")
        return items
    except Exception as e:
        logger.error(f"Error fetching RSS feed {url}: {e}", exc_info=True)
        return []

def get_industry_news():
    """
    Aggregates industry news from multiple sources.
    """
    sources = [
        ('https://openai.com/blog/rss.xml', 'OpenAI'),
        ('https://research.google/blog/rss', 'Google Research'),
        ('https://www.anthropic.com/rss', 'Anthropic'),
        ('https://techcrunch.com/category/artificial-intelligence/feed/', 'TechCrunch AI'),
    ]
    
    logger.info(f"Fetching industry news from {len(sources)} sources")
    all_news = []
    for url, name in sources:
        news = fetch_rss_feed(url, name)
        all_news.extend(news)
        logger.info(f"  {name}: {len(news)} items")
    
    logger.info(f"Total industry news items: {len(all_news)}")
    return all_news

if __name__ == "__main__":
    # Test run
    print("Fetching arXiv papers...")
    papers = fetch_arxiv_papers(max_results=5)
    print(f"Found {len(papers)} papers")
    if papers:
        print(papers[0]['title'])
        
    print("\nFetching Industry news...")
    news = get_industry_news()
    print(f"Found {len(news)} news items")
    if news:
        print(news[0]['title'])
