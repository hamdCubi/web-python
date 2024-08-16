import requests
from bs4 import BeautifulSoup
from urllib.parse import unquote
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
import os

app = FastAPI()


class Progress(BaseModel):
    current_page: int
    links_extracted: int
    total_links: int


progress = Progress(current_page=0, links_extracted=0, total_links=0)


def extract_links_bayut(url):
    headers = {
        'User-Agent':
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'
    }
    try:

        print(url, "this is the url")
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

    return links, next_page_url


def extract_links_propertyfinder(url):
    headers = {
        'User-Agent':
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'
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
def scrape_all_pages(starting_url):
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
    folder_name = "LinkFiles"
    os.makedirs(folder_name, exist_ok=True)
    file_name = f"{folder_name}/link-{timestamp}.txt"

    while url:
        print(f"Processing page {page_count} ({url})...")
        links, next_page_url = extract_links(url)
        new_links = set(
            links
        ) - all_links  # Find new links that are not already in all_links

        progress.current_page = page_count
        progress.links_extracted = len(new_links)
        progress.total_links = len(all_links) + len(new_links)

        # Ensure the directory exists before writing the file
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)

        # Open the file in append mode and write each unique link immediately
        with open(file_name, 'a', encoding='utf-8') as file:
            for link in new_links:
                file.write(link + '\n')

        all_links.update(new_links)  # Add new links to the set

        print(
            f"Done with {url}. Links extracted: {progress.links_extracted}. Total links: {progress.total_links}"
        )
        if next_page_url is None:  # Check if there is no next page URL
            break  # Break out of the loop if no next page URL is found
        url = next_page_url  # Update the URL to the next page
        page_count += 1

    return file_name


@app.get("/{encoded_url:path}")
async def read_root(encoded_url: str):
    print(encoded_url, "this is base url +++++++++++++==")
    UpdURL = "https://"+encoded_url
    base_url = unquote(UpdURL)
    if not base_url:
        raise HTTPException(status_code=404, detail="URL not found")

    print(base_url, "this is base url encoded +++++++++++++==")
    # Call the main function to scrape and store links
    file_path = scrape_all_pages(base_url)
    if file_path is None:
        raise HTTPException(status_code=500, detail="Error in scraping links.")

    file_name = os.path.basename(file_path)

    return {
        "message": "Successfully saved links.",
        "respon": {
            "fileName": file_name,
            "site_link": base_url
        }
    }


@app.get("/progress")
async def get_progress():
    return progress
