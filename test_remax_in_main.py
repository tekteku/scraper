"""
Test script for Remax integration in the main scraper
"""

import os
import sys
import json
import logging
from datetime import datetime
from playwright.sync_api import sync_playwright

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("RemaxMainTest")

# Create output folders for test
TEST_DATA_FOLDER = "test_data/remax_main_test"
os.makedirs(TEST_DATA_FOLDER, exist_ok=True)

def save_to_json(data, output_file):
    """Save data to JSON file"""
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info(f"Saved data to {output_file}")

def test_remax_in_main():
    """Test the Remax.com.tn scraper directly"""
    # Import the function from tunisian_property_scraper.py
    from tunisian_property_scraper import scrape_remax_site
    
    # Get the Remax configuration
    from tunisian_property_scraper import SITE_CONFIGS
    remax_config = next((config for config in SITE_CONFIGS if config["name"] == "remax.com.tn"), None)
    
    if not remax_config:
        logger.error("Remax configuration not found in SITE_CONFIGS")
        return
    
    # Modify config for faster testing
    remax_test_config = remax_config.copy()
    remax_test_config["max_pages"] = 2
    
    # Create a timestamp for test files
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Run the Remax scraper directly
    logger.info("Starting Remax.com.tn scraper test")
    
    # Initialize empty list for all properties
    all_properties = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        
        try:
            # Create a page and navigate to Remax to check if we can extract the HTML for analysis
            context = browser.new_context()
            page = context.new_page()
            logger.info("Navigating to Remax to check HTML structure")
            page.goto(remax_test_config["base_url"], wait_until="domcontentloaded")
            
            # Wait for page to load
            page.wait_for_timeout(5000)
            
            # Save HTML for analysis
            html_folder = os.path.join(TEST_DATA_FOLDER, "html")
            os.makedirs(html_folder, exist_ok=True)
            html_path = os.path.join(html_folder, f"remax_page_{timestamp}.html")
            
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(page.content())
            logger.info(f"Saved HTML to {html_path} for analysis")
            
            # Take a screenshot
            screenshot_path = os.path.join(TEST_DATA_FOLDER, f"remax_page_{timestamp}.png")
            page.screenshot(path=screenshot_path)
            logger.info(f"Saved screenshot to {screenshot_path}")
            
            # Check for property elements with different selectors
            selectors_to_try = [
                ".gallery-item", 
                ".propertyListItem", 
                ".property-item", 
                ".listingGridBox",
                ".property-container",
                ".listing-item",
                ".search-result-item",
                ".property-card",
                "[class*='property']",
                "[class*='listing']"
            ]
            
            for selector in selectors_to_try:
                elements = page.query_selector_all(selector)
                logger.info(f"Selector '{selector}' found {len(elements)} elements")
            
            # Close this context
            context.close()
            
            # Run the scraper
            properties = scrape_remax_site(remax_test_config, browser, all_properties)
            
            # Log results
            logger.info(f"Test completed. Found {len(properties)} properties")
            
            # Save the results
            output_file = os.path.join(TEST_DATA_FOLDER, f"remax_test_{timestamp}.json")
            save_to_json(properties, output_file)
            
            if len(properties) > 0:
                logger.info("Sample property details:")
                for field, value in list(properties[0].items())[:5]:
                    logger.info(f"  {field}: {value}")
        except Exception as e:
            logger.error(f"Error running Remax scraper: {e}")
            import traceback
            logger.error(traceback.format_exc())
        finally:
            browser.close()

if __name__ == "__main__":
    try:
        test_remax_in_main()
    except Exception as e:
        logger.error(f"Error during test: {e}")
        import traceback
        traceback.print_exc()
