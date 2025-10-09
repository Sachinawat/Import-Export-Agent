import requests
import numpy as np
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse, urljoin

from config import settings, logger

def perform_google_search(query: str) -> List[Dict[str, Any]]:
    """
    Performs a Google Custom Search and returns the results.
    """
    search_url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": settings.GOOGLE_CSE_API_KEY,
        "cx": settings.GOOGLE_CSE_CX,
        "q": query,
        "num": 5  # Number of results to fetch
    }
    logger.info(f"Performing Google search for: {query}")
    try:
        response = requests.get(search_url, params=params, timeout=10)
        response.raise_for_status() # Raise an exception for bad status codes
        search_results = response.json()
        if 'items' in search_results:
            logger.info(f"Found {len(search_results['items'])} search results.")
            return search_results['items']
        else:
            logger.warning("No 'items' found in Google Search results.")
            return []
    except requests.exceptions.RequestException as e:
        logger.error(f"Google Search API request failed: {e}")
        return []

def simple_web_scraper(url: str, selector: str = 'body') -> Optional[str]:
    """
    A very basic web scraper that fetches content from a URL based on a CSS selector.
    This is highly simplified and will likely need significant refinement for real-world use.
    """
    logger.info(f"Attempting to scrape URL: {url} with selector: {selector}")
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        element = soup.select_one(selector)
        if element:
            logger.info(f"Successfully scraped content from {url}.")
            return element.get_text(separator=' ', strip=True)
        else:
            logger.warning(f"No element found for selector '{selector}' on {url}.")
            return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Web scraping failed for {url}: {e}")
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred during scraping {url}: {e}")
        return None

def normalize_country_name(country_name: str) -> str:
    """
    Placeholder for country name normalization (e.g., USA -> United States).
    Could use a more comprehensive library if needed.
    """
    country_map = {
        "usa": "United States",
        "india": "India",
        "germany": "Germany",
        "uk": "United Kingdom",
        "united kingdom": "United Kingdom",
        "china": "China",
        "japan": "Japan",
        "eu": "European Union" # Or map to individual members if preferred
    }
    return country_map.get(country_name.lower(), country_name)
