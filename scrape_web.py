from bs4 import BeautifulSoup
import requests
import re

def get_content(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    response = requests.get(url, headers=headers)
    return response.text

def extract_text_only(html_content) -> str:
    # Use BeautifulSoup to parse the HTML content
    from bs4 import BeautifulSoup

    # Parse the HTML content
    soup = BeautifulSoup(html_content, 'html.parser')

    # Extract the text content from the parsed HTML
    return soup.get_text(separator='\n', strip=True)

def scrape_web(url: str) -> str:
    html_content = get_content(url)
    clean_content = extract_text_only(html_content)
    return clean_content
