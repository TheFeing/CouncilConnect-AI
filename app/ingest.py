import scraper.crawler
import scraper.redactor
import app.vector_store

def run_ingestion_pipeline(target_url):
    """
    Orchestrates the Fetch -> Redact -> Store flow.
    """

    crawler = scraper.crawler.CouncilCrawler(target_url)
    vector_db = app.vector_store.VectorStoreManager()
    print(f"--- Starting Ingestion for {target_url} ---")
    
    # 1. Fetch content
    raw_content = crawler.scrape_content(target_url)
    
    if raw_content:
        # 2. Redact PII
        safe_content = scraper.redactor.redact_pii(raw_content)

        # 3. Store in Vector DB
        doc_id = vector_db.upsert_document(
            safe_content, 
            metadata={"source_url": target_url}   # Provides metadata for future proofing and data traceability.
            )
        print(f"Success: Content stored with ID: {doc_id}")
    else:
        print("Error: No content retrieved.")

if __name__ == "__main__":  
    run_ingestion_pipeline("(https://www.salford.gov.uk/council-tax/)") 