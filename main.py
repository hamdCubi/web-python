from similar_content import app as similar_content
from delete_file import app as delete_file
from unique_content import app as unique_content
from extract_blog_links import app as extract_blog_links
from extractfilehtml import app as extractFIleHtml
from fastapi import FastAPI, Request, HTTPException
from generate_csv import app as generate_csv
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.staticfiles import StaticFiles
import os
import uvicorn

main_app = FastAPI()

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


# Directory for static files
output_folder = "uniqueFolder"
os.makedirs(output_folder, exist_ok=True)

# Mounting sub-applications
main_app.mount("/similar_content", similar_content)
main_app.mount("/delete_file", delete_file)
main_app.mount("/unique_content", unique_content)
main_app.mount("/extract_html", extractFIleHtml)
main_app.mount("/extract_blog_links", extract_blog_links)
main_app.mount("/generate_csv", generate_csv)
main_app.mount("/uniqueFolder",
               StaticFiles(directory=output_folder),
               name="uniqueFolder")

# Running the application with environment variables for host and port
if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(main_app, reload=True)
