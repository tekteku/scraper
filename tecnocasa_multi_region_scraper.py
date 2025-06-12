from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
import csv
import json
import os
import time
import re
from datetime import datetime
from urllib.parse import urlparse

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
    "image_url", "listing_url", "source_site", "page_number", "region"
]

# List of regions to scrape
REGION_URLS = [
    "https://www.tecnocasa.tn/vendre/immeubles/nord-est-ne/bizerte.html",
    "https://www.tecnocasa.tn/vendre/immeubles/centre-est-ce/kairouan.html",
    "https://www.tecnocasa.tn/vendre/immeubles/centre-est-ce/mahdia.html",
    "https://www.tecnocasa.tn/vendre/immeubles/centre-est-ce/sfax.html",
    "https://www.tecnocasa.tn/vendre/immeubles/centre-est-ce/monastir.html",
    "https://www.tecnocasa.tn/vendre/immeubles/centre-est-ce/sousse.html",
    "https://www.tecnocasa.tn/vendre/immeubles/nord-est-ne/cap-bon/kelibia.html"  # Added from previous example
]

def clean_text(text):
    """Clean the text by removing extra spaces and unwanted characters"""
    if not text:
        return ""
    return " ".join(text.strip().split())

def extract_number(text):
    """Extract number from text like '120 m²' or '3 chambres'"""
    if not text:
        return ""
    matches = re.search(r'(\d+)', text)
    if matches:
        return matches.group(1)
    return ""

def extract_price(text):
    """Extract price from text in format like '250 000 DT'"""
    if not text:
        return ""
    # Remove non-numeric characters except spaces
    price_text = re.sub(r'[^\d\s]', '', text)
    # Remove extra spaces and join
    return clean_text(price_text)

def get_region_name(url):
    """Extract region name from URL"""
    parsed_url = urlparse(url)
    path_parts = parsed_url.path.split('/')
    
    # Try to find the region part in the URL
    for part in reversed(path_parts):
        if part and part != 'html' and part != 'immeubles' and part != 'vendre':
            # Remove .html extension if present
            return part.replace('.html', '')
    
    return "unknown-region"

def scrape_tecnocasa_region(url, browser, all_properties):
    """Scrape a specific region from Tecnocasa.tn"""
    domain = "tecnocasa.tn"
    region = get_region_name(url)
    
    print(f"\nStarting scraping of region: {region} at URL: {url}")
    region_properties = []
    
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
        viewport={"width": 1280, "height": 800}
    )
    page = context.new_page()        try:
            # Navigate to the URL with retry mechanism
            print(f"Loading page...")
            max_page_load_attempts = 3
            page_loaded = False
            
            for attempt in range(max_page_load_attempts):
                try:
                    page.goto(url, timeout=90000)  # Extended timeout
                    page.wait_for_load_state("networkidle", timeout=90000)
                    page_loaded = True
                    print(f"Page loaded successfully on attempt {attempt+1}")
                    break
                except Exception as e:
                    print(f"Error loading page on attempt {attempt+1}: {str(e)}")
                    if attempt < max_page_load_attempts - 1:
                        print(f"Waiting before retry...")
                        time.sleep(15)
                    else:
                        raise Exception(f"Failed to load page after {max_page_load_attempts} attempts")
            
            # Wait longer for the page to fully render
            print("Waiting for page to fully initialize...")
            time.sleep(8)
            
            # Take a screenshot for debugging
            screenshot_file = f"{domain}_{region}_homepage.png"
            page.screenshot(path=os.path.join(OUTPUT_FOLDER, screenshot_file))
            print(f"Saved screenshot to {screenshot_file}")
            
            # Scroll down to load lazy content with multiple scrolls
            print("Scrolling to load more content...")
            for scroll in range(3):  # Multiple scrolls for better content loading
                print(f"Scroll {scroll+1}/3")
                page.evaluate(f"window.scrollTo(0, {(scroll+1) * 1000})")
                time.sleep(3)  # Wait between scrolls
            
            page.evaluate("window.scrollTo(0, 0)")  # Back to top
            time.sleep(3)
        
        page_count = 1
        max_pages = 10  # Increased from 5 to handle more pages per region
        
        # Process each page
        while page_count <= max_pages:
            print(f"Processing {region} page {page_count}...")
            
            # Take a screenshot for debugging
            screenshot_file = f"{domain}_{region}_page{page_count}.png"
            page.screenshot(path=os.path.join(OUTPUT_FOLDER, screenshot_file))
            print(f"Saved screenshot to {screenshot_file}")
            
            # Get property items - Tecnocasa specific selectors
            property_selectors = [
                ".immeuble", 
                ".views-row",
                ".view-content .node",
                ".annonce-wrapper"
            ]
            
            # Try each selector
            property_locator = None
            property_count = 0
            
            for selector in property_selectors:
                try:
                    count = page.locator(selector).count()
                    if count > 0:
                        print(f"Found {count} properties with selector: {selector}")
                        property_locator = page.locator(selector)
                        property_count = count
                        break
                except Exception as e:
                    print(f"Error with selector '{selector}': {str(e)}")
            
            if not property_locator or property_count == 0:
                print("No properties found with any selector")
                
                # Try something more generic as a fallback
                try:
                    # Look for any div with a link that might be a property
                    print("Trying generic property detection...")
                    property_locator = page.locator("div.annonce")
                    property_count = property_locator.count()
                    
                    if property_count == 0:
                        property_locator = page.locator("div:has(a:has(img))")
                        property_count = property_locator.count()
                    
                    if property_count > 0:
                        print(f"Found {property_count} potential properties with generic selectors")
                    else:
                        # Save HTML for debugging
                        html = page.content()
                        html_file = os.path.join(OUTPUT_FOLDER, f"{domain}_{region}_page{page_count}.html")
                        with open(html_file, "w", encoding="utf-8") as f:
                            f.write(html)
                        print(f"Saved HTML to {html_file} for debugging")
                        
                        print("No properties found, moving to next region")
                        break
                        
                except Exception as e:
                    print(f"Error with generic property detection: {str(e)}")
                    break
            
            # Process each property
            for i in range(property_count):
                try:
                    # Select current property
                    current_property = property_locator.nth(i)
                    
                    # Extract data with specific French selectors for Tecnocasa
                    
                    # Title
                    title = ""
                    for title_selector in ["h3", ".titre", ".titre-annonce", "h2", ".field-content"]:
                        if current_property.locator(title_selector).count() > 0:
                            title = current_property.locator(title_selector).first.inner_text().strip()
                            break
                    
                    # If title is empty, try to extract from link text
                    if not title:
                        links = current_property.locator("a").all()
                        for link in links:
                            link_text = link.inner_text().strip()
                            if link_text and len(link_text) > 5 and not link_text.startswith("http"):
                                title = link_text
                                break
                    
                    # Price
                    price = ""
                    for price_selector in [".prix", ".price", "strong", ".field-name-field-prix"]:
                        if current_property.locator(price_selector).count() > 0:
                            price_text = current_property.locator(price_selector).first.inner_text().strip()
                            price = extract_price(price_text)
                            break
                    
                    # Location
                    location = ""
                    for location_selector in [".lieu", ".location", ".adresse", ".field-name-field-ville"]:
                        if current_property.locator(location_selector).count() > 0:
                            location = current_property.locator(location_selector).first.inner_text().strip()
                            break
                    
                    # If no location found but we have region, use that
                    if not location:
                        location = region.capitalize()
                    
                    # Bedrooms - Look for "chambres" or "pièces" in French
                    bedrooms = ""
                    for bedrooms_selector in [".chambres", ".pieces", ".nb-pieces", "span:has-text('chambre')", "span:has-text('pièce')"]:
                        if current_property.locator(bedrooms_selector).count() > 0:
                            bedrooms_text = current_property.locator(bedrooms_selector).first.inner_text().strip()
                            bedrooms = extract_number(bedrooms_text)
                            break
                    
                    # Bathrooms - "salle de bain" in French
                    bathrooms = ""
                    for bathrooms_selector in [".sdb", ".salles-de-bain", "span:has-text('salle de bain')", "span:has-text('salle d'eau')"]:
                        if current_property.locator(bathrooms_selector).count() > 0:
                            bathrooms_text = current_property.locator(bathrooms_selector).first.inner_text().strip()
                            bathrooms = extract_number(bathrooms_text)
                            break
                    
                    # Area - "surface" in French
                    area = ""
                    for area_selector in [".surface", ".field-name-field-surface", "span:has-text('m²')", "span:has-text('surface')"]:
                        if current_property.locator(area_selector).count() > 0:
                            area_text = current_property.locator(area_selector).first.inner_text().strip()
                            area = extract_number(area_text)
                            break
                    
                    # Property type - Extract from title or dedicated field
                    property_type = ""
                    for type_selector in [".type", ".categorie", ".field-name-field-type-bien"]:
                        if current_property.locator(type_selector).count() > 0:
                            property_type = current_property.locator(type_selector).first.inner_text().strip()
                            break
                    
                    # If no property type found, try to extract from title
                    if not property_type and title:
                        # Common property types in French
                        property_types = {
                            "appartement": "Appartement",
                            "maison": "Maison",
                            "villa": "Villa",
                            "duplex": "Duplex",
                            "studio": "Studio",
                            "terrain": "Terrain",
                            "local": "Local commercial"
                        }
                        
                        title_lower = title.lower()
                        for key, value in property_types.items():
                            if key in title_lower:
                                property_type = value
                                break
                    
                    # Description
                    description = ""
                    for desc_selector in [".description", ".resume", ".field-name-body"]:
                        if current_property.locator(desc_selector).count() > 0:
                            description = current_property.locator(desc_selector).first.inner_text().strip()
                            break
                    
                    # Features
                    features = []
                    for features_selector in [".amenities li", ".caracteristiques li", ".field-name-field-options li"]:
                        feature_elements = current_property.locator(features_selector).all()
                        for feature_el in feature_elements:
                            feature = feature_el.inner_text().strip()
                            if feature:
                                features.append(feature)
                    
                    # Image URL
                    image_url = ""
                    for image_selector in ["img", ".field-slideshow-image img", ".property-image img"]:
                        image_elements = current_property.locator(image_selector).all()
                        for img_el in image_elements:
                            src = img_el.get_attribute("src") or img_el.get_attribute("data-src") or ""
                            if src and ("jpg" in src or "jpeg" in src or "png" in src):
                                # If relative URL, make it absolute
                                if not src.startswith(("http://", "https://")):
                                    base_url = f"https://{domain}"
                                    src = f"{base_url}{src if src.startswith('/') else '/' + src}"
                                image_url = src
                                break
                        if image_url:
                            break
                    
                    # Listing URL
                    listing_url = ""
                    link_elements = current_property.locator("a").all()
                    for link_el in link_elements:
                        href = link_el.get_attribute("href") or ""
                        if href and "/immeubles/" in href:
                            if not href.startswith(("http://", "https://")):
                                base_url = f"https://{domain}"
                                href = f"{base_url}{href if href.startswith('/') else '/' + href}"
                            listing_url = href
                            break
                    
                    # If we couldn't find a proper URL but have image with link, use its parent
                    if not listing_url and image_url:
                        try:
                            img_element = current_property.locator(f"img[src=\"{image_url}\"]").first
                            parent_a = img_element.locator("xpath=..").first
                            if parent_a.get_attribute("href"):
                                href = parent_a.get_attribute("href")
                                if not href.startswith(("http://", "https://")):
                                    base_url = f"https://{domain}"
                                    href = f"{base_url}{href if href.startswith('/') else '/' + href}"
                                listing_url = href
                        except Exception:
                            pass
                    
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
                        "page_number": page_count,
                        "region": region
                    }
                    
                    # Only add if we have some basic data
                    if title or price or listing_url:
                        region_properties.append(property_data)
                        all_properties.append(property_data)
                        print(f"  Added property {i+1}: {title[:30]}... | {price} | {location}")
                    
                except Exception as e:
                    print(f"Error processing property {i+1}: {str(e)}")
            
            # Save data after each page to avoid losing progress
            if region_properties:
                intermediate_csv = os.path.join(OUTPUT_FOLDER, f"{domain}_{region}_{TIMESTAMP}_page{page_count}.csv")
                intermediate_json = os.path.join(OUTPUT_FOLDER, f"{domain}_{region}_{TIMESTAMP}_page{page_count}.json")
                
                save_to_csv(region_properties, intermediate_csv)
                save_to_json(region_properties, intermediate_json)
                print(f"Saved {len(region_properties)} properties to intermediate files")
            
            # Check if there's a next page
            if page_count < max_pages:
                # Different next page selectors in French
                next_page_selectors = [
                    "li.next a", 
                    "a.next",
                    ".pager-next a",
                    "a:has-text('Suivant')",
                    "a:has-text('Page suivante')",
                    "a:has-text('»')"
                ]
                
                next_clicked = False
                for selector in next_page_selectors:
                    try:
                        next_button = page.locator(selector)
                        if next_button.count() > 0 and next_button.first.is_visible():
                            print(f"Found next page button with selector: {selector}")
                            
                            # Take screenshot before clicking
                            page.screenshot(path=os.path.join(OUTPUT_FOLDER, f"{domain}_{region}_before_next_page{page_count}.png"))
                            
                            next_button.first.click()
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
                    print("No next page button found. Ending pagination for this region.")
                    break
            else:
                print(f"Reached maximum page limit ({max_pages}). Stopping pagination for this region.")
                break
        
        print(f"Completed scraping of region {region}. Total properties: {len(region_properties)}")
        
        # Save region-specific results
        if region_properties:
            region_csv = os.path.join(OUTPUT_FOLDER, f"{domain}_{region}_{TIMESTAMP}_full.csv")
            region_json = os.path.join(OUTPUT_FOLDER, f"{domain}_{region}_{TIMESTAMP}_full.json")
            
            save_to_csv(region_properties, region_csv)
            save_to_json(region_properties, region_json)
            
            print(f"Saved region data to:")
            print(f"- CSV: {region_csv}")
            print(f"- JSON: {region_json}")
        
    except Exception as e:
        print(f"Error scraping region {region}: {str(e)}")
    finally:
        context.close()
    
    return region_properties

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
    """Main function to scrape Tecnocasa.tn for multiple regions"""
    print(f"Starting multi-region Tecnocasa scraper at {TIMESTAMP}")
    print(f"Will scrape {len(REGION_URLS)} regions")
    
    all_properties = []
      with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=False,
            # Slow down operation to avoid being blocked
            slow_mo=100
        )
        
        # Process each region with retry mechanism
        for url in REGION_URLS:
            attempts = 0
            max_attempts = 3
            region_scraped = False
            
            while attempts < max_attempts and not region_scraped:
                try:
                    print(f"Attempt {attempts+1}/{max_attempts} for region URL: {url}")
                    region_properties = scrape_tecnocasa_region(url, browser, all_properties)
                    if region_properties:
                        print(f"Successfully scraped {len(region_properties)} properties from {url}")
                        region_scraped = True
                    else:
                        print(f"No properties found in attempt {attempts+1}. Waiting before retry...")
                        time.sleep(30)  # Wait between retries
                        attempts += 1
                except Exception as e:
                    print(f"Error during attempt {attempts+1} for {url}: {str(e)}")
                    attempts += 1
                    time.sleep(45)  # Longer wait after an error
            
            if not region_scraped:
                print(f"Failed to scrape region after {max_attempts} attempts: {url}")
            
            # Wait between regions to avoid overloading the server
            print(f"Waiting 1 minute before proceeding to the next region...")
            time.sleep(60)
        
        browser.close()
    
    # Save final combined results
    if all_properties:
        csv_filename = os.path.join(OUTPUT_FOLDER, f"tecnocasa.tn_all_regions_{TIMESTAMP}_full.csv")
        json_filename = os.path.join(OUTPUT_FOLDER, f"tecnocasa.tn_all_regions_{TIMESTAMP}_full.json")
        
        save_to_csv(all_properties, csv_filename)
        save_to_json(all_properties, json_filename)
        
        print(f"\nScraping completed. Total properties collected across all regions: {len(all_properties)}")
        print(f"- CSV file: {csv_filename}")
        print(f"- JSON file: {json_filename}")
    else:
        print("\nNo properties were collected from any region.")

if __name__ == "__main__":
    main()
