import os   # Used for accessing environment variables, allowing for secure configuration without hardcoding sensitive information.
import azure.identity   # Provides various credential classes for authenticating with Azure services (e.g., Managed Identity).
import azure.keyvault.secrets   # For interacting with Azure Key Vault to retrieve secrets securely at runtime.

class SecretManager:
    """
    Implements a 'Secret-less' pattern (K15).
    Fetches credentials from Azure Key Vault using Managed Identity.
    This class encapsulates the complexity of cloud authentication.
    """
	
    def __init__(self):
        self.vault_url = os.getenv("VAULT_URL")	# Retrieve Vault URL from env variable set by Terraform.
        self.credential = azure.identity.DefaultAzureCredential()	# Automatically use the best available auth method based on environment.
        
    def get_secret(self, secret_name: str) -> str:
        """
        Retrieves a secret value by its name.
		Falls back to local env variables if values not found, ensuring app can still run in dev env.
        """
		
        if not self.vault_url:
            print(f"Warning: VAULT_URL not found. Falling back to local env for {secret_name}")
            return os.getenv(secret_name, "")
            
        try:
            client = azure.keyvault.secrets.SecretClient(vault_url=self.vault_url, credential=self.credential)	# Create client instance for the Key Vault using the vault URL & credential.
            retrieved_secret = client.get_secret(secret_name)
            return retrieved_secret.value	# Runtime fetching in RAM only, never stored elsewhere.
        except Exception as e:
            print(f"Security Error: Could not retrieve {secret_name} from Vault. {e}")
            return os.getenv(secret_name, "")