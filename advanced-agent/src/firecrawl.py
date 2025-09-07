import os
from firecrawl import Firecrawl
from dotenv import load_dotenv

load_dotenv()

class FirecrawlService:
    def __init__(self):
        api_key = os.getenv("FIRECRAWL_API_KEY")
        if not api_key:
            raise ValueError("Missing FIRECRAWL_API_KEY in environment variables")
        self.app = Firecrawl(api_key=api_key)

    def search_companies(self,query:str ,num_results:int = 5):
        query = f"{query} company pricing"
        print(f"Searching for companies with query: {query}")
        try:
            result  = self.app.search(
                query=f"{query} company pricing",
                limit=num_results,
                integration="langchain",  # 或其他适合的集成选项
                scrape_options={
                    "formats": ["markdown"]
                }
            )
            return result
        except Exception as e:
            print(f"Error during search_companies in firecrawl: {e}")
            return []
    
    def scrape_company_page(self,url:str):
        try:
            result = self.app.scrape(
                url = url,
                formats = ["markdown"]
            )
            return result
        except Exception as e:
            print(f"Error during scrape_company_page: {e}")
            return None
    