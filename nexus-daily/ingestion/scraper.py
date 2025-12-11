import requests
import feedparser
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
import time

def fetch_arxiv_papers(categories=['cs.LG', 'cs.AI', 'cs.CL', 'cs.CV', 'stat.ML'], max_results=50):
    """
    Fetches recent papers from arXiv for the given categories.
    """
    base_url = 'http://export.arxiv.org/api/query'
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=1)
    
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
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        
        root = ET.fromstring(response.content)
        ns = {'atom': 'http://www.w3.org/2005/Atom', 'arxiv': 'http://arxiv.org/schemas/atom'}
        
        papers = []
        for entry in root.findall('atom:entry', ns):
            title = entry.find('atom:title', ns).text.strip().replace('\n', ' ')
            summary = entry.find('atom:summary', ns).text.strip().replace('\n', ' ')
            url = entry.find('atom:id', ns).text.strip()
            published = entry.find('atom:published', ns).text.strip()
            try:
                published_dt = datetime.fromisoformat(published.replace('Z', '+00:00')).astimezone(timezone.utc)
            except Exception:
                published_dt = now
            if published_dt < cutoff:
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
            
        return papers
        
    except Exception as e:
        print(f"Error fetching arXiv papers: {e}")
        return []

def fetch_rss_feed(url, source_name):
    """
    Fetches items from an RSS feed.
    """
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=1)

    try:
        feed = feedparser.parse(url)
        items = []
        
        for entry in feed.entries:
            published_dt = None
            if getattr(entry, 'published_parsed', None):
                published_dt = datetime.fromtimestamp(time.mktime(entry.published_parsed), tz=timezone.utc)
            elif getattr(entry, 'updated_parsed', None):
                published_dt = datetime.fromtimestamp(time.mktime(entry.updated_parsed), tz=timezone.utc)
            elif getattr(entry, 'published', None):
                try:
                    published_dt = parsedate_to_datetime(entry.published).astimezone(timezone.utc)
                except Exception:
                    published_dt = None

            if not published_dt:
                continue

            if published_dt < cutoff:
                continue
            
            items.append({
                'title': entry.title,
                'url': entry.link,
                'summary': getattr(entry, 'summary', '') or getattr(entry, 'description', ''),
                'source': source_name,
                'published_at': published_dt.isoformat(),
                'type': 'industry'
            })
            
        return items
    except Exception as e:
        print(f"Error fetching RSS feed {url}: {e}")
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
    
    all_news = []
    for url, name in sources:
        news = fetch_rss_feed(url, name)
        all_news.extend(news)
        
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
