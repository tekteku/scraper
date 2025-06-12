"""
Test script for Remax property detail pages
"""

import os
import json
import time
import logging
from playwright.sync_api import sync_playwright
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("RemaxDetailTest")

def save_to_json(data, output_file):
    """Save data to JSON file"""
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info(f"Saved data to {output_file}")

def test_remax_property_details():
    """Test extracting details directly from property detail pages"""
    test_urls = [
        "https://www.remax.com.tn/fr-tn/biens/appartement/vente/le-bardo/1048044004-13",
        "https://www.remax.com.tn/fr-tn/biens/lot-de-terrains/vente/hammamet-sud/8057/1048042026-4"
    ]
    
    # Create output directory
    output_dir = "test_data/remax_details"
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate timestamp for filenames
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        all_properties = []
        
        for i, url in enumerate(test_urls):
            logger.info(f"Processing property URL {i+1}/{len(test_urls)}: {url}")
            
            try:
                # Navigate to the property page
                page.goto(url, wait_until="domcontentloaded")
                time.sleep(3)  # Wait for dynamic content
                
                # Save screenshot for debugging
                screenshot_path = os.path.join(output_dir, f"property_{i+1}_{timestamp}.png")
                page.screenshot(path=screenshot_path)
                logger.info(f"Saved screenshot to {screenshot_path}")
                
                # Extract property data
                property_data = {
                    "source_site": "remax.com.tn",
                    "property_url": url
                }
                
                # Extract property ID from URL
                url_parts = url.split("/")
                if url_parts:
                    id_part = url_parts[-1]
                    if "-" in id_part:
                        property_data["property_id"] = id_part.split("-")[0]
                    
                    # Extract property type from URL
                    if len(url_parts) > 4:
                        property_data["property_type"] = url_parts[4].replace("-", " ").title()
                
                # Title
                title_selector = page.query_selector("h1, .property-title, h3.title")
                if title_selector:
                    property_data["title"] = title_selector.text_content().strip()
                
                # Price
                price_selector = page.query_selector(".price-main, .main-price, .price-container")
                if price_selector:
                    property_data["price"] = price_selector.text_content().strip()
                
                # Features from property details section
                details_section = page.query_selector(".property-details, .property-features")
                if details_section:
                    # Method 1: Look for specific detail rows
                    detail_items = details_section.query_selector_all(".detail-item, .feature-item, .row")
                    
                    for item in detail_items:
                        label_element = item.query_selector(".detail-label, .feature-label, .label")
                        value_element = item.query_selector(".detail-value, .feature-value, .value")
                        
                        if label_element and value_element:
                            label = label_element.text_content().strip().lower()
                            value = value_element.text_content().strip()
                            
                            property_data[f"detail_{label}"] = value
                            
                            if "surface" in label or "area" in label:
                                property_data["area"] = value
                            elif "chambres" in label or "bedrooms" in label:
                                property_data["bedrooms"] = value
                            elif "salles de bain" in label or "bathrooms" in label:
                                property_data["bathrooms"] = value
                            elif "terrain" in label or "land" in label:
                                property_data["land_area"] = value
                
                # Method 2: Look for data attributes or structured data
                structured_data = page.evaluate("""() => {
                    const jsonLd = document.querySelector('script[type="application/ld+json"]');
                    if (jsonLd) {
                        try {
                            return JSON.parse(jsonLd.textContent);
                        } catch (e) {
                            return null;
                        }
                    }
                    return null;
                }""")
                
                if structured_data:
                    property_data["structured_data"] = structured_data
                
                # Method 3: Extract all text content from key sections
                sections = {
                    "description": ".property-description, .description",
                    "features": ".property-features, .features",
                    "location": ".property-location, .location"
                }
                
                for key, selector in sections.items():
                    section_element = page.query_selector(selector)
                    if section_element:
                        property_data[key] = section_element.text_content().strip()
                
                # Method 4: Look for image galleries
                gallery_images = page.query_selector_all(".property-gallery img, .gallery img")
                if gallery_images:
                    property_data["images"] = []
                    for img in gallery_images:
                        src = img.get_attribute("src")
                        if src:
                            property_data["images"].append(src)
                
                # Save this property's data
                all_properties.append(property_data)
                
                # Save to individual file
                output_file = os.path.join(output_dir, f"property_{i+1}_{timestamp}.json")
                save_to_json(property_data, output_file)
                
            except Exception as e:
                logger.error(f"Error processing URL {url}: {e}")
        
        browser.close()
    
    # Save all properties together
    combined_file = os.path.join(output_dir, f"all_properties_{timestamp}.json")
    save_to_json(all_properties, combined_file)
    
    logger.info(f"Completed testing {len(test_urls)} property pages")
    return all_properties

if __name__ == "__main__":
    test_remax_property_details()
