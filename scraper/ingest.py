import os               # OS interfaces for structural file path management
import json             # For compiling structural JSON backup documents
import uuid             # For generating unique tracking IDs for file assets
import logging          # Telemetry infrastructure for pipeline observability
import scraper.crawler  # For fetching local council domain contents
import scraper.redactor # For scrubbing unauthorised personal details from text
import app.database     # Connection path to the database infrastructure
import sys              # For system specific parameters and functions

# Configure operational logging infrastructure for the ingestion subsystem.
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_ingestion_pipeline(target_url: str):
    """
    Orchestrates the formal Fetch -> Redact -> Store ingestion pipeline.
    Ensures complete operational traceability and error management.
    """

    crawler = scraper.crawler.CouncilCrawler(target_url)
    vector_db = app.database.VectorStoreManager(collection_name="council_knowledge")

    # Define where the 'Safety Backups' are stored relative to this script's directory location.
    base_dir = os.path.dirname(os.path.dirname(__file__))
    backup_path = os.path.join(base_dir, "knowledge_base", "processed")
    
    try:
        os.makedirs(backup_path, exist_ok=True) # Ensure the directory exists before proceeding.
    except Exception as path_error:
        logger.error(f"Failed to initialise storage container layout: {str(path_error)}")
        return

    logger.info(f"--- Starting Ingestion Sequence For Target: {target_url} ---")
    
    # Fetch content from target node. The crawler should return a structured dictionary with a 'text' key containing the raw content string.
    raw_response = crawler.scrape_content(target_url)
    
    if raw_response and "text" in raw_response:
        # Extract the text string from the crawler's structured dictionary payload contract.
        raw_text = raw_response["text"]
        
        # Redact any private identifiers using the allow-list rules engine.
        safe_content = scraper.redactor.redact_pii(raw_text)

        # Save to local disk arrays to establish a Disaster Recovery recovery cache.
        backup_file = f"{uuid.uuid4().hex[:8]}.json"
        backup_data = {
            "url": target_url,
            "text": safe_content
        }
        
        try:
            full_file_path = os.path.join(backup_path, backup_file)
            with open(full_file_path, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=4)
            logger.info(f"Backup tracking asset written successfully for DR: {backup_file}")
        except Exception as write_error:
            logger.error(f"Disaster Recovery serialisation blocked by unexpected storage write failure: {str(write_error)}")

        # Store the scrubbed content block inside the active vector index
        try:
            doc_id = vector_db.upsert_document(
                safe_content, 
                metadata={"source_url": target_url} # Provides source traceability attributes
            )
            logger.info(f"Ingestion lifecycle completed. Content committed with Point ID: {doc_id}")
        except Exception as db_error:
            logger.critical(f"Vector Database commit sequence failed completely: {str(db_error)}")
    else:
        logger.error("Ingestion sequence aborted: No target text data could be extracted by the crawler.")


if __name__ == "__main__":
    # Check if a specific target URL argument was passed via the command line
    # E.g., python -m scraper.ingest "https://www.salford.gov.uk/bins-and-recycling/"
    if len(sys.argv) > 1:
        runtime_url = sys.argv[1]
        run_ingestion_pipeline(runtime_url)
    else:
        # Fallback default parameter for localised safety verifications
        logger.warning("No dynamic URL argument provided. Launching standard baseline verification path.")
        run_ingestion_pipeline("https://www.salford.gov.uk/council-tax/")