from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
import csv
import json
import os
import time
from datetime import datetime
import random

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

# Define site-specific configurations
SITE_CONFIGS = {
    "tecnocasa.tn": {
        "property_selector": ".annonce-wrapper, .property-item",
        "title_selector": ".annonce-title, h2",
        "price_selector": ".annonce-price, .price",
        "location_selector": ".annonce-location, .location",
        "bedrooms_selector": ".annonce-bedrooms, .bedrooms",
        "bathrooms_selector": ".annonce-bathrooms, .bathrooms",
        "area_selector": ".annonce-area, .area",
        "property_type_selector": ".annonce-type, .property-type",
        "description_selector": ".annonce-description, .description",
        "features_selector": ".annonce-features li, .features li",
        "image_selector": ".annonce-image img, .property-image img",
        "listing_url_selector": ".annonce-wrapper a, .property-item a",
        "next_page_selector": ".pagination .next, .pagination-next",
        "wait_time": 3
    },
    "mubawab.tn": {
        "property_selector": ".listingBox, [data-testid='listingBox']",
        "title_selector": ".listingTitle, h2",
        "price_selector": ".prices, .priceTag",
        "location_selector": ".listingLocation, .locationBox",
        "bedrooms_selector": ".bedroom, [data-testid='bedrooms']",
        "bathrooms_selector": ".bathroom, [data-testid='bathrooms']",
        "area_selector": ".surface, [data-testid='area']",
        "property_type_selector": ".listingType, [data-testid='type']",
        "description_selector": ".listingDesc, [data-testid='description']",
        "features_selector": ".specifications li, .amenities li",
        "image_selector": ".imageContainer img, .listingBox img",
        "listing_url_selector": ".listingBox a",
        "next_page_selector": ".pagination a.icon-arrow-right-3, .pagination a[rel='next']",
        "wait_time": 3
    },
    "menzili.tn": {
        "property_selector": ".property-item, .annonce",
        "title_selector": ".property-title, h2",
        "price_selector": ".property-price, .price",
        "location_selector": ".property-location, .location",
        "bedrooms_selector": ".property-bedrooms, .bedrooms",
        "bathrooms_selector": ".property-bathrooms, .bathrooms",
        "area_selector": ".property-area, .area",
        "property_type_selector": ".property-type, .type",
        "description_selector": ".property-description, .description",
        "features_selector": ".property-features li, .features li",
        "image_selector": ".property-image img, .annonce-image img",
        "listing_url_selector": ".property-item a, .annonce a",
        "next_page_selector": ".pagination .next, .nav-links .next, .next-page",
        "wait_time": 3
    },
    "tunisie-annonce.com": {
        "property_selector": ".box-annonce, tr.ligne0, tr.ligne1",
        "title_selector": ".annonce-titre, .texte_annonce a",
        "price_selector": ".annonce-prix, .prix",
        "location_selector": ".annonce-localisation, .localisation",
        "bedrooms_selector": ".annonce-chambres, .chambres",
        "bathrooms_selector": ".annonce-sdb, .sdb",
        "area_selector": ".annonce-surface, .surface",
        "property_type_selector": ".annonce-type, .type",
        "description_selector": ".annonce-desc, .description",
        "features_selector": ".annonce-carac li, .caracteristiques li",
        "image_selector": ".annonce-photo img, .photo img",
        "listing_url_selector": ".box-annonce a, .texte_annonce a",
        "next_page_selector": ".navpage a:contains('Suivante'), .pagination-next",
        "wait_time": 3
    },
    "darcomtunisia.com": {
        "property_selector": ".property-item, .property-box",
        "title_selector": ".property-title, h3",
        "price_selector": ".property-price, .price",
        "location_selector": ".property-location, .location",
        "bedrooms_selector": ".property-bedrooms, .bedrooms",
        "bathrooms_selector": ".property-bathrooms, .bathrooms",
        "area_selector": ".property-area, .area",
        "property_type_selector": ".property-type, .type",
        "description_selector": ".property-description, .description",
        "features_selector": ".property-features li, .features li",
        "image_selector": ".property-image img, .property-thumbnail img",
        "listing_url_selector": ".property-item a, .property-box a",
        "next_page_selector": ".pagination .next, .pagination a:nth-child(n+2)",
        "wait_time": 3
    },
    "fi-dari.tn": {
        "property_selector": ".listing-item, .property-card",
        "title_selector": ".listing-title, h3",
        "price_selector": ".listing-price, .price",
        "location_selector": ".listing-location, .location",
        "bedrooms_selector": ".listing-bedrooms, .bedrooms",
        "bathrooms_selector": ".listing-bathrooms, .bathrooms",
        "area_selector": ".listing-area, .area",
        "property_type_selector": ".listing-type, .type",
        "description_selector": ".listing-description, .description",
        "features_selector": ".listing-features li, .features li",
        "image_selector": ".listing-image img, .property-thumbnail img",
        "listing_url_selector": ".listing-item a, .property-card a",
        "next_page_selector": ".pagination .next, .pagination-next",
        "wait_time": 3
    }
}

# Default configuration for unknown sites
DEFAULT_CONFIG = {
    "property_selector": ".property, .listing, .realty-item, .real-estate, article, .product-item",
    "title_selector": "h1, h2, h3, .title, .name",
    "price_selector": ".price, .amount, .cost",
    "location_selector": ".location, .address, .place",
    "bedrooms_selector": ".bedrooms, .beds, .rooms",
    "bathrooms_selector": ".bathrooms, .baths",
    "area_selector": ".area, .surface, .size",
    "property_type_selector": ".type, .category",
    "description_selector": ".description, .details, .text",
    "features_selector": ".features li, .amenities li, .specs li",
    "image_selector": "img",
    "listing_url_selector": "a",
    "next_page_selector": ".next, .pagination a[rel='next'], a.next, .pagination-next, .pagination [aria-label='Next']",
    "wait_time": 3
}

def get_domain(url):
    """Extract domain from URL"""
    try:
        domain = url.split("//")[1].split("/")[0].replace("www.", "")
        return domain
    except:
        return "unknown"

def get_site_config(domain):
    """Get configuration for a specific domain"""
    return SITE_CONFIGS.get(domain, DEFAULT_CONFIG)

def extract_text(page, selector):
    """Extract text from an element using selector, with error handling"""
    try:
        element = page.locator(selector).first
        if element:
            return element.inner_text().strip()
    except Exception as e:
        pass
    return ""

def extract_attribute(page, selector, attribute):
    """Extract attribute from an element using selector, with error handling"""
    try:
        element = page.locator(selector).first
        if element:
            return element.get_attribute(attribute)
    except Exception as e:
        pass
    return ""

def scrape_site(url):
    """Scrape a real estate website with pagination support"""
    domain = get_domain(url)
    config = get_site_config(domain)
    
    print(f"\nStarting scraping of: {url}")
    print(f"Using configuration for domain: {domain}")
    
    # List to store all properties
    all_properties = []
    
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)  # Set to True for production
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36"
        )
        page = context.new_page()
        
        try:
            # Navigate to the URL
            page.goto(url, timeout=60000)
            page.wait_for_load_state("networkidle", timeout=60000)
            
            # Wait a moment
            time.sleep(config["wait_time"])
            
            # Scroll down to load lazy content
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(2)
            
            page_count = 1
            total_properties = 0
            max_pages = 10  # Limit to avoid infinite loops
            
            # Process each page
            while page_count <= max_pages:
                print(f"Processing page {page_count}...")
                
                # Wait for properties to load
                try:
                    page.wait_for_selector(config["property_selector"], timeout=10000)
                except:
                    print(f"No properties found with selector: {config['property_selector']}")
                
                # Count properties
                property_count = page.locator(config["property_selector"]).count()
                print(f"Found {property_count} properties on page {page_count}")
                
                # Process each property
                for i in range(property_count):
                    try:
                        # Create locator for the current property
                        property_locator = page.locator(config["property_selector"]).nth(i)
                        
                        # Extract data
                        title = ""
                        try:
                            title_locator = property_locator.locator(config["title_selector"]).first
                            if title_locator:
                                title = title_locator.inner_text().strip()
                        except:
                            pass
                        
                        price = ""
                        try:
                            price_locator = property_locator.locator(config["price_selector"]).first
                            if price_locator:
                                price = price_locator.inner_text().strip()
                        except:
                            pass
                        
                        location = ""
                        try:
                            location_locator = property_locator.locator(config["location_selector"]).first
                            if location_locator:
                                location = location_locator.inner_text().strip()
                        except:
                            pass
                        
                        # Extract other data
                        bedrooms = extract_text(property_locator, config["bedrooms_selector"])
                        bathrooms = extract_text(property_locator, config["bathrooms_selector"])
                        area = extract_text(property_locator, config["area_selector"])
                        property_type = extract_text(property_locator, config["property_type_selector"])
                        description = extract_text(property_locator, config["description_selector"])
                        
                        # Extract features as a list
                        features = []
                        for j in range(property_locator.locator(config["features_selector"]).count()):
                            feature = property_locator.locator(config["features_selector"]).nth(j).inner_text().strip()
                            features.append(feature)
                        
                        # Extract image URL
                        image_url = ""
                        try:
                            image_locator = property_locator.locator(config["image_selector"]).first
                            if image_locator:
                                image_url = image_locator.get_attribute("src") or image_locator.get_attribute("data-src") or ""
                        except:
                            pass
                        
                        # Extract listing URL
                        listing_url = ""
                        try:
                            url_locator = property_locator.locator(config["listing_url_selector"]).first
                            if url_locator:
                                relative_url = url_locator.get_attribute("href") or ""
                                if relative_url.startswith("http"):
                                    listing_url = relative_url
                                else:
                                    # Convert relative to absolute URL
                                    base_url = f"https://{domain}"
                                    listing_url = f"{base_url}{relative_url if relative_url.startswith('/') else '/' + relative_url}"
                        except:
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
                            "page_number": page_count
                        }
                        
                        all_properties.append(property_data)
                        total_properties += 1
                        
                    except Exception as e:
                        print(f"Error processing property {i+1}: {e}")
                
                # Check if there's a next page
                if page_count < max_pages:
                    next_selector = config["next_page_selector"]
                    try:
                        # Check if next page element exists and is visible
                        has_next = page.locator(next_selector).count() > 0 and page.locator(next_selector).first.is_visible()
                        
                        if has_next:
                            print("Navigating to next page...")
                            page.locator(next_selector).first.click()
                            page_count += 1
                            
                            # Wait for page to load
                            page.wait_for_load_state("networkidle", timeout=30000)
                            
                            # Scroll down to load lazy content
                            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                            time.sleep(random.uniform(2, 4))
                        else:
                            print("No next page button found. Ending pagination.")
                            break
                    except Exception as e:
                        print(f"Error navigating to next page: {e}")
                        break
                else:
                    print("Reached maximum page limit.")
                    break
            
            print(f"Completed scraping of {domain}. Total properties: {total_properties}")
            
        except Exception as e:
            print(f"Error scraping {domain}: {e}")
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
    """Main function to scrape real estate sites"""
    # Define real estate sites to scrape
    sites = [
        "https://www.tecnocasa.tn/vendre/immeubles/nord-est-ne/cap-bon/kelibia.html",
        "https://www.mubawab.tn/fr/ct/tunis/immobilier-a-vendre",
        "https://www.mubawab.tn/fr/cc/immobilier-a-vendre-all:ci:74566,74830:sc:house-sale,villa-sale",
        "https://www.menzili.tn/immo/vente-immobilier-tunisie",
        "http://www.tunisie-annonce.com/AnnoncesImmobilier.asp?rech_cod_rub=101&rech_cod_typ=10102",
        "https://www.darcomtunisia.com/search?property_types%5B%5D=1&vocations%5B%5D=1&vocations%5B%5D=2&reference=&surface_terrain_min=&prix_max=",
        "https://fi-dari.tn/search?objectif=vendre&usage=Tout+usage&bounds=[[37.649,7.778],[30.107,11.953]]&page=1"
    ]
    
    print(f"Starting real estate scraper at {TIMESTAMP}")
    print(f"Will scrape {len(sites)} websites")
    
    all_properties = []
    
    # Process each site
    for i, site_url in enumerate(sites):
        print(f"\n{'='*50}")
        print(f"Site {i+1}/{len(sites)}: {site_url}")
        print(f"{'='*50}")
        
        try:
            # Get domain for filenames
            domain = get_domain(site_url)
            
            # Scrape the site
            site_properties = scrape_site(site_url)
            all_properties.extend(site_properties)
            
            # Save individual site data
            csv_filename = os.path.join(OUTPUT_FOLDER, f"{domain}_{TIMESTAMP}.csv")
            json_filename = os.path.join(OUTPUT_FOLDER, f"{domain}_{TIMESTAMP}.json")
            
            save_to_csv(site_properties, csv_filename)
            save_to_json(site_properties, json_filename)
            
            # Wait between sites to avoid being blocked
            if i < len(sites) - 1:
                delay = random.uniform(10, 15)
                print(f"Waiting {delay:.1f} seconds before next site...")
                time.sleep(delay)
                
        except Exception as e:
            print(f"Error processing site {site_url}: {e}")
    
    # Save combined data
    if all_properties:
        all_csv_filename = os.path.join(OUTPUT_FOLDER, f"all_properties_{TIMESTAMP}.csv")
        all_json_filename = os.path.join(OUTPUT_FOLDER, f"all_properties_{TIMESTAMP}.json")
        
        save_to_csv(all_properties, all_csv_filename)
        save_to_json(all_properties, all_json_filename)
        
        print(f"\nScraping completed. Total properties collected: {len(all_properties)}")
        print(f"- All properties CSV: {all_csv_filename}")
        print(f"- All properties JSON: {all_json_filename}")
    else:
        print("\nNo properties were collected from any site.")

if __name__ == "__main__":
    main()
