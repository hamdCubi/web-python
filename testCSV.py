import os
from fastapi import FastAPI, HTTPException
import csv
import datetime
from azure.storage.blob import BlobServiceClient
from io import StringIO
from dotenv import load_dotenv
app = FastAPI()
load_dotenv()
# Azure Storage connection string
connect_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
blob_service_client = BlobServiceClient.from_connection_string(connect_str)

# Containers
savecsv_container = "savecsv"

# Function to upload a file to Azure Blob Storage
def upload_file_to_container(container_name, file_name, file_content):
    try:
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=file_name)
        blob_client.upload_blob(file_content, overwrite=True)
        print(f"Uploaded {file_name} to {container_name} container.")
    except Exception as ex:
        print(f"Exception: {ex}")
        raise HTTPException(status_code=500, detail="Failed to upload file to Azure Storage.")

@app.get("/test-upload")
async def test_upload():
    current_datetime = datetime.datetime.now()
    timestamp = int(current_datetime.timestamp())
    csv_file_name = f"test-{timestamp}.csv"

    # Dummy data to test the upload process
    dummy_data = [
        {"Title": "Test Title 1", "Publish Date": "2024-08-19", "Meta Description": "Test Description 1", "Canonical Link": "http://example.com/1", "Article Content": "Test content 1", "Yoast Schema Graph": "Test schema 1"},
        {"Title": "Test Title 2", "Publish Date": "2024-08-19", "Meta Description": "Test Description 2", "Canonical Link": "http://example.com/2", "Article Content": "Test content 2", "Yoast Schema Graph": "Test schema 2"}
    ]

    # Use StringIO as an in-memory file
    csv_buffer = StringIO()
    fieldnames = ["Title", "Publish Date", "Meta Description", "Canonical Link", "Article Content", "Yoast Schema Graph"]
    writer = csv.DictWriter(csv_buffer, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(dummy_data)

    # Get the CSV content from the buffer
    csv_content = csv_buffer.getvalue()

    # Upload the CSV content to Azure Storage
    upload_file_to_container(savecsv_container, csv_file_name, csv_content)

    return {"Message": "Test upload complete.", "fileName": csv_file_name}
