"""
Remax.com.tn Playwright-based Pagination Module

This module uses Playwright to handle Remax.com.tn's hash-based URL pagination.
Since AgentQL integration is proving challenging, we'll use Playwright directly
which gives us similar capabilities for navigating hash-based URLs.
"""

import time
import logging
import re
import csv
import os
from datetime import datetime
from playwright.sync_api import sync_playwright

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("RemaxPlaywright")

def scrape_remax_with_playwright(base_url, max_pages=20, output_callback=None):
    """
    Scrape Remax.com.tn using Playwright with proper hash-based pagination handling
    
    Args:
        base_url (str): The base URL for Remax.com.tn
        max_pages (int): Maximum number of pages to scrape
        output_callback (function): Optional callback function to process scraped data
                                   Signature: callback(properties, page_number)
    
    Returns:
        list: All property listings found across pages
    """
    logger.info(f"Starting Remax.com.tn scraping with Playwright: {base_url}")
    
    all_properties = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Navigate to the base URL
        page.goto(base_url, timeout=60000)
        
        # Ensure we have the right hash in the URL for the first page
        current_url = page.url
        if "#" not in current_url:
            # Add default hash parameters for the first page
            hash_url = f"{base_url}#mode=gallery&tt=261&cur=TND&sb=MostRecent&page=1&sc=1048"
            logger.info(f"Setting initial hash URL: {hash_url}")
            page.goto(hash_url, timeout=60000)
            time.sleep(3)  # Wait for page to load with hash parameters
        
        # Initial scrolling to ensure all content is loaded
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(2)
        
        page_count = 1
        
        # Loop through pages as long as there's a next page and we haven't hit max_pages
        while page_count <= max_pages:
            logger.info(f"Processing Remax.com.tn page {page_count}")
            
            try:
                # Current URL and hash
                current_url = page.url
                current_hash = page.evaluate("window.location.hash")
                
                logger.info(f"Current URL: {current_url}")
                logger.info(f"Current hash: {current_hash}")
                
                # Extract properties from the current page
                properties_data = extract_properties_from_page(page)
                
                logger.info(f"Found {len(properties_data)} properties on page {page_count}")
                
                # Add page number to each property
                for prop in properties_data:
                    prop['page_number'] = page_count
                    prop['source_site'] = "remax.com.tn"
                    all_properties.append(prop)
                
                # Process scraped data if callback is provided
                if output_callback and callable(output_callback):
                    output_callback(properties_data, page_count)
                
                # Check if there's a next page button
                next_button_exists = page.evaluate("""() => {
                    const nextButtons = document.querySelectorAll('#ctl00_ContentPlaceHolder1_ListViewPager_NextButton:not([disabled]), .pagination a:not(.aspNetDisabled), .pagerLink:not([disabled])');
                    return nextButtons.length > 0;
                }""")
                
                next_button_disabled = page.evaluate("""() => {
                    const disabledButtons = document.querySelectorAll('#ctl00_ContentPlaceHolder1_ListViewPager_NextButton[disabled], .pagination a.aspNetDisabled, .pagerLink[disabled]');
                    return disabledButtons.length > 0;
                }""")
                
                logger.info(f"Next page button exists: {next_button_exists}")
                logger.info(f"Next page button disabled: {next_button_disabled}")
                
                if next_button_exists and not next_button_disabled:
                    # Generate the new hash URL for the next page
                    next_page_num = page_count + 1
                    
                    # Parse the current hash to update the page number
                    if "#" in current_url:
                        base_url, hash_part = current_url.split('#', 1)
                        # Update the page parameter in the hash
                        if "page=" in hash_part:
                            new_hash = re.sub(r'page=\d+', f'page={next_page_num}', hash_part)
                        else:
                            new_hash = f"{hash_part}&page={next_page_num}"
                        next_url = f"{base_url}#{new_hash}"
                    else:
                        # If no hash in URL (should not happen at this point), create a new one
                        next_url = f"{current_url}#mode=gallery&tt=261&cur=TND&sb=MostRecent&page={next_page_num}&sc=1048"
                    
                    logger.info(f"Navigating to next page: {next_url}")
                    page.goto(next_url, timeout=60000)
                    page_count += 1
                    
                    # Wait for the page to load and scroll to show all content
                    time.sleep(3)
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    time.sleep(1)
                else:
                    logger.info("No more pages available or reached the end")
                    break
                
            except Exception as e:
                logger.error(f"Error processing page {page_count}: {str(e)}")
                break
        
        # Close the browser
        browser.close()
    
    logger.info(f"Remax.com.tn scraping completed. Total properties collected: {len(all_properties)}")
    return all_properties

def extract_properties_from_page(page):
    """
    Extract property data from the current page
    
    Args:
        page: The Playwright page object
    
    Returns:
        list: List of property dictionaries
    """
    properties = []
    
    # Get all property listing elements
    property_elements = page.query_selector_all(".propertyListItem, .property-item, .property-list-item, .listingGridBox")
    
    for element in property_elements:
        try:
            # Extract property details
            title_element = element.query_selector("h3, .property-title, .listingTitle, .property-address, .addressLine1")
            title = title_element.text_content().strip() if title_element else ""
            
            price_element = element.query_selector(".price, .property-price, .listingPrice, span:has-text('TND'), span:has-text('DT')")
            price = price_element.text_content().strip() if price_element else ""
            
            location_element = element.query_selector(".location, .property-location, .listingLocation, .property-area, .addressLine2, .cityLabel")
            location = location_element.text_content().strip() if location_element else ""
            
            area_element = element.query_selector("span:has-text('m²'), .property-size, .surface, .area")
            area = area_element.text_content().strip() if area_element else ""
            
            bedrooms_element = element.query_selector("span:has-text('chambres'), span:has-text('pièces'), .bedrooms, .beds")
            bedrooms = bedrooms_element.text_content().strip() if bedrooms_element else ""
            
            bathrooms_element = element.query_selector("span:has-text('sdb'), span:has-text('salles de bain'), .bathrooms, .baths")
            bathrooms = bathrooms_element.text_content().strip() if bathrooms_element else ""
            
            features_element = element.query_selector(".features, .amenities, .propertyFeatures, .property-details")
            features = features_element.text_content().strip() if features_element else ""
            
            image_element = element.query_selector("img")
            image_url = image_element.get_attribute("src") if image_element else ""
            
            link_element = element.query_selector("a")
            property_url = link_element.get_attribute("href") if link_element else ""
            
            # Create property object
            property_data = {
                "title": title,
                "price": price,
                "location": location,
                "area": area,
                "bedrooms": bedrooms,
                "bathrooms": bathrooms,
                "features": features,
                "image_url": image_url,
                "property_url": property_url
            }
            
            properties.append(property_data)
            
        except Exception as e:
            logger.error(f"Error extracting property data: {str(e)}")
    
    return properties

def save_to_csv(properties, filename):
    """
    Save properties to a CSV file
    
    Args:
        properties (list): List of property dictionaries
        filename (str): Output filename
    """
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    # Get all keys to use as fieldnames
    fieldnames = set()
    for prop in properties:
        fieldnames.update(prop.keys())
    fieldnames = sorted(list(fieldnames))
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for prop in properties:
            writer.writerow(prop)
    
    logger.info(f"Saved {len(properties)} properties to {filename}")

# Test function
def test_remax_playwright():
    """Test the Remax Playwright pagination"""
    base_url = "https://www.remax.com.tn/PublicListingList.aspx"
    
    # Generate output filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_dir = os.path.join("real_estate_data", "tests")
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"remax_playwright_test_{timestamp}.csv")
    
    # Define a callback function to print progress
    def print_page_data(properties, page_number):
        print(f"Page {page_number}: Found {len(properties)} properties")
        for i, prop in enumerate(properties[:2]):  # Print first 2 properties
            print(f"  Property {i+1}: {prop.get('title', 'No title')} - {prop.get('price', 'No price')}")
    
    # Run the test scrape with a callback to print some data
    properties = scrape_remax_with_playwright(base_url, max_pages=2, output_callback=print_page_data)
    print(f"Total properties found: {len(properties)}")
    
    # Save results to CSV
    save_to_csv(properties, output_file)
    
    return properties

if __name__ == "__main__":
    test_remax_playwright()
