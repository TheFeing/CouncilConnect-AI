import requests                                 # Sending HTTP requests to websites
from bs4 import BeautifulSoup                   # Parsing and extracting data from HTML
from urllib.parse import urljoin, urlparse      # Handling and breaking down URLs
import time                                     # Delays between requests
import random                                   # Generating random delays (human-like behavior)

class CouncilCrawler1:
    """
    Only one hard-coded Dunder hook (__init__) is automated for setting initial state.
     Custom methods (like scraping) are kept manual to separate object setup from high-latency execution and side effects.
    """

    def __init__(self, base_url1):      # Auto-called and attached to the instance (self) by Python when creating a new instance
        self.base_url1 = base_url1      # Starting point for crawling
        self.visited_urls1 = set()      # Stores seen URLs. A 'set' ensures no duplicates
        self.headers1 = {
            # Mimics a real Chrome browser for better compatibility and to reduce the chance of being blocked (S10).
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.7632.110 Safari/537.36',
            'Accept-Language': 'en-GB,en;q=0.9',
            # Contact info for transparency and to comply with ethical scraping practices (S10).
            'From': 'Project-Apprenticeship-Fei'
        }

    def is_polite1(self, url1):
        """
        Placeholder for robots.txt parsing logic (Sprint 4).
        Currently defaults to True for specific development targets.
        """
        return True

    def get_links1(self, html1, current_url1):
        """
        Extracts all internal links from the page to support multi-page crawling.
        """
        soup1 = BeautifulSoup(html1, 'html.parser')
        links1 = []
        for anchor1 in soup1.find_all('a', href=True):
            href1 = anchor1['href']
            full_url1 = urljoin(current_url1, href1)
            # Only follow links within the same domain
            if urlparse(full_url1).netloc == urlparse(self.base_url1).netloc:
                links1.append(full_url1)
        return links1

    def scrape_content1(self, url1):
        if url1 in self.visited_urls1 or not self.is_polite1(url1): # Ensures not visited and allowed
            return None
       
        # Avoid triggering rate limiters (S10).
        time.sleep(random.uniform(2.0, 5.0))   
        print(f"Crawling: {url1}")      # Console feedback

        try:
            response1 = requests.get(url1, headers=self.headers1, timeout=10)   # Fetch web content
            print(f"Debug: HTTP Status Code for {url1} is {response1.status_code}")
            self.visited_urls1.add(url1)    # Mark URL as visited
           
            if response1.status_code != 200:
                return None     # Skip to next URL if not successful
               
            soup1 = BeautifulSoup(response1.text, 'html.parser')    # Turns HTML into a navigable tree structure

            # Identify the main content container to avoid sidebar/nav noise
            # Some sites often use <main> or specific article tags
            content_area1 = soup1.find('main') or soup1.find('article') or soup1.body

            if not content_area1:
                return None

            # Remove non-content tags
            for script1 in content_area1(["script", "style", "nav", "footer", "header"]):
                 script1.extract()  

            return content_area1.get_text(separator=' ', strip=True) # Extracts clean text with spacing
           
        except requests.RequestException as e1:
            print(f"Error fetching {url1}: {e1}")
            return None     # Error encountered, return nothing for this URL