from scraper.crawler import CouncilCrawler1
from scraper.redactor import redact_pii1
from app.vector_store import VectorStoreManager1

def run_ingestion_pipeline1(target_url1):
    """
    Orchestrates the Fetch -> Redact -> Store flow.
    """

    crawler1 = CouncilCrawler1(target_url1)
    vector_db1 = VectorStoreManager1()
    print(f"--- Starting Ingestion for {target_url1} ---")
   
    # 1. Fetch content
    raw_content1 = crawler1.scrape_content1(target_url1)
   
    if raw_content1:
        # 2. Redact PII
        safe_content1 = redact_pii1(raw_content1)
        # print(f"Processed content length: {len(safe_content1)}")
        # print(f"Preview: {safe_content1[:100]}...") # Show the first 100 characters as a sanity check

        # 3. Store in Vector DB
        doc_id1 = vector_db1.upsert_document1(
            safe_content1,
            metadata1={"source_url": target_url1}   # Provides metadata for future proofing and data traceability.
            )
        print(f"Success: Content stored with ID: {doc_id1}")
    else:
        print("Error: No content retrieved.")

"""
Guarded entry point for running the ingestion pipeline.
 - Safety layer: Prevents unintended execution during imports
- Auto-run: Executes when the script is run directly
- Multiprocessing prevention: Avoids issues in environments that spawn subprocesses
"""
if __name__ == "__main__":  # Built-in variable "__name__" is assigned "__main__" when the script is run directly, otherwise it gets this module/script name when imported
    run_ingestion_pipeline1("https://www.salford.gov.uk/council-tax/") # Default frequently accessed council page for testing