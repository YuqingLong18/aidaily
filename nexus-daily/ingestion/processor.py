import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class LLMProcessor:
    def __init__(self):
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY"),
        )
        self.model = "google/gemini-2.0-flash-exp:free" # Cost-effective default

    def process_item(self, item):
        """
        Summarizes and classifies a single item.
        """
        prompt = f"""
        Analyze the following {item['type']} content:
        Title: {item['title']}
        Summary/Snippet: {item['summary']}
        
        Task:
        1. Classify it into ONE of these categories:
           - Academic: "AI for Science", "AI Theory & Architectures", "AI in Education"
           - Industry: "Product & Technology", "Market & Policy"
           If it doesn't fit well, choose the closest one.
           
        2. Create a structured summary:
           - 3-5 bullet points of key ideas.
           - 1 bullet point on "Why it matters".
           
        3. Assign a relevance score (0-10) based on impact and novelty.
        
        Output JSON format:
        {{
            "category": "Category Name",
            "summary_bullets": ["point 1", "point 2", ...],
            "why_it_matters": "explanation",
            "score": 8.5
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert AI analyst."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # Merge results back into item
            item['category'] = result.get('category', 'Uncategorized')
            item['summary'] = "\n".join([f"- {b}" for b in result.get('summary_bullets', [])])
            item['why_it_matters'] = result.get('why_it_matters', '')
            item['score'] = result.get('score', 0)
            
            return item
            
        except Exception as e:
            print(f"Error processing item {item['title']}: {e}")
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
