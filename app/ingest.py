import os   # OS interfaces for file path management
import json # For reading JSON backup files
import uuid # For generating unique document IDs
import scraper.crawler  # Importing the CouncilCrawler class to fetch content from target URLs
import scraper.redactor # Importing the redactor module for PII redaction
import app.vector_store # Importing the VectorStoreManager class to interact with the Qdrant database

def run_ingestion_pipeline(target_url):
    """
    Orchestrates the Fetch -> Redact -> Store flow.
    """

    crawler = scraper.crawler.CouncilCrawler(target_url)
    vector_db = app.vector_store.VectorStoreManager()

    # 1. Define and ensure the backup path exists for Continuity
    backup_path = os.path.join(os.getcwd(), "knowledge_base", "processed")
    os.makedirs(backup_path, exist_ok=True) # "exist_ok" (predefined parameter) prevents an error if the directory already exists.

    print(f"--- Starting Ingestion for {target_url} ---")
    
    # 2. Fetch content
    raw_content = crawler.scrape_content(target_url)
    
    if raw_content:
        # 3. Redact PII
        safe_content = scraper.redactor.redact_pii(raw_content)

        # 4. Save to local disk (where app runs) for Disaster Recovery
        backup_file = f"{uuid.uuid4().hex[:8]}.json"
        backup_data = {
            "url": target_url,
            "text": safe_content
        }
        
        with open(os.path.join(backup_path, backup_file), 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, indent=4)
        print(f"Backup saved for DR: {backup_file}")

        # 5. Store in Vector DB
        doc_id = vector_db.upsert_document(
            safe_content, 
            metadata={"source_url": target_url}   # Provides metadata for future proofing and data traceability.
            )
        print(f"Success: Content stored with ID: {doc_id}")
    else:
        print("Error: No content retrieved.")

if __name__ == "__main__":  # Auto-execute when run directly, but not when imported as a module
    run_ingestion_pipeline("https://www.salford.gov.uk/council-tax/") 