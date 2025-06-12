"""
Playwright-based Remax.com.tn Integration

This module provides an alternative approach to scraping Remax.com.tn using 
Playwright directly, with special handling for hash-based URL pagination.
"""

import os
import csv
import time
import json
import logging
import re
from datetime import datetime
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("RemaxPlaywright")

def handle_hash_pagination(current_url, page_number):
    """
    Handle Remax.com.tn hash-based URL pagination
    
    Args:
        current_url (str): The current URL
        page_number (int): The desired page number to navigate to
        
    Returns:
        str: The URL with updated hash fragment for the requested page
    """
    # If URL already has a hash, parse it
    if "#" in current_url:
        base_url, hash_part = current_url.split('#', 1)
        
        # If hash already has page parameter, update it
        if "page=" in hash_part:
            # Replace the current page with the new page
            parts = []
            for param in hash_part.split('&'):
                if param.startswith("page="):
                    parts.append(f"page={page_number}")
                else:
                    parts.append(param)
            new_hash = '&'.join(parts)
            return f"{base_url}#{new_hash}"
        else:
            # Add page parameter to existing hash
            return f"{current_url}&page={page_number}"
    else:
        # Create a new hash with default parameters based on observed URL patterns
        return f"{current_url}#mode=gallery&tt=261&cur=TND&sb=MostRecent&page={page_number}&sc=1048"

def extract_property_details(property_element):
    """
    Extract details from a property listing element
    
    Args:
        property_element: Playwright element representing a property listing
        
    Returns:
        dict: Extracted property details
    """
    property_data = {}
    
    try:
        # Title
        title_element = property_element.query_selector(".gallery-title a, h3, .property-title, .listingTitle, .property-address")
        property_data["title"] = title_element.text_content().strip() if title_element else ""
        
        # Price
        price_element = property_element.query_selector(".gallery-price-main .proplist_price, .gallery-price a, .price")
        property_data["price"] = price_element.text_content().strip() if price_element else ""
        
        # Location (same as title for Remax)
        property_data["location"] = property_data["title"]
        
        # Property type
        type_element = property_element.query_selector(".gallery-transtype span, .propertyType")
        property_data["property_type"] = type_element.text_content().strip() if type_element else ""
        
        # Area, Bedrooms, Bathrooms from gallery-icons
        icons = property_element.query_selector_all(".gallery-icons img")
        for icon in icons:
            tooltip = icon.get_attribute("data-original-title") or ""
            value_element = icon.evaluate_handle("el => el.nextElementSibling")
            value = value_element.text_content().strip() if value_element else ""
            
            if "Mètres carré" in tooltip:
                property_data["area"] = value
            elif "chambres" in tooltip or "pièces" in tooltip:
                property_data["bedrooms"] = value
            elif "salles de bain" in tooltip or "sdb" in tooltip:
                property_data["bathrooms"] = value
            elif "Nombre de pièces" in tooltip:
                property_data["rooms"] = value
        
        # Image URL
        img_element = property_element.query_selector(".gallery-photo img, img.img-responsive")
        property_data["image_url"] = img_element.get_attribute("src") if img_element else ""
        
        # Property URL
        url_element = property_element.query_selector(".gallery-title a, .LinkImage")
        property_data["property_url"] = url_element.get_attribute("href") if url_element else ""
        
        # Check if it's a new listing
        new_element = property_element.query_selector(".exclusive-banner")
        property_data["is_new"] = False
        if new_element and "Nouveau sur le marché" in new_element.text_content():
            property_data["is_new"] = True
        
        # Agent name
        agent_element = property_element.query_selector(".card-agent .popover-name a")
        property_data["agent_name"] = agent_element.text_content().strip() if agent_element else ""
        
    except Exception as e:
        logger.error(f"Error extracting property details: {e}")
    
    return property_data

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
        # Launch browser
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()
        
        try:
            # Navigate to base URL
            page.goto(base_url, wait_until="domcontentloaded")
            
            # Ensure we have the right hash in the URL for the first page
            current_url = page.url
            if "#" not in current_url:
                # Add default hash parameters for the first page
                hash_url = handle_hash_pagination(base_url, 1)
                logger.info(f"Setting initial hash URL: {hash_url}")
                page.goto(hash_url, wait_until="domcontentloaded")
                time.sleep(3)  # Wait for page to load with hash parameters
            
            # Start scraping
            page_count = 1
            
            while page_count <= max_pages:
                logger.info(f"Processing Remax.com.tn page {page_count}")
                
                # Scroll page to load all content
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(2)
                
                # Get current URL with hash
                current_url = page.url
                logger.info(f"Current URL: {current_url}")
                
                # Extract properties from the current page
                property_elements = page.query_selector_all(".gallery-item, .propertyListItem, .property-item, .listingGridBox")
                
                properties_data = []
                for element in property_elements:
                    prop_data = extract_property_details(element)
                    prop_data["page_number"] = page_count
                    prop_data["source_site"] = "remax.com.tn"
                    properties_data.append(prop_data)
                
                logger.info(f"Found {len(properties_data)} properties on page {page_count}")
                
                # Add to all properties
                all_properties.extend(properties_data)
                
                # Process scraped data if callback is provided
                if output_callback and callable(output_callback):
                    output_callback(properties_data, page_count)
                
                # Check if there's a next page
                if page_count >= max_pages:
                    logger.info(f"Reached maximum pages ({max_pages})")
                    break
                
                # Generate URL for next page
                next_page_num = page_count + 1
                next_url = handle_hash_pagination(current_url, next_page_num)
                
                logger.info(f"Navigating to next page: {next_url}")
                page.goto(next_url, wait_until="domcontentloaded")
                page_count += 1
                
                # Wait for the page to load
                time.sleep(3)
                
        except Exception as e:
            logger.error(f"Error during scraping: {e}")
        
        finally:
            # Close the browser
            browser.close()
    
    logger.info(f"Remax.com.tn scraping completed. Total properties collected: {len(all_properties)}")
    return all_properties

def export_to_csv(properties, output_file):
    """
    Export properties to CSV file
    
    Args:
        properties (list): List of property dictionaries
        output_file (str): Path to output CSV file
    """
    if not properties:
        logger.warning("No properties to export")
        return
    
    # Get all field names from all properties
    fieldnames = set()
    for prop in properties:
        fieldnames.update(prop.keys())
    
    # Sort fieldnames for consistency
    fieldnames = sorted(list(fieldnames))
    
    # Write to CSV
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for prop in properties:
            writer.writerow(prop)
    
    logger.info(f"Exported {len(properties)} properties to {output_file}")

def test_remax_playwright():
    """Test the Remax Playwright-based scraper"""
    base_url = "https://www.remax.com.tn/PublicListingList.aspx"
    
    # Create output directory
    output_dir = "real_estate_data"
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate timestamp for output file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = os.path.join(output_dir, f"remax.com.tn_playwright_{timestamp}.csv")
    
    def print_page_data(properties, page_number):
        print(f"Page {page_number}: Found {len(properties)} properties")
        for i, prop in enumerate(properties[:2]):  # Print first 2 properties
            print(f"  Property {i+1}: {prop.get('title', 'No title')} - {prop.get('price', 'No price')}")
    
    # Run the test scrape with a callback to print some data
    properties = scrape_remax_with_playwright(
        base_url, 
        max_pages=3, 
        output_callback=print_page_data
    )
    
    # Export to CSV
    export_to_csv(properties, output_file)
    
    print(f"Total properties found: {len(properties)}")
    print(f"Results saved to {output_file}")
    
    return properties

if __name__ == "__main__":
    test_remax_playwright()
