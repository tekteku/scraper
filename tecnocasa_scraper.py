from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
import csv
import json
import os
import time
from datetime import datetime

# Load environment variables
load_dotenv()

# Create output folder
OUTPUT_FOLDER = "real_estate_data"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Generate timestamp for this session
TIMESTAMP = datetime.now().strftime('%Y%m%d_%H%M%S')

# Common field names for CSV
FIELDNAMES = [
    "title", "price", "location", "bedrooms", "bathrooms", 
    "area", "property_type", "description", "features",
    "image_url", "listing_url", "source_site", "page_number"
]

def scrape_tecnocasa():
    """Scrape Tecnocasa.tn"""
    url = "https://www.tecnocasa.tn/vendre/immeubles/nord-est-ne/cap-bon/kelibia.html"
    domain = "tecnocasa.tn"
    
    print(f"\nStarting scraping of: {url}")
    all_properties = []
    
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
            viewport={"width": 1280, "height": 800}
        )
        page = context.new_page()
        
        try:
            # Navigate to the URL
            print(f"Loading page...")
            page.goto(url, timeout=60000)
            page.wait_for_load_state("networkidle", timeout=60000)
            
            # Wait a moment
            time.sleep(3)
            
            # Take a screenshot for debugging
            screenshot_file = f"{domain}_homepage.png"
            page.screenshot(path=os.path.join(OUTPUT_FOLDER, screenshot_file))
            print(f"Saved screenshot to {screenshot_file}")
            
            # Scroll down to load lazy content
            print("Scrolling to load more content...")
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(2)
            
            page_count = 1
            max_pages = 5
            
            # Process each page
            while page_count <= max_pages:
                print(f"Processing page {page_count}...")
                
                # Take a screenshot for debugging
                screenshot_file = f"{domain}_page{page_count}.png"
                page.screenshot(path=os.path.join(OUTPUT_FOLDER, screenshot_file))
                print(f"Saved screenshot to {screenshot_file}")
                
                # Get property items
                property_selectors = [
                    ".views-row",
                    ".view-content .node", 
                    ".immeuble",
                    ".annonce-wrapper"
                ]
                
                # Try each selector
                property_locator = None
                for selector in property_selectors:
                    count = page.locator(selector).count()
                    if count > 0:
                        print(f"Found {count} properties with selector: {selector}")
                        property_locator = page.locator(selector)
                        break
                
                if not property_locator:
                    print("No properties found with any selector")
                    break
                
                # Process each property
                property_count = property_locator.count()
                for i in range(property_count):
                    try:
                        # Select current property
                        current_property = property_locator.nth(i)
                        
                        # Extract data
                        # Title
                        title = ""
                        for title_selector in ["h3", ".field-content a", ".property-title", ".views-field-title"]:
                            if current_property.locator(title_selector).count() > 0:
                                title = current_property.locator(title_selector).first.inner_text().strip()
                                break
                        
                        # Price
                        price = ""
                        for price_selector in [".field-name-field-prix", ".field--name-field-prix", ".prix", ".views-field-field-prix"]:
                            if current_property.locator(price_selector).count() > 0:
                                price = current_property.locator(price_selector).first.inner_text().strip()
                                break
                        
                        # Location
                        location = ""
                        for location_selector in [".field-name-field-ville", ".field--name-field-ville", ".location", ".views-field-field-ville"]:
                            if current_property.locator(location_selector).count() > 0:
                                location = current_property.locator(location_selector).first.inner_text().strip()
                                break
                        
                        # Bedrooms
                        bedrooms = ""
                        for bedrooms_selector in [".field-name-field-nb-pieces", ".field--name-field-nb-pieces", ".chambres", ".views-field-field-nb-pieces"]:
                            if current_property.locator(bedrooms_selector).count() > 0:
                                bedrooms = current_property.locator(bedrooms_selector).first.inner_text().strip()
                                break
                        
                        # Bathrooms - not always available
                        bathrooms = ""
                        for bathrooms_selector in [".field-name-field-salles-de-bain", ".field--name-field-salles-de-bain", ".sdb"]:
                            if current_property.locator(bathrooms_selector).count() > 0:
                                bathrooms = current_property.locator(bathrooms_selector).first.inner_text().strip()
                                break
                        
                        # Area
                        area = ""
                        for area_selector in [".field-name-field-surface", ".field--name-field-surface", ".surface", ".views-field-field-surface"]:
                            if current_property.locator(area_selector).count() > 0:
                                area = current_property.locator(area_selector).first.inner_text().strip()
                                break
                        
                        # Property type
                        property_type = ""
                        for type_selector in [".field-name-field-type-bien", ".field--name-field-type-bien", ".type"]:
                            if current_property.locator(type_selector).count() > 0:
                                property_type = current_property.locator(type_selector).first.inner_text().strip()
                                break
                        
                        # Description - may not be available on listing page
                        description = ""
                        for desc_selector in [".field-name-body", ".body", ".description"]:
                            if current_property.locator(desc_selector).count() > 0:
                                description = current_property.locator(desc_selector).first.inner_text().strip()
                                break
                        
                        # Features
                        features = []
                        for features_selector in [".field-name-field-options li", ".features li", ".options li"]:
                            feature_count = current_property.locator(features_selector).count()
                            if feature_count > 0:
                                for j in range(feature_count):
                                    feature = current_property.locator(features_selector).nth(j).inner_text().strip()
                                    features.append(feature)
                                break
                        
                        # Image URL
                        image_url = ""
                        for image_selector in ["img", ".field-slideshow-image img", ".property-image img"]:
                            if current_property.locator(image_selector).count() > 0:
                                img_element = current_property.locator(image_selector).first
                                image_url = img_element.get_attribute("src") or img_element.get_attribute("data-src") or ""
                                
                                # If relative URL, make it absolute
                                if image_url and not image_url.startswith(("http://", "https://")):
                                    base_url = f"https://{domain}"
                                    image_url = f"{base_url}{image_url if image_url.startswith('/') else '/' + image_url}"
                                break
                        
                        # Listing URL
                        listing_url = ""
                        for url_selector in ["a", "h3 a", ".field-content a"]:
                            if current_property.locator(url_selector).count() > 0:
                                for j in range(current_property.locator(url_selector).count()):
                                    link_element = current_property.locator(url_selector).nth(j)
                                    href = link_element.get_attribute("href") or ""
                                    if href and "immeubles" in href:
                                        listing_url = href
                                        if not listing_url.startswith(("http://", "https://")):
                                            base_url = f"https://{domain}"
                                            listing_url = f"{base_url}{listing_url if listing_url.startswith('/') else '/' + listing_url}"
                                        break
                                if listing_url:  # Break outer loop if we found a URL
                                    break
                        
                        # Create property data
                        property_data = {
                            "title": title,
                            "price": price,
                            "location": location,
                            "bedrooms": bedrooms,
                            "bathrooms": bathrooms,
                            "area": area,
                            "property_type": property_type,
                            "description": description,
                            "features": ", ".join(features),
                            "image_url": image_url,
                            "listing_url": listing_url,
                            "source_site": domain,
                            "page_number": page_count
                        }
                        
                        if title or price or location:  # Only add if we have some basic data
                            all_properties.append(property_data)
                            print(f"  Added property {i+1}: {title[:30]}... | {price} | {location}")
                        
                    except Exception as e:
                        print(f"Error processing property {i+1}: {str(e)}")
                
                # Save data after each page to avoid losing progress
                if all_properties:
                    intermediate_csv = os.path.join(OUTPUT_FOLDER, f"{domain}_{TIMESTAMP}_page{page_count}.csv")
                    intermediate_json = os.path.join(OUTPUT_FOLDER, f"{domain}_{TIMESTAMP}_page{page_count}.json")
                    
                    save_to_csv(all_properties, intermediate_csv)
                    save_to_json(all_properties, intermediate_json)
                    print(f"Saved {len(all_properties)} properties to intermediate files")
                
                # Check if there's a next page
                if page_count < max_pages:
                    # Different next page selectors
                    next_page_selectors = [
                        ".pager-next a", 
                        ".pagination a[rel='next']", 
                        "a:text('Suivant')",
                        "a:text('page suivante')",
                        "a.next",
                        ".next a"
                    ]
                    
                    next_clicked = False
                    for selector in next_page_selectors:
                        try:
                            if page.locator(selector).count() > 0 and page.locator(selector).first.is_visible():
                                print(f"Found next page button with selector: {selector}")
                                
                                # Take screenshot before clicking
                                page.screenshot(path=os.path.join(OUTPUT_FOLDER, f"{domain}_before_next_page{page_count}.png"))
                                
                                page.locator(selector).first.click()
                                next_clicked = True
                                page_count += 1
                                
                                # Wait for page to load
                                page.wait_for_load_state("networkidle", timeout=30000)
                                
                                # Scroll down to load lazy content
                                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                                time.sleep(3)
                                break
                        except Exception as e:
                            print(f"Error clicking next page with selector '{selector}': {str(e)}")
                    
                    if not next_clicked:
                        print("No next page button found. Ending pagination.")
                        break
                else:
                    print(f"Reached maximum page limit ({max_pages}). Stopping pagination.")
                    break
            
            print(f"Completed scraping of {domain}. Total properties: {len(all_properties)}")
            
        except Exception as e:
            print(f"Error scraping {domain}: {str(e)}")
        finally:
            browser.close()
    
    return all_properties

def save_to_csv(data, filename):
    """Save the scraped data to a CSV file"""
    with open(filename, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDNAMES)
        writer.writeheader()
        
        for prop in data:
            # Create a row with all possible fields
            row = {field: "" for field in FIELDNAMES}
            
            # Update with available data
            for key, value in prop.items():
                if key in FIELDNAMES:
                    row[key] = value
                    
            writer.writerow(row)
    
    print(f"Data saved to: {filename}")

def save_to_json(data, filename):
    """Save the scraped data to a JSON file"""
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)
    
    print(f"Data saved to: {filename}")

def main():
    """Main function to scrape Tecnocasa.tn"""
    print(f"Starting scraper at {TIMESTAMP}")
    
    # Scrape the site
    all_properties = scrape_tecnocasa()
    
    # Save final results
    if all_properties:
        csv_filename = os.path.join(OUTPUT_FOLDER, f"tecnocasa.tn_{TIMESTAMP}_full.csv")
        json_filename = os.path.join(OUTPUT_FOLDER, f"tecnocasa.tn_{TIMESTAMP}_full.json")
        
        save_to_csv(all_properties, csv_filename)
        save_to_json(all_properties, json_filename)
        
        print(f"\nScraping completed. Total properties collected: {len(all_properties)}")
        print(f"- CSV file: {csv_filename}")
        print(f"- JSON file: {json_filename}")
    else:
        print("\nNo properties were collected from the site.")

if __name__ == "__main__":
    main()
