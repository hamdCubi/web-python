from similar_content import app as similar_content
from delete_file import app as delete_file
from unique_content import app as unique_content
from testCSV import app as testcsv
from extract_blog_links import app as extract_blog_links
from extractfilehtml import app as extractFIleHtml
from fastapi import FastAPI, Request, HTTPException
from generate_csv import app as generate_csv
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.responses import StreamingResponse
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv
import os
import uvicorn
import io
load_dotenv()
main_app = FastAPI()

# Azure Storage connection string
connect_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
blob_service_client = BlobServiceClient.from_connection_string(connect_str)
unique_container = "unique"

origins = [
    "http://localhost:3000",
    "https://ceab2bb2-97fe-427e-a123-a597551cdec4-00-2zbjbptvbtg7o.pike.replit.dev",
    # Add other allowed origins as needed
]

main_app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Or specify specific methods 
    allow_headers=["*"],  # Or specify specific headers
)

# Root endpoint
@main_app.get("/")
def read_root():
    return {"message": "Hello from the main app"}

# Route to fetch files from the unique container
@main_app.get("/uniqueFolder/{file_name}")
async def get_unique_file(file_name: str):
    blob_client = blob_service_client.get_blob_client(container=unique_container, blob=file_name)
    try:
        stream = blob_client.download_blob().readall()
        return StreamingResponse(io.BytesIO(stream), media_type='application/octet-stream', headers={"Content-Disposition": f"attachment; filename={file_name}"})
    except Exception as ex:
        raise HTTPException(status_code=404, detail=f"File not found: {str(ex)}")

# Mounting sub-applications
main_app.mount("/similar_content", similar_content)
main_app.mount("/test", testcsv)
main_app.mount("/delete_file", delete_file)
main_app.mount("/unique_content", unique_content)
main_app.mount("/extract_html", extractFIleHtml)
main_app.mount("/extract_blog_links", extract_blog_links)
main_app.mount("/generate_csv", generate_csv)

# Running the application with environment variables for host and port
# if __name__ == "__main__":
#     host = os.getenv("HOST", "0.0.0.0")
#     port = int(os.getenv("PORT", 8000))
#     uvicorn.run(main_app, host=host, port=port, reload=True)
