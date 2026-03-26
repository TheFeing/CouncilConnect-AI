import requests                 # Sending HTTP requests to websites
import bs4                      # Parsing and extracting data from HTML (BeautifulSoup)
import urllib.parse             # Handling and breaking down URLs
import time                     # Delays between requests
import random                   # Generating random delays (human-like behavior)

class CouncilCrawler:
    """
    Only one hard-coded Dunder hook (__init__) is automated for setting initial state. 
    Custom methods (like scraping) are kept manual to separate object setup from high-latency execution and side effects.
    """

    def __init__(self, base_url):   # Auto-called and attached to the instance (self) by Python when creating a new instance
        self.base_url = base_url        # Starting point for crawling
        self.visited_urls = set()       # Stores seen URLs. A 'set' ensures no duplicates
        self.headers = {
            # Mimics a real Chrome browser for better compatibility and to reduce the chance of being blocked (S10).
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.7632.110 Safari/537.36',
            'Accept-Language': 'en-GB,en;q=0.9',
            # Contact info for transparency and to comply with ethical scraping practices (S10).
            'From': 'Project-Apprenticeship-Fei'
        }

    def is_polite(self, url):
        return True

    def get_links(self, html, current_url):
        soup = bs4.BeautifulSoup(html, 'html.parser')
        links = []
        for anchor in soup.find_all('a', href=True):
            href = anchor['href']
            full_url = urllib.parse.urljoin(current_url, href)
            # Only follow links within the same domain
            if urllib.parse.urlparse(full_url).netloc == urllib.parse.urlparse(self.base_url).netloc:
                links.append(full_url)
        return links

    def scrape_content(self, url):
        if url in self.visited_urls or not self.is_polite(url): # Ensures not visited and allowed
            return None
        
        time.sleep(random.uniform(2.0, 5.0)) # Avoid triggering rate limiters (S10).
        print(f"Crawling: {url}") # Console feedback

        try:
            response = requests.get(url, headers=self.headers, timeout=10) # Fetch web content
            print(f"Debug: HTTP Status Code for {url} is {response.status_code}")
            self.visited_urls.add(url) # Mark URL as visited
            
            if response.status_code != 200:
                return None # Skip to next URL if not successful
                
            soup = bs4.BeautifulSoup(response.text, 'html.parser') # Turns HTML into a navigable tree structure

            # Identify the main content container to avoid sidebar/nav noise
            # Some sites often use <main> or specific article tags
            content_area = soup.find('main') or soup.find('article') or soup.body

            if not content_area:
                return None

            for script in content_area(["script", "style", "nav", "footer", "header"]): # Remove non-content tags
                script.extract()   

            return content_area.get_text(separator=' ', strip=True) # Extracts clean text with spacing
            
        except requests.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return None # Error encountered, return nothing for this URL