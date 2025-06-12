"""
Test script for Remax integration into Tunisian Property Scraper
"""

import os
import json
import time
import logging
from datetime import datetime
from playwright.sync_api import sync_playwright
from urllib.parse import urlparse

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("RemaxIntegrationTest")

# Create output folders for test
TEST_DATA_FOLDER = "test_data"
os.makedirs(TEST_DATA_FOLDER, exist_ok=True)

# Generate timestamp for this test
TIMESTAMP = datetime.now().strftime('%Y%m%d_%H%M%S')

def get_domain_name(url):
    """Extract domain name from URL"""
    parsed_url = urlparse(url)
    domain = parsed_url.netloc
    if domain.startswith('www.'):
        domain = domain[4:]
    return domain

def wait_with_random_delay(min_seconds=2, max_seconds=5):
    """Wait for a random amount of time between min and max seconds"""
    delay = min_seconds + (max_seconds - min_seconds) * random.random()
    time.sleep(delay)

def save_to_json(data, output_file):
    """Save data to JSON file"""
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info(f"Saved {len(data)} items to {output_file}")

def save_to_csv(data, output_file):
    """Save data to CSV file"""
    if not data:
        logger.warning(f"No data to save to {output_file}")
        return
    
    # Get all field names from all properties
    fieldnames = set()
    for item in data:
        for key in item.keys():
            fieldnames.add(key)
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=sorted(list(fieldnames)))
        writer.writeheader()
        writer.writerows(data)
    
    logger.info(f"Saved {len(data)} items to {output_file}")

def test_remax_integration():
    """Test the Remax integration"""
    # Define test configuration
    site_config = {
        "name": "remax.com.tn",
        "base_url": "https://www.remax.com.tn/PublicListingList.aspx",
        "max_pages": 3,  # Limited to 3 pages for testing
        "property_selectors": [".gallery-item", ".propertyListItem", ".property-item", ".listingGridBox"],
        "title_selectors": [".gallery-title a", ".property-title", "h3", ".listingTitle", ".property-address"],
        "price_selectors": [".gallery-price-main .proplist_price", ".gallery-price a", ".price"],
        "location_selectors": [".gallery-title a", ".location", ".property-location"],
        "area_selectors": [".gallery-icons img[data-original-title*='Mètres']", ".property-size", ".surface"],
        "bedrooms_selectors": [".gallery-icons img[data-original-title*='chambres']", ".bedrooms", ".beds"],
        "bathrooms_selectors": [".gallery-icons img[data-original-title*='salles de bain']", ".bathrooms", ".baths"],
        "features_selectors": [".features", ".amenities", ".propertyFeatures"],
        "hash_url_pagination": True
    }
    
    # First method - import directly from the remax_playwright_integration module
    try:
        from remax_playwright_integration import scrape_remax_with_playwright
        logger.info("Method 1: Testing remax_playwright_integration.py")
        properties = scrape_remax_with_playwright(
            site_config["base_url"], 
            max_pages=site_config["max_pages"]
        )
        output_file = os.path.join(TEST_DATA_FOLDER, f"remax_method1_{TIMESTAMP}.json")
        save_to_json(properties, output_file)
        logger.info(f"Method 1 found {len(properties)} properties")
    except ImportError:
        logger.error("remax_playwright_integration.py not found")
    
    # Second method - import from remax_helper 
    try:
        import remax_helper
        logger.info("Method 2: Testing remax_helper.py")
        
        properties = []
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(viewport={"width": 1280, "height": 800})
            page = context.new_page()
            
            try:
                # Navigate to base URL
                page.goto(site_config["base_url"], wait_until="domcontentloaded")
                
                # Add hash parameters if needed
                current_url = page.url
                if "#" not in current_url:
                    hash_url = remax_helper.handle_remax_hash_pagination(current_url, 1)
                    page.goto(hash_url, wait_until="domcontentloaded")
                    time.sleep(3)
                
                # Process pages
                page_count = 1
                site_properties = []
                
                while page_count <= site_config["max_pages"]:
                    logger.info(f"Processing page {page_count}")
                    
                    # Extract properties
                    property_elements = page.query_selector_all(", ".join(site_config["property_selectors"]))
                    logger.info(f"Found {len(property_elements)} property elements")
                    
                    # Process properties
                    for element in property_elements:
                        prop_data = remax_helper.extract_remax_property_data(
                            element, site_config, site_config["name"], page_count
                        )
                        site_properties.append(prop_data)
                    
                    # Go to next page if not at max
                    if page_count >= site_config["max_pages"]:
                        break
                    
                    # Navigate to next page
                    next_page = page_count + 1
                    next_url = remax_helper.handle_remax_hash_pagination(page.url, next_page)
                    page.goto(next_url, wait_until="domcontentloaded")
                    page_count += 1
                    time.sleep(3)
                
                properties = site_properties
                
            except Exception as e:
                logger.error(f"Error in Method 2: {e}")
            
            finally:
                browser.close()
        
        output_file = os.path.join(TEST_DATA_FOLDER, f"remax_method2_{TIMESTAMP}.json")
        save_to_json(properties, output_file)
        logger.info(f"Method 2 found {len(properties)} properties")
        
    except ImportError:
        logger.error("remax_helper.py not found")
    
    logger.info("Integration test completed")

if __name__ == "__main__":
    try:
        import csv
        import random
        test_remax_integration()
    except Exception as e:
        logger.error(f"Error during test: {e}")
