import pytest
# MagicMock can create sub-objects on the fly (yes to everything), without needing the actual library
# patch replaces the Client class in the guardrails module with MagicMock
from unittest.mock import patch, MagicMock
from app.ingest import run_ingestion_pipeline1

@patch('app.ingest.CouncilCrawler1') # Decorator (type of wrapper) @patch replaces CouncilCrawler1 class (imported) in ingest module, prevents real web scraping
@patch('app.ingest.redact_pii1')    # Decorator @patch replaces redact_pii1 function in ingest module, controls its output
def test_run_ingestion_pipeline_success1(mock_redactor, mock_crawler_class):    # Tests when content is successfully retrieved.

    mock_crawler = MagicMock()
    mock_crawler_class.return_value = mock_crawler
    mock_crawler.scrape_content1.return_value = "Original content with email@test.com"
    
    mock_redactor.return_value = "Original content with [EMAIL_REDACTED]"
    
    # Tests pipeline execution with a sample URL
    run_ingestion_pipeline1("https://example.com/test")
    
    # Ensures the mock is called once with specific string
    mock_crawler.scrape_content1.assert_called_once_with("https://example.com/test")
    mock_redactor.assert_called_once_with("Original content with email@test.com")

@patch('app.ingest.CouncilCrawler1')
def test_run_ingestion_pipeline_no_content1(mock_crawler_class): # Tests when the crawler returns None.

    mock_crawler = MagicMock()
    mock_crawler_class.return_value = mock_crawler
    mock_crawler.scrape_content1.return_value = None
    
    # Ensure it doesn't crash when no content is found
    run_ingestion_pipeline1("https://example.com/empty")
    
    mock_crawler.scrape_content1.assert_called_once()