from scraper.crawler import CouncilCrawler1
from scraper.redactor import redact_pii1

def run_ingestion_pipeline1(target_url1):
    crawler1 = CouncilCrawler1(target_url1)
    print(f"--- Starting Ingestion for {target_url1} ---")
   
    raw_content1 = crawler1.scrape_content1(target_url1)
   
    if raw_content1:
        safe_content1 = redact_pii1(raw_content1)
        # Placeholder for Sprint 5 Vector DB insertion
        print(f"Processed content length: {len(safe_content1)}")
        print(f"Preview: {safe_content1[:100]}...") # Show the first 100 characters as a sanity check
    else:
        print("No content retrieved.")

"""
Guarded entry point for running the ingestion pipeline.
 - Safety layer: Prevents unintended execution during imports
- Auto-run: Executes when the script is run directly
- Multiprocessing prevention: Avoids issues in environments that spawn subprocesses
"""
if __name__ == "__main__":  # Built-in variable "__name__" is assigned "__main__" when the script is run directly, otherwise it gets the module name "ingest" when imported
    run_ingestion_pipeline1("https://www.salford.gov.uk/council-tax/") # Default frequently accessed council page for testing