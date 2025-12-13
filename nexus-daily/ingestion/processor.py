import os
import json
import logging
import sys
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class LLMProcessor:
    def __init__(self):
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            logger.error("OPENROUTER_API_KEY not set! LLM processing will fail.")
        else:
            logger.info(f"Initializing LLMProcessor with API key: {api_key[:10]}...")
        
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )
        # Allow overriding the model via env; fall back to a cost-effective default.
        self.model = os.getenv("OPENROUTER_MODEL", "google/gemini-2.0-flash-exp:free")
        logger.info(f"Using model: {self.model}")

    def process_item(self, item):
        """
        Summarizes and classifies a single item, returning bilingual output.
        """
        item_title = item.get('title', 'Unknown')[:60]
        logger.debug(f"Processing item: {item_title}")
        
        prompt = f"""
        You are an expert AI analyst and translator. Analyze the following {item['type']} content:
        Title: {item['title']}
        Summary/Snippet: {item['summary']}

        Tasks:
        1) Classify it into ONE of these categories (keep exact labels):
           Academic: "AI for Science", "AI Theory & Architectures", "AI in Education"
           Industry: "Product & Technology", "Market & Policy"
        2) Create a structured summary with 3-5 concise bullets in English, and provide a faithful, professional Chinese translation of those bullets.
        3) Provide one-line "Why it matters" in English AND a precise Chinese translation.
        4) Provide exactly 3 high-signal keywords/highlights in English AND Chinese.
        5) Assign a relevance score (0-10) based on impact and novelty.

        Output JSON:
        {{
          "category": "Category Name",
          "summary_bullets_en": ["..."],
          "summary_bullets_zh": ["..."],
          "why_it_matters_en": "...",
          "why_it_matters_zh": "...",
          "keywords_en": ["kw1","kw2","kw3"],
          "keywords_zh": ["词1","词2","词3"],
          "score": 8.5
        }}
        """
        
        try:
            logger.debug(f"Calling LLM API for: {item_title}")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert AI analyst."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            raw_content = response.choices[0].message.content
            logger.debug(f"LLM response received (length: {len(raw_content)} chars)")
            
            result = json.loads(raw_content)
            logger.debug(f"Parsed JSON result: category={result.get('category')}, score={result.get('score')}")
            
            # Merge results back into item
            summary_bullets_en = result.get('summary_bullets_en') or result.get('summary_bullets') or []
            summary_bullets_zh = result.get('summary_bullets_zh') or []
            keywords_en = result.get('keywords_en') or []
            keywords_zh = result.get('keywords_zh') or []

            if not summary_bullets_en:
                logger.warning(f"No English summary bullets found for: {item_title}")
            if not summary_bullets_zh:
                logger.warning(f"No Chinese summary bullets found for: {item_title}")

            item['category'] = result.get('category', 'Uncategorized')
            item['summary'] = "\n".join([f"- {b}" for b in summary_bullets_en]) if summary_bullets_en else item.get('summary', '')
            item['summary_en'] = "\n".join([f"- {b}" for b in summary_bullets_en]) if summary_bullets_en else ''
            item['summary_zh'] = "\n".join([f"- {b}" for b in summary_bullets_zh]) if summary_bullets_zh else ''
            item['why_it_matters'] = result.get('why_it_matters_en', '') or result.get('why_it_matters', '')
            item['why_it_matters_en'] = result.get('why_it_matters_en', '') or result.get('why_it_matters', '')
            item['why_it_matters_zh'] = result.get('why_it_matters_zh', '')
            item['keywords_en'] = keywords_en
            item['keywords_zh'] = keywords_zh
            item['score'] = result.get('score', 0)
            
            # Log what we got
            logger.debug(f"Processed item fields: category={item['category']}, score={item['score']}, "
                        f"summary_en_len={len(item['summary_en'])}, summary_zh_len={len(item['summary_zh'])}, "
                        f"keywords_en={item['keywords_en']}")
            
            return item
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error processing {item_title}: {e}")
            logger.error(f"Raw response: {raw_content[:500] if 'raw_content' in locals() else 'N/A'}")
            return None
        except Exception as e:
            logger.error(f"Error processing item {item_title}: {e}", exc_info=True)
            return None

if __name__ == "__main__":
    # Test
    processor = LLMProcessor()
    test_item = {
        'title': 'Attention Is All You Need',
        'summary': 'We propose a new simple network architecture, the Transformer, based solely on attention mechanisms.',
        'type': 'academic'
    }
    print(processor.process_item(test_item))
