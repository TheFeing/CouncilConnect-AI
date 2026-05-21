import pytest
# MagicMock (unittest.mock) can create sub-objects on the fly (yes to everything), without needing the actual library
# patch (unittest.mock) replaces the Client class in the guardrails module with MagicMock
import unittest.mock
import scraper.ingest

# The @patch decorator acts as a wrapper in the ingest module to replace both the CouncilCrawler1 class and the redact_pii function, preventing real web scraping and controlling function output.
@unittest.mock.patch('scraper.crawler.CouncilCrawler')
@unittest.mock.patch('scraper.redactor.redact_pii')
def test_run_ingestion_pipeline_success(mock_redactor, mock_crawler_class):
    """
    Rationale: Verifies text extraction and redaction coordination pipelines handle scraped parameters cleanly.
    """
    
    mock_crawler = unittest.mock.MagicMock()
    mock_crawler_class.return_value = mock_crawler
    
    # Return the dictionary format expected by the ingestion orchestration workflow
    mock_crawler.scrape_content.return_value = {
        "type": "html",
        "url": "https://example.com/test",
        "text": "Original content with email@test.com"
    }

    mock_redactor.return_value = "Original content with [EMAIL_REDACTED]"

    # Tests pipeline execution with a sample URL
    scraper.ingest.run_ingestion_pipeline("https://example.com/test")

    # Ensures the mock is called once with specific string
    mock_crawler.scrape_content.assert_called_once_with("https://example.com/test")
    mock_redactor.assert_called_once_with("Original content with email@test.com")