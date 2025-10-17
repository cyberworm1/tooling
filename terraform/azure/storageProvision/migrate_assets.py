import os
from azure.storage.blob import BlobServiceClient, BlobClient
from azure.identity import DefaultAzureCredential

def migrate_assets(local_dir, storage_account_name, container_name):
    credential = DefaultAzureCredential()
    blob_service_client = BlobServiceClient(account_url=f"https://{storage_account_name}.blob.core.windows.net", credential=credential)
    container_client = blob_service_client.get_container_client(container_name)
    
    for root, _, files in os.walk(local_dir):
        for file in files:
            local_path = os.path.join(root, file)
            blob_path = os.path.relpath(local_path, local_dir)
            blob_client = container_client.get_blob_client(blob_path)
            with open(local_path, "rb") as data:
                blob_client.upload_blob(data, blob_type="BlockBlob", overwrite=True, max_concurrency=4)  # Parallel for media throughput

# Usage: migrate_assets("/on-prem/game-assets", "yourstorageaccount", "game-assets")