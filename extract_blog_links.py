import requests
from bs4 import BeautifulSoup
from urllib.parse import unquote
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from datetime import datetime
import os
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv

app = FastAPI()
load_dotenv()

class Progress(BaseModel):
    current_page: int
    links_extracted: int
    total_links: int

progress = Progress(current_page=0, links_extracted=0, total_links=0)

# Azure Storage connection string
connect_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
blob_service_client = BlobServiceClient.from_connection_string(connect_str)

def upload_file_to_container(container_name, file_name, file_content):
    try:
        # Create a blob client using the provided file name as the name for the blob
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=file_name)

        print(f"Uploading to Azure Storage as blob:\n\t{file_name}")

        # Upload the created file
        blob_client.upload_blob(file_content, overwrite=True)

        print("Upload completed successfully.")
    except Exception as ex:
        print(f"Exception: {ex}")
        raise HTTPException(status_code=500, detail="Failed to upload file to Azure Storage.")

def extract_links_bayut(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'
    }
    try:
        r = requests.get(url, headers=headers)
        r.raise_for_status()  # Raise an error for bad status codes
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return [], None

    soup = BeautifulSoup(r.text, 'html.parser')

    # Find all <h3> tags with the specified class and extract links
    anchor_tags = soup.find_all('h3', class_='entry-title title post_title')
    links = [anchor_tag.find('a').get('href') for anchor_tag in anchor_tags]

    # Find the "next page" link
    next_page = soup.find('a', class_='next page-numbers')
    next_page_url = next_page.get('href') if next_page else None

    # Handle the specific case for page 468
    if url == "https://www.bayut.com/mybayut/page/468/":
        next_page_url = "https://www.bayut.com/mybayut/page/469/"
    elif url == "https://www.bayut.com/mybayut/page/472/":
        next_page_url = "https://www.bayut.com/mybayut/page/473/"

    return links, next_page_url

def extract_links_propertyfinder(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'
    }
    try:
        r = requests.get(url, headers=headers)
        r.raise_for_status()  # Raise an error for bad status codes
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return [], None

    soup = BeautifulSoup(r.text, 'html.parser')

    # Find all <div> tags with the class 'col post-item' and extract links
    post_items = soup.find_all('div', class_='col post-item')
    links = [post_item.find('a').get('href') for post_item in post_items]

    # Find the "next page" link
    next_page = soup.find('a', class_='next page-number')
    next_page_url = next_page.get('href') if next_page else None

    return links, next_page_url

# Main function to scrape links from all pages
def scrape_all_pages(starting_url, base_url):
    if not starting_url:
        print("URL not found")
        return None

    all_links = set()  # Use a set to keep track of all unique links
    url = starting_url

    # Determine which extraction function to use based on the URL
    if "bayut.com" in starting_url:
        extract_links = extract_links_bayut
    elif "propertyfinder.ae" in starting_url:
        extract_links = extract_links_propertyfinder
    else:
        print("Unsupported URL")
        return None

    # Extract initial page number from the URL for progress tracking
    try:
        page_count = int(starting_url.split('/')[-2])
    except ValueError:
        page_count = 1

    # Generate a unique file name with timestamp
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    file_name = f"link-{timestamp}.txt"
    file_content = ""

    while url:
        print(f"Processing page {page_count} ({url})...")
        links, next_page_url = extract_links(url)
        new_links = set(links) - all_links  # Find new links that are not already in all_links

        progress.current_page = page_count
        progress.links_extracted = len(new_links)
        progress.total_links = len(all_links) + len(new_links)

        # Append each unique link to the content that will be uploaded
        for link in new_links:
            file_content += link + '\n'

        all_links.update(new_links)  # Add new links to the set

        print(f"Done with {url}. Links extracted: {progress.links_extracted}. Total links: {progress.total_links}")
        if next_page_url is None:  # Check if there is no next page URL
            break  # Break out of the loop if no next page URL is found
        url = next_page_url  # Update the URL to the next page
        page_count += 1

    # Upload the file content to the Azure container
    upload_file_to_container("savelinks", file_name, file_content)

    # Send a webhook notification to the Node.js server
    webhook_url = "http://localhost:4000/api/webhook/getextractLink"
    payload = {
        "message": "Successfully saved links.",
        "respon": {
            "fileName": file_name,
            "site_link": base_url
        }
    }
    try:
        response = requests.post(webhook_url, json=payload)
        response.raise_for_status()
        print("Webhook notification sent successfully.")
    except requests.RequestException as e:
        print(f"Error sending webhook notification: {e}")

@app.get("/{encoded_url:path}")
async def start_scraping(encoded_url: str, background_tasks: BackgroundTasks):
    print(encoded_url, "this is base url +++++++++++++==")
    UpdURL = "https://"+encoded_url
    base_url = unquote(UpdURL)
    if not base_url:
        raise HTTPException(status_code=404, detail="URL not found")

    print(base_url, "this is base url encoded +++++++++++++==")
    
    # Start the scraping process in the background
    background_tasks.add_task(scrape_all_pages, base_url, base_url)

    return {"status": "Task started", "message": "Scraping process has started."}

@app.get("/progress")
async def get_progress():
    return progress
