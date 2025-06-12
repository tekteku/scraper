"""
Integration module to use either AgentQL or hash-based navigation for Remax.com.tn

This module provides a unified interface to handle Remax.com.tn pagination
using either the AgentQL approach or the hash-based URL approach, based on
which dependencies are available and user configuration.
"""

import logging
import time
import re
import importlib.util

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("RemaxIntegration")

def check_agentql_available():
    """Check if AgentQL is available in the environment"""
    try:
        import agentql
        return True
    except ImportError:
        return False

def check_module_exists(module_name):
    """Check if a module exists without importing it"""
    return importlib.util.find_spec(module_name) is not None

def get_remax_pagination_handler(use_agentql=True):
    """
    Get the appropriate pagination handler for Remax.com.tn
    
    Args:
        use_agentql (bool): Whether to prefer AgentQL if available
        
    Returns:
        dict: A dictionary with pagination handling functions
    """
    agentql_available = check_agentql_available()
    hash_module_exists = check_module_exists("remax_hash_pagination")
    agentql_module_exists = check_module_exists("remax_agentql_pagination")
    
    logger.info(f"AgentQL available: {agentql_available}")
    logger.info(f"Hash pagination module exists: {hash_module_exists}")
    logger.info(f"AgentQL pagination module exists: {agentql_module_exists}")
    
    handler = {
        "type": None,
        "navigate_to_page": None,
        "extract_properties": None,
        "has_next_page": None
    }
    
    # Try to use AgentQL if preferred and available
    if use_agentql and agentql_available and agentql_module_exists:
        try:
            from remax_agentql_pagination import scrape_remax_with_agentql
            logger.info("Using AgentQL for Remax pagination")
            
            handler["type"] = "agentql"
            handler["scrape_with_agentql"] = scrape_remax_with_agentql
            
            # Return the AgentQL handler which provides all functionality in one method
            return handler
        except ImportError as e:
            logger.warning(f"Failed to import AgentQL pagination module: {e}")
    
    # Fall back to hash-based URL pagination
    if hash_module_exists:
        try:
            from remax_hash_pagination import handle_remax_hash_pagination
            logger.info("Using hash-based URLs for Remax pagination")
            
            handler["type"] = "hash"
            handler["get_page_url"] = handle_remax_hash_pagination
            
            # The hash pagination handler is simpler - it just provides URL generation
            return handler
        except ImportError as e:
            logger.warning(f"Failed to import hash-based pagination module: {e}")
    
    # If neither is available, create a basic hash URL handler
    logger.warning("No pagination modules available. Using basic hash URL handler.")
    handler["type"] = "basic"
    
    def basic_hash_handler(current_url, page_number):
        """
        Basic hash URL handler for Remax pagination
        
        Args:
            current_url (str): The current URL
            page_number (int): The page number to navigate to
            
        Returns:
            str: The URL for the specified page
        """
        if "#" in current_url:
            base_url, hash_part = current_url.split('#', 1)
            if "page=" in hash_part:
                new_hash = re.sub(r'page=\d+', f'page={page_number}', hash_part)
            else:
                new_hash = f"{hash_part}&page={page_number}"
            return f"{base_url}#{new_hash}"
        else:
            return f"{current_url}#mode=gallery&tt=261&cur=TND&sb=MostRecent&page={page_number}&sc=1048"
    
    handler["get_page_url"] = basic_hash_handler
    return handler

def scrape_remax_site(browser_page, url, max_pages=20, use_agentql=True):
    """
    Unified function to scrape Remax.com.tn using either AgentQL or hash-based pagination
    
    Args:
        browser_page: The browser page object (Playwright page or None for AgentQL)
        url (str): The URL to scrape
        max_pages (int): Maximum number of pages to scrape
        use_agentql (bool): Whether to prefer AgentQL if available
        
    Returns:
        list: The scraped property listings
    """
    # Get the appropriate pagination handler
    handler = get_remax_pagination_handler(use_agentql)
    all_properties = []
    
    # If using AgentQL, we can delegate the entire scraping process
    if handler["type"] == "agentql" and handler.get("scrape_with_agentql"):
        logger.info("Delegating Remax scraping to AgentQL implementation")
        
        def collect_properties(properties, page_number):
            logger.info(f"Collected {len(properties)} properties from page {page_number}")
            all_properties.extend(properties)
        
        # The AgentQL handler handles everything including property extraction
        handler["scrape_with_agentql"](url, max_pages=max_pages, output_callback=collect_properties)
        
    # If using hash-based pagination, we need to navigate manually
    elif handler["type"] in ("hash", "basic") and handler.get("get_page_url") and browser_page:
        logger.info("Using hash-based pagination with Playwright")
        page_count = 1
        current_url = url
        
        while page_count <= max_pages:
            logger.info(f"Processing page {page_count} with hash-based navigation")
            
            # Generate URL for the current page
            page_url = handler["get_page_url"](url, page_count)
            logger.info(f"Navigating to: {page_url}")
            
            # Navigate to the page
            browser_page.goto(page_url, timeout=60000)
            current_url = browser_page.url
            
            # Wait for content to load
            time.sleep(3)
            browser_page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(1)
            
            # Here you would extract properties using the browser_page
            # This part would be provided by your existing Playwright-based scraper
            
            # Move to next page
            page_count += 1
            
            # Check if we've reached the last page
            # This would depend on your existing detection logic
    
    else:
        logger.error("No suitable pagination handler available for Remax.com.tn")
    
    return all_properties


# Example usage in the main tunisian_property_scraper.py
"""
# Inside your main scraper, you would import and use this integration

from remax_integration import scrape_remax_site

# When scraping a Remax site:
if "remax.com.tn" in site_config["name"]:
    # Try to use AgentQL first, falling back to hash-based pagination if needed
    properties = scrape_remax_site(page, current_url, max_pages=site_config["max_pages"])
    # Add the properties to your results
    all_properties.extend(properties)
else:
    # Use your existing scraping logic for other sites
    # ...
"""
