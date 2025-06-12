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

def clean_text(text):
    """Clean the text by removing extra spaces and unwanted characters"""
    if not text:
        return ""
    return " ".join(text.strip().split())

def extract_text(element, selector):
    """Extract text from an element using selector, with error handling"""
    try:
        if element.locator(selector).count() > 0:
            return element.locator(selector).first.inner_text().strip()
    except Exception as e:
        pass
    return ""

def extract_attribute(element, selector, attribute):
    """Extract attribute from an element using selector, with error handling"""
    try:
        if element.locator(selector).count() > 0:
            return element.locator(selector).first.get_attribute(attribute)
    except Exception as e:
        pass
    return ""

def scrape_single_site():
    """Test scraper that focuses on Fi-dari.tn with link-based extraction"""
    url = "https://fi-dari.tn/search?objectif=vendre&usage=Tout+usage&bounds=[[37.649,7.778],[30.107,11.953]]&page=1"
    domain = "fi-dari.tn"
    
    print(f"\nStarting test scraping of: {url}")
    all_properties = []
    
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36"
        )
        page = context.new_page()
        
        try:
            # Navigate to the URL
            print(f"Loading page...")
            page.goto(url, timeout=60000)
            
            # Wait for content to load
            page.wait_for_selector("a[href^='/bien/']", timeout=60000)
            
            # Take a screenshot for debugging
            screenshot_file = f"{domain}_test_homepage.png"
            page.screenshot(path=os.path.join(OUTPUT_FOLDER, screenshot_file))
            print(f"Saved screenshot to {screenshot_file}")
            
            # Let's process just one page for testing
            print(f"Processing test page...")
            
            # Get property links directly
            property_links = page.locator('a[href^="/bien/"]').all()
            print(f"Found {len(property_links)} property links")
            
            # Process just 3 property links for quick testing
            for i, link in enumerate(property_links[:3]):
                try:
                    # Get the href
                    href = link.get_attribute("href") or ""
                    
                    if not href:
                        print(f"Skipping link {i+1} - no href found")
                        continue
                    
                    # Create the listing URL
                    listing_url = f"https://{domain}{href}"
                    
                    # Get the card element for this link
                    card = link.locator(".b-annonce-card-body").first
                    
                    # Extract data directly from the card
                    title = ""
                    price = ""
                    location = ""
                    image_url = ""
                    
                    # Get title
                    title_el = card.locator(".card-title")
                    if title_el.count() > 0:
                        title = title_el.first.inner_text().strip()
                    
                    # Get price
                    price_el = card.locator(".text-primary")
                    if price_el.count() > 0:
                        price_text = clean_text(price_el.first.inner_text())
                        if "DT" in price_text:
                            price = price_text.split("DT")[0].strip()
                    
                    # Get location
                    location_el = card.locator(".fa-map-marker").locator("xpath=../..")
                    if location_el.count() > 0:
                        location_text = clean_text(location_el.first.inner_text())
                        location = location_text.split("\n")[-1].strip() if "\n" in location_text else location_text
                    
                    # Get image URL
                    img_el = card.locator("img")
                    if img_el.count() > 0:
                        image_url = img_el.first.get_attribute("src") or ""
                    
                    # Extract property type from title
                    property_type = ""
                    if title:
                        if "appartement" in title.lower():
                            property_type = "Appartement"
                        elif "villa" in title.lower():
                            property_type = "Villa"
                        elif "maison" in title.lower():
                            property_type = "Maison"
                        elif "duplex" in title.lower():
                            property_type = "Duplex"
                    
                    # Create property data
                    property_data = {
                        "title": title,
                        "price": price,
                        "location": location,
                        "bedrooms": "",
                        "bathrooms": "",
                        "area": "",
                        "property_type": property_type,
                        "description": "",
                        "features": "",
                        "image_url": image_url,
                        "listing_url": listing_url,
                        "source_site": domain,
                        "page_number": 1
                    }
                    
                    # Add property to our list
                    all_properties.append(property_data)
                    print(f"  Added test property {i+1}: {title[:30]}... | {price} | {location}")
                    
                except Exception as e:
                    print(f"Error processing property link {i+1}: {str(e)}")
            
            print(f"Completed test scraping. Found {len(all_properties)} properties.")
            
        except Exception as e:
            print(f"Error in test scraping: {str(e)}")
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
    """Main function to run test scraper"""
    print(f"Starting test scraper at {TIMESTAMP}")
    
    # Scrape the site
    properties = scrape_single_site()
    
    # Save results
    if properties:
        csv_filename = os.path.join(OUTPUT_FOLDER, f"test_scraper_{TIMESTAMP}.csv")
        json_filename = os.path.join(OUTPUT_FOLDER, f"test_scraper_{TIMESTAMP}.json")
        
        save_to_csv(properties, csv_filename)
        save_to_json(properties, json_filename)
        
        print(f"\nTest scraping completed. Properties collected: {len(properties)}")
        print(f"- CSV file: {csv_filename}")
        print(f"- JSON file: {json_filename}")
    else:
        print("\nNo properties were collected during test.")

if __name__ == "__main__":
    main()
