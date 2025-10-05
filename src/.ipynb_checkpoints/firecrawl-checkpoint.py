import os
from firecrawl import FirecrawlApp, ScrapeOptions
from dotenv import load_dotenv

load_dotenv()

"""
This file is just to initialize our FireCrawl App service and provide some helper functions for it to access the services of 
firecrawl with. Now within this workflow, we can replace this file with any other external service or something else that we are 
using instead. 

The steps would be the same. We connect to the service within this file and produce helper functions within a class so that
we can assess the service and the functions within another class in another file.
"""

class FirecrawlService:

    # Initialize the service and connect to the Firecrawl app
    def __init__(self):

        firecrawl_api_key = os.environ("FIRECRAWL_API_KEY")

        if not firecrawl_api_key:
            raise ValueError("Missing API Key for FireCrawl")
        
        self.app = FirecrawlApp(api_key=firecrawl_api_key)


    # Tool: Search information about the company and its pricing given a query with the company name. Limit results to specified int
    def search_companies(self, query: str, num_results: int = 3):
        
        try:
            result = self.app.search(
                query=f"{query} company pricing",    # Assume that user only gives the name of the company so we want our search to be better so we add company pricing to query
                limit=num_results,      # Limit number of results to specified value
                scrape_options=ScrapeOptions(
                    formats=["markdown"]        # Good for processing with llms
                )
            )

            return result
        
        except Exception as e:
            print(f"Exception occured when searching for company: {e}")
            return []
        
    # Tool: Scrape company pages: given a url it will scrape the information off of this page
    def scrape_company_pages(self, url: str):
        try:
            result = self.app.scrape_url(
                url,
                formats=["markdown"]
            )
            return result
        except Exception as e:
            print(e)
            return None