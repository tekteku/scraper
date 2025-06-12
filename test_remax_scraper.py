# Test script for the Remax portion of the Tunisian property scraper
# This will test just the Remax.com.tn site with our hash-based URL pagination

import sys
import time
import os
import logging
from datetime import datetime
from playwright.sync_api import sync_playwright
from tunisian_property_scraper import (
    SITE_CONFIGS, 
    scrape_properties, 
    RAW_DATA_FOLDER,
    SCREENSHOTS_FOLDER,
    HTML_DUMPS_FOLDER
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("remax_test.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("RemaxTest")

# Make sure the output folders exist
for folder in [RAW_DATA_FOLDER, SCREENSHOTS_FOLDER, HTML_DUMPS_FOLDER]:
    os.makedirs(folder, exist_ok=True)

def test_remax_scraping():
    """Test the Remax.com.tn site scraping with hash-based URL pagination"""
    
    # Find the Remax configuration
    remax_config = None
    for config in SITE_CONFIGS:
        if config["name"] == "remax.com.tn":
            remax_config = config
            break
    
    if not remax_config:
        logger.error("Remax.com.tn configuration not found in SITE_CONFIGS!")
        return
    
    # Verify hash_url_pagination flag is set
    if not remax_config.get("hash_url_pagination", False):
        logger.warning("hash_url_pagination flag is not set in Remax config, but continuing anyway")
    
    # Set a lower page limit for the test
    test_config = remax_config.copy()
    test_config["max_pages"] = 3  # Just test 3 pages
    
    logger.info(f"Testing Remax.com.tn scraping with configuration: {test_config}")
    
    # Generate timestamp for this test
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Initialize storage for properties
    all_properties = []
    
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=False,  # Show the browser for debugging
            args=[
                '--disable-dev-shm-usage',
                '--disable-features=site-per-process',
                '--disable-web-security',
                '--no-sandbox',
                '--window-size=1920,1080'
            ],
            slow_mo=100,  # Slow down operations for better visibility
            timeout=180000  # 3 minutes timeout
        )
        
        try:
            # Run the scraper on Remax only
            remax_properties = scrape_properties(test_config, browser, all_properties)
            
            # Log the results
            logger.info(f"Test completed. Scraped {len(remax_properties)} properties from Remax.")
            
            # Save the results to a special test file
            if remax_properties:
                import csv
                
                test_csv = os.path.join(RAW_DATA_FOLDER, f"remax_test_{timestamp}.csv")
                fieldnames = ["title", "price", "location", "bedrooms", "bathrooms", 
                            "area", "land_area", "property_type", "description", "features",
                            "image_url", "listing_url", "source_site", "page_number", "region"]
                
                with open(test_csv, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    for item in remax_properties:
                        writer.writerow({k: item.get(k, '') for k in fieldnames})
                
                logger.info(f"Saved test results to {test_csv}")
            
        except Exception as e:
            logger.error(f"Error during test: {str(e)}")
        finally:
            browser.close()
    
    return all_properties

if __name__ == "__main__":
    print("Starting Remax.com.tn scraper test...")
    properties = test_remax_scraping()
    print(f"Test complete. Scraped {len(properties) if properties else 0} properties.")
