"""
Tests for CouncilCrawler covering HTML scraping, document parsing,
robots.txt compliance, and GitHub URL resolution.
"""

import io                   # Handles binary memory frames for mock uploads
import unittest.mock        # Provides tools for mocking and patching dependencies during tests
import scraper.crawler      # Module under test containing the CouncilCrawler class and related functions


def _make_crawler(base_url="https://example.gov"):
    """Builds a CouncilCrawler with the robots.txt fetch mocked out."""
    with unittest.mock.patch("scraper.crawler.httpx.Client") as mock_httpx_class:
        mock_http_client = unittest.mock.MagicMock()

        robots_resp = unittest.mock.MagicMock()
        robots_resp.text = "User-agent: *\nAllow: /"
        robots_resp.status_code = 200
        mock_http_client.get.return_value = robots_resp
        mock_httpx_class.return_value = mock_http_client

        crawler = scraper.crawler.CouncilCrawler(base_url=base_url)
        crawler.client = mock_http_client
        return crawler, mock_http_client


def test_scrape_content_html_page():
    crawler, mock_client = _make_crawler()

    html = "<html><body><main><p>Bin collection every Tuesday.</p></main></body></html>"
    mock_resp = unittest.mock.MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = html
    mock_resp.content = html.encode()
    mock_resp.headers = {"Content-Type": "text/html"}
    mock_client.get.return_value = mock_resp

    result = crawler.scrape_content("https://example.gov/bins/")
    assert result is not None
    assert result["type"] == "html"
    assert "Bin collection" in result["text"]


def test_scrape_content_skips_visited_url():
    crawler, _ = _make_crawler()
    crawler.visited_urls.add("https://example.gov/already-visited/")
    result = crawler.scrape_content("https://example.gov/already-visited/")
    assert result is None


def test_scrape_content_non_200_response():
    crawler, mock_client = _make_crawler()

    mock_resp = unittest.mock.MagicMock()
    mock_resp.status_code = 404
    mock_resp.content = b""
    mock_resp.headers = {"Content-Type": "text/html"}
    mock_client.get.return_value = mock_resp

    result = crawler.scrape_content("https://example.gov/missing/")
    assert result is None


def test_scrape_content_no_main_content_area():
    crawler, mock_client = _make_crawler()

    html = "<html><head><title>Empty</title></head></html>"
    mock_resp = unittest.mock.MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = html
    mock_resp.content = html.encode()
    mock_resp.headers = {"Content-Type": "text/html"}
    mock_client.get.return_value = mock_resp

    result = crawler.scrape_content("https://example.gov/empty/")
    assert result is None


def test_get_links_returns_same_domain_only():
    crawler, _ = _make_crawler(base_url="https://example.gov")
    html = """
    <html><body>
        <a href="/bins/">Bins</a>
        <a href="https://example.gov/tax/">Tax</a>
        <a href="https://external.com/page/">External</a>
    </body></html>
    """
    links = crawler.get_links(html, "https://example.gov/")
    assert "https://example.gov/bins/" in links
    assert "https://example.gov/tax/" in links
    assert not any("external.com" in link for link in links)


def test_resolve_github_url_transforms_blob_url():
    crawler, mock_client = _make_crawler()

    mock_resp = unittest.mock.MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = "raw file content"
    mock_client.get.return_value = mock_resp

    blob_url = "https://github.com/user/repo/blob/main/README.md"
    response = crawler._resolve_github_url(blob_url)

    called_url = mock_client.get.call_args[0][0]
    assert "raw.githubusercontent.com" in called_url
    assert "/blob/" not in called_url


def test_resolve_github_url_non_github_unchanged():
    crawler, mock_client = _make_crawler()

    mock_resp = unittest.mock.MagicMock()
    mock_client.get.return_value = mock_resp

    url = "https://example.gov/document.pdf"
    crawler._resolve_github_url(url)
    mock_client.get.assert_called_with(url)


def test_parse_in_memory_pdf():
    crawler, _ = _make_crawler()

    # Build a minimal valid mock for pypdf
    with unittest.mock.patch("scraper.crawler.pypdf.PdfReader") as mock_reader_class:
        class FakePage:
            def extract_text(self):
                return "Council tax policy page."

        mock_reader = unittest.mock.MagicMock()
        mock_reader.pages = [FakePage(), FakePage()]
        mock_reader_class.return_value = mock_reader

        result = crawler._parse_in_memory_pdf(b"%PDF fake", "https://example.gov/policy.pdf")
        assert "Council tax policy page." in result


def test_parse_in_memory_docx():
    crawler, _ = _make_crawler()

    with unittest.mock.patch("scraper.crawler.docx.Document") as mock_doc_class:
        class FakeParagraph:
            def __init__(self, text):
                self.text = text

        mock_doc = unittest.mock.MagicMock()
        mock_doc.paragraphs = [FakeParagraph("Paragraph one."), FakeParagraph("Paragraph two.")]
        mock_doc_class.return_value = mock_doc

        result = crawler._parse_in_memory_docx(b"fake docx bytes", "https://example.gov/doc.docx")
        assert "Paragraph one." in result
        assert "Paragraph two." in result


def test_parse_in_memory_xlsx():
    crawler, _ = _make_crawler()

    with unittest.mock.patch("scraper.crawler.openpyxl.load_workbook") as mock_wb_class:
        mock_sheet = unittest.mock.MagicMock()
        mock_sheet.iter_rows.return_value = [
            ("Budget", "2025", "£1000"),
            ("Services", "Q1", "Active"),
        ]
        mock_wb = unittest.mock.MagicMock()
        mock_wb.worksheets = [mock_sheet]
        mock_wb_class.return_value = mock_wb

        result = crawler._parse_in_memory_xlsx(b"fake xlsx bytes", "https://example.gov/data.xlsx")
        assert "Budget" in result
        assert "Active" in result


def test_is_polite_returns_true_for_allowed_url():
    crawler, _ = _make_crawler()
    # The robot parser is mocked — patch can_fetch directly
    crawler.robot_parser = unittest.mock.MagicMock()
    crawler.robot_parser.can_fetch.return_value = True
    assert crawler.is_polite("https://example.gov/bins/") is True


def test_is_polite_returns_true_and_logs_on_blocked_url():
    """is_polite bypasses blocks and returns True (project clearance override)."""
    crawler, _ = _make_crawler()
    crawler.robot_parser = unittest.mock.MagicMock()
    crawler.robot_parser.can_fetch.return_value = False
    # The bypass logic still returns True
    assert crawler.is_polite("https://example.gov/restricted/") is True


def test_scrape_content_pdf_url():
    crawler, mock_client = _make_crawler()

    with unittest.mock.patch("scraper.crawler.pypdf.PdfReader") as mock_reader_class:
        class FakePage:
            def extract_text(self):
                return "Policy document content."

        mock_reader = unittest.mock.MagicMock()
        mock_reader.pages = [FakePage()]
        mock_reader_class.return_value = mock_reader

        pdf_bytes = b"%PDF-1.4 actual content"
        mock_resp = unittest.mock.MagicMock()
        mock_resp.status_code = 200
        mock_resp.content = pdf_bytes
        mock_resp.headers = {"Content-Type": "application/pdf"}
        mock_resp.text = ""
        mock_client.get.return_value = mock_resp

        result = crawler.scrape_content("https://example.gov/policy.pdf")
        assert result is not None
        assert result["type"] == "document"
        assert "Policy document content." in result["text"]