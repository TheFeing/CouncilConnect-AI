import os           # OS interfaces for structural file path management
import json         # For parsing local JSON backup schemas
import logging      # Telemetry infrastructure for pipeline observability
import app.database # For VectorStoreManager connection engine

# Configure operational logging infrastructure for the reindexing subsystem.
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def rebuild_index():
    """
    Disaster Recovery (DR) automation.
    Reconstructs the Qdrant index from local JSON backups to restore the application's semantic memory.
    """

    # 1. Connect to the database. Auto-create if missing.
    # Corrected target reference module from 'app.vector_store' to 'app.database'.
    db_manager = app.database.VectorStoreManager(collection_name="council_knowledge")
    
    # 2. Define where the 'Safety Backups' are stored relative to this script's directory location.
    # Changed from os.getcwd() to guarantee path resolution inside automated container runtimes.
    base_dir = os.path.dirname(os.path.dirname(__file__))
    backup_path = os.path.join(base_dir, "knowledge_base", "processed")
    
    logger.info("--- Starting Disaster Recovery Re-indexing Phase ---")
    
    # 3. Check if the recovery source directories exist on the host file system
    if not os.path.exists(backup_path):
        logger.error(f"Critical Recovery Failure: Backup path {backup_path} does not exist. Execution aborted.")
        return

    # 4. Iterate through backup files and restore pipeline states
    files_processed = 0
    try:
        for filename in os.listdir(backup_path):
            if filename.endswith(".json"):
                file_full_path = os.path.join(backup_path, filename)
                
                try:
                    with open(file_full_path, 'r', encoding='utf-8') as f:  # Read mode with UTF-8 encoding to handle special characters
                        data = json.load(f)
                        
                        # Push the data back into the Vector Store
                        db_manager.upsert_document(
                            text=data['text'], 
                            metadata={
                                "source": data.get('url', 'unknown'), 
                                "restored": "true", # Restored documents are marked for traceability
                                "original_file": filename
                            }
                        )
              
                        files_processed += 1
                        logger.info(f"Successfully Restored Asset Document: {filename}")
                except Exception as file_error:
                    logger.error(f"Failed to restore individual record file {filename}: {str(file_error)}")
    except Exception as directory_error:
        logger.critical(f"Failed to read backup storage container directory: {str(directory_error)}")

    logger.info(f"--- Recovery Phase Complete. Restored {files_processed} documents to Vector Store. ---")


if __name__ == "__main__":  # Auto-execute when run directly, but not when imported as a module
    rebuild_index()