import requests
from bs4 import BeautifulSoup
import os
from fastapi import FastAPI, HTTPException
from urllib.parse import urljoin, urlparse

app = FastAPI()

def download_file(url, save_path):
    response = requests.get(url)
    response.raise_for_status()  # Raise an exception for HTTP errors
    with open(save_path, 'wb') as file:
        file.write(response.content)

def scrape_website(url, save_dir='scraped_files', visited=None):
    if visited is None:
        visited = set()

    # Normalize the URL and add to visited set
    url = url.rstrip('/')
    if url in visited:
        return
    visited.add(url)

    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors
        soup = BeautifulSoup(response.text, 'html.parser')

        # Create directory to save files
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        # Save HTML file
        html_filename = os.path.basename(urlparse(url).path) or 'index.html'
        html_path = os.path.join(save_dir, html_filename)
        with open(html_path, 'w', encoding='utf-8') as file:
            file.write(soup.prettify())

        # Scrape and save CSS files
        for css in soup.find_all('link', rel='stylesheet'):
            css_url = urljoin(url, css['href'])
            css_path = os.path.join(save_dir, os.path.basename(css_url))
            download_file(css_url, css_path)
            css['href'] = os.path.basename(css_url)

        # Scrape and save JS files
        for script in soup.find_all('script', src=True):
            js_url = urljoin(url, script['src'])
            js_path = os.path.join(save_dir, os.path.basename(js_url))
            download_file(js_url, js_path)
            script['src'] = os.path.basename(js_url)

        # Scrape and save images
        for img in soup.find_all('img'):
            img_url = urljoin(url, img['src'])
            img_path = os.path.join(save_dir, os.path.basename(img_url))
            download_file(img_url, img_path)
            img['src'] = os.path.basename(img_url)

        # Recursively scrape linked pages
        for link in soup.find_all('a', href=True):
            link_url = urljoin(url, link['href'])
            if urlparse(link_url).netloc == urlparse(url).netloc and link_url not in visited:  # Same domain
                scrape_website(link_url, save_dir, visited)

        print(f"Website scraped and saved to {save_dir}")
    except Exception as e:
        print(f"Failed to scrape {url}: {e}")

@app.get("/{encoded_url:path}")
async def read_root(encoded_url: str):
    try:
        scrape_website(encoded_url)
        return {"message": "Successfully saved website content."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Example usage
# scrape_website('https://vativeapps.com/')
