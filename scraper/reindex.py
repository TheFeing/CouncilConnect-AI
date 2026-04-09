import os   # OS interfaces for file path management
import json # For reading JSON backup files
import app.vector_store # Importing the VectorStoreManager class to interact with the Qdrant database

def rebuild_index():
    """
    Disaster Recovery (DR) automation.
    Reconstructs the Qdrant index from local JSON backups.
    This ensures AI's 'memory' can be recovered in minutes.
    """

    # 1. Connect to the database. Auto-create if missing
    db_manager = app.vector_store.VectorStoreManager(collection_name="council_knowledge")
    
    # 2. Define where the 'Safety Backups' are stored locally (same as ingest.py)
    backup_path = os.path.join(os.getcwd(), "knowledge_base", "processed")
    
    print("--- Starting Disaster Recovery Re-indexing ---")
    
    # 3. Check if we have any data to restore from
    if not os.path.exists(backup_path):
        print(f"Error: Backup path {backup_path} does not exist. Recovery aborted.")
        return

    # 4. Iterate through backup files and restore
    files_processed = 0
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
                    print(f"Successfully Restored: {filename}")
            except Exception as e:
                print(f"Failed to restore {filename}: {e}")

    print(f"--- Recovery Complete. Restored {files_processed} documents. ---")

if __name__ == "__main__":  # Auto-execute when run directly, but not when imported as a module
    rebuild_index()