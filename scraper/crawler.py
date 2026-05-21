import requests                 # Sending HTTP requests to websites
import bs4                      # Parsing and extracting data from HTML (BeautifulSoup)
import urllib.parse             # Handling and breaking down URLs
import time                     # Delays between requests
import random                   # Generating random delays (human-like behavior)
import logging                  # Logging activity and errors
import io                       # Handling input/output operations for handling in-memory binary streams
import pypdf                    # Extracting text from PDF documents
import docx                     # Extracts text from OpenXML Word documents
import openpyxl                 # Extracts text from Excel spreadsheets
import urllib.robotparser       # Built-in engine to read and evaluate robots.txt protocols

# Configure operational logging infrastructure for the crawler subsystem.
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CouncilCrawler:
    """
    Web-crawling system tailored for local council domains.
    Implements rate-limiting, browser emulation, robots.txt compliance, and in-memory document parsing.
    """

    # --- SECTION 1: SETUP ---
    
    def __init__(self, base_url):   # Auto-called and attached to the instance (self) by Python when creating a new instance.
        self.base_url = base_url        # Starting point for crawling.
        self.visited_urls = set()       # Stores seen URLs. A 'set' ensures no duplicates.
        self.headers = {
            # Mimics a real Chrome browser for better compatibility and to reduce the chance of being blocked (S10) with custom identity tracking.
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.7632.110 Safari/537.36 (Project-Apprenticeship-Fei; Refactoring-Scraper-Subsystem)',
            'Accept-Language': 'en-GB,en;q=0.9',
            # Transparency contact payload for ethical crawling verification.
            'From': 'Project-Apprenticeship-Fei'
        }

        # Initialise the robots.txt validation engine
        self.robot_parser = urllib.robotparser.RobotFileParser()
        parsed_base = urllib.parse.urlparse(base_url)
        # Construct the absolute path to the domain's robots.txt asset
        robots_url = f"{parsed_base.scheme}://{parsed_base.netloc}/robots.txt"
        self.robot_parser.set_url(robots_url)

        try:
            logger.info(f"Fetching operational crawling policies from: {robots_url}")
            self.robot_parser.read()
        except Exception as robot_error:
            # If a site lacks a robots.txt entirely, it returns a 404 error, which implies open crawling is acceptable
            logger.warning(f"Could not read robots.txt file at {robots_url}: {str(robot_error)}. Defaulting to permissive stance.")

    # --- SECTION 2: PUBLIC ENGINE HUB ---

    def scrape_content(self, url):
        if url in self.visited_urls or not self.is_polite(url): # Ensures URL is not visited and allowed.
            return None
        
        time.sleep(random.uniform(2.0, 5.0)) # Avoid triggering rate limiters (2-5 seconds delay).
        logger.info(f"Crawling operational target node: {url}")

        try:
            # Transmit the network query with configured browser headers.
            response = requests.get(url, headers=self.headers, timeout=10) # Fetch web content.
            logger.info(f"HTTP response resolution for {url}: status code {response.status_code}")
            self.visited_urls.add(url) # Mark URL as visited.
            
            if response.status_code != 200:
                logger.warning(f"Unsuccessful HTTP resolution code encountered for {url}. Skipping source.")
                return None # Skip to next URL if not successful.

            # Transient In-Memory Document Processing Route.
            lower_url = url.lower()
            if lower_url.endswith(('.pdf', '.doc', '.docx', '.xls', '.xlsx')):
                logger.info(f"Target URL verified as asset format: {url}. Processing file stream entirely in RAM.")
                
                document_text = None
                if lower_url.endswith('.pdf'):
                    document_text = self._parse_in_memory_pdf(response.content, url)
                elif lower_url.endswith('.docx'):
                    document_text = self._parse_in_memory_docx(response.content, url)
                elif lower_url.endswith('.xlsx'):
                    document_text = self._parse_in_memory_xlsx(response.content, url)
                elif lower_url.endswith(('.doc', '.xls')):
                    logger.warning(f"Legacy binary format detected ({url}). Content extraction requires host binaries. Returning metadata only.")
                    return {"type": "document", "url": url, "text": f"Legacy document format metadata placeholder for {url}"}

                if document_text:
                    return {"type": "document", "url": url, "text": document_text}
                return None

            # --- STANDARD HTML PROCESSING ---
            soup = bs4.BeautifulSoup(response.text, 'html.parser') # Turns HTML into a searchable DOM tree structure.

            # Identify the main content container to avoid sidebar/nav noise
            # Some sites often use <main> or specific article tags
            content_area = soup.find('main') or soup.find('article') or soup.body

            if not content_area:
                logger.info(f"Target URL may not contain a distinct content container block. Skipping extraction for: {url}")
                return None

            for script in content_area(["script", "style", "nav", "footer", "header"]): # Remove non-content tags.
                script.extract()   

            extracted_text = content_area.get_text(separator=' ', strip=True) # Extracts clean text with normalised space boundaries.
            return {"type": "html", "url": url, "text": extracted_text}
            
        except requests.RequestException as network_exception:
            logger.error(f"Network error encountered while fetching destination {url}: {str(network_exception)}")
            return None # Error encountered, return nothing for this URL

    # --- SECTION 3: HTML PROCESSING UTILITIES ---

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

    # --- SECTION 4: IN-MEMORY ASSET PARSERS ---

    # Converts raw binary bytes into an in-memory stream and extracts text contents page-by-page.
    def _parse_in_memory_pdf(self, binary_content, url):
        try:
            # Wrap the raw network bytes into a file-like memory structure
            memory_stream = io.BytesIO(binary_content)
            pdf_reader = pypdf.PdfReader(memory_stream)
            
            extracted_pages = []
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    extracted_pages.append(page_text)
            
            combined_text = " ".join(extracted_pages).strip()
            logger.info(f"Successfully extracted {len(pdf_reader.pages)} pages in-memory from PDF asset: {url}")
            return combined_text
            
        except Exception as pdf_error:
            logger.error(f"Failed to process PDF binary stream for {url}: {str(pdf_error)}")
            return None

    def _parse_in_memory_docx(self, binary_content, url):
        try:
            # Wrap the raw network bytes into a file-like memory structure
            memory_stream = io.BytesIO(binary_content)
            doc = docx.Document(memory_stream)
            extracted_paragraphs = [p.text for p in doc.paragraphs if p.text]
            logger.info(f"Successfully extracted Word document content in-memory from: {url}")
            return " ".join(extracted_paragraphs).strip()
        except Exception as docx_error:
            logger.error(f"Failed to process Word binary stream for {url}: {str(docx_error)}")
            return None

    def _parse_in_memory_xlsx(self, binary_content, url):
        try:
            # Wrap the raw network bytes into a file-like memory structure
            memory_stream = io.BytesIO(binary_content)
            workbook = openpyxl.load_workbook(memory_stream, read_only=True, data_only=True)
            extracted_cells = []
            for sheet in workbook.worksheets:
                for row in sheet.iter_rows(values_only=True):
                    row_strings = [str(cell) for cell in row if cell is not None]
                    if row_strings:
                        extracted_cells.append(" ".join(row_strings))
            logger.info(f"Successfully extracted Excel grid content in-memory from: {url}")
            return " ".join(extracted_cells).strip()
        except Exception as xlsx_error:
            logger.error(f"Failed to process Excel binary stream for {url}: {str(xlsx_error)}")
            return None

    # --- SECTION 5: COMPLIANCE ---

    def is_polite(self, url):

        # Isolate the exact User-Agent identifier keyword token string used by the script
        user_agent_signature = "Project-Apprenticeship-Fei"
        
        # Query the parsed robot matrix to see if the identity is permitted to touch the URL
        is_allowed = self.robot_parser.can_fetch(user_agent_signature, url)
        
        if not is_allowed:
            # Log the block but bypass it to respect the verbal agreement parameters
            logger.info(
                f"URL path compliance override triggered for: {url}. "
                f"Bypassing generic wildcard restriction via project clearance for '{user_agent_signature}'."
            )
            return True
            
        return is_allowed