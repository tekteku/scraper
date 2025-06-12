from dotenv import load_dotenv
import agentql
import csv
import json
import os
import time
from datetime import datetime
import random
from playwright.sync_api import sync_playwright

# Load environment variables
load_dotenv()

# Define real estate sites to scrape
REAL_ESTATE_SITES = [
    "https://www.tecnocasa.tn/vendre/immeubles/nord-est-ne/cap-bon/kelibia.html",
    "https://www.mubawab.tn/fr/ct/tunis/immobilier-a-vendre",
    "https://www.mubawab.tn/fr/cc/immobilier-a-vendre-all:ci:74566,74830:sc:house-sale,villa-sale",
    "https://www.menzili.tn/immo/vente-immobilier-tunisie",
    "http://www.tunisie-annonce.com/AnnoncesImmobilier.asp?rech_cod_rub=101&rech_cod_typ=10102",
    "https://www.darcomtunisia.com/search?property_types%5B%5D=1&vocations%5B%5D=1&vocations%5B%5D=2&reference=&surface_terrain_min=&prix_max=",
    "https://fi-dari.tn/search?objectif=vendre&usage=Tout+usage&bounds=[[37.649,7.778],[30.107,11.953]]&page=1"
]

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

def extract_real_estate_data(page):
    """Extract real estate data from the page"""
    return page.evaluate("""() => {
        // Function to extract text content safely
        const getText = (selector) => {
            const el = document.querySelector(selector);
            return el ? el.textContent.trim() : '';
        };
        
        // Function to extract attribute safely
        const getAttribute = (selector, attr) => {
            const el = document.querySelector(selector);
            return el ? el.getAttribute(attr) : '';
        };
        
        // Extract property listings
        const listings = [];
        
        // Different sites have different selectors for property listings
        const listingSelectors = [
            '.property-item', '.listing-item', '.property-card',
            '.real-estate-item', '.annonce-item', '.property',
            '.listing', '.realty-item', '[data-testid="listing-card"]'
        ];
        
        // Try each selector until we find listings
        let elements = [];
        for (const selector of listingSelectors) {
            elements = document.querySelectorAll(selector);
            if (elements.length > 0) break;
        }
        
        // Process each listing
        for (const el of elements) {
            try {
                // Different sites have different data structures, try various selectors
                const title = el.querySelector('.title, .property-title, h2, h3, .listing-title')?.textContent.trim() || '';
                
                // Try to extract price with various selectors
                let price = '';
                const priceEl = el.querySelector('.price, .property-price, [data-testid="price"], .listing-price');
                if (priceEl) price = priceEl.textContent.trim();
                
                // Try to extract location
                let location = '';
                const locationEl = el.querySelector('.location, .property-location, .address, .listing-location');
                if (locationEl) location = locationEl.textContent.trim();
                
                // Try to extract bedrooms
                let bedrooms = '';
                const bedroomsEl = el.querySelector('.bedrooms, .beds, [data-testid="bedrooms"]');
                if (bedroomsEl) bedrooms = bedroomsEl.textContent.trim();
                
                // Try to extract bathrooms
                let bathrooms = '';
                const bathroomsEl = el.querySelector('.bathrooms, .baths, [data-testid="bathrooms"]');
                if (bathroomsEl) bathrooms = bathroomsEl.textContent.trim();
                
                // Try to extract area
                let area = '';
                const areaEl = el.querySelector('.area, .surface, [data-testid="area"]');
                if (areaEl) area = areaEl.textContent.trim();
                
                // Try to extract property type
                let propertyType = '';
                const typeEl = el.querySelector('.property-type, .type, [data-testid="property-type"]');
                if (typeEl) propertyType = typeEl.textContent.trim();
                
                // Try to extract description
                let description = '';
                const descEl = el.querySelector('.description, .property-description, [data-testid="description"]');
                if (descEl) description = descEl.textContent.trim();
                
                // Try to extract features
                let features = [];
                const featureEls = el.querySelectorAll('.feature, .property-feature, .amenity');
                for (const featureEl of featureEls) {
                    features.push(featureEl.textContent.trim());
                }
                
                // Try to extract image URL
                let imageUrl = '';
                const imgEl = el.querySelector('img');
                if (imgEl) {
                    imageUrl = imgEl.src || imgEl.getAttribute('data-src') || '';
                }
                
                // Try to extract listing URL
                let listingUrl = '';
                const linkEl = el.querySelector('a');
                if (linkEl) {
                    listingUrl = linkEl.href || '';
                }
                
                // Add to listings
                listings.push({
                    title,
                    price,
                    location,
                    bedrooms,
                    bathrooms,
                    area,
                    property_type: propertyType,
                    description,
                    features: features.join(', '),
                    image_url: imageUrl,
                    listing_url: listingUrl
                });
            } catch (error) {
                console.error('Error processing listing:', error);
            }
        }
        
        return listings;
    }""")

def has_next_page(page):
    """Check if there is a next page button that is enabled"""
    return page.evaluate("""() => {
        // Different sites have different selectors for next page button
        const nextPageSelectors = [
            '.next-page', '.pagination-next', 'a.next', 'li.next a',
            '.pagination a[rel="next"]', '.pagination a:contains("Next")',
            '.pagination a:contains("Suivant")'
        ];
        
        // Try each selector
        for (const selector of nextPageSelectors) {
            const nextButton = document.querySelector(selector);
            if (nextButton && !nextButton.disabled && nextButton.style.display !== 'none') {
                return true;
            }
        }
        
        return false;
    }""")

def click_next_page(page):
    """Click the next page button"""
    # Different sites have different selectors for next page button
    next_page_selectors = [
        '.next-page', '.pagination-next', 'a.next', 'li.next a',
        '.pagination a[rel="next"]', '.pagination a:contains("Next")',
        '.pagination a:contains("Suivant")'
    ]
    
    # Try each selector
    for selector in next_page_selectors:
        if page.locator(selector).count() > 0:
            try:
                page.click(selector)
                return True
            except Exception as e:
                print(f"Failed to click {selector}: {e}")
    
    return False

def scrape_site(url, output_file):
    """Scrape a real estate website with pagination support"""
    print(f"\nStarting scraping of: {url}")
    domain = url.split("//")[1].split("/")[0].replace("www.", "")
    
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
            page.goto(url, wait_until="networkidle")
            
            # Scroll down to load lazy content
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(2)
            
            page_count = 1
            total_properties = 0
            max_pages = 10  # Limit to avoid infinite loops
            
            # Process each page
            while page_count <= max_pages:
                print(f"Processing page {page_count}...")
                
                # Extract property data
                properties = extract_real_estate_data(page)
                print(f"Found {len(properties)} properties on page {page_count}")
                
                # Add metadata to each property
                for prop in properties:
                    prop["source_site"] = domain
                    prop["page_number"] = page_count
                    all_properties.append(prop)
                    total_properties += 1
                
                # Check if there's a next page
                if page_count < max_pages and has_next_page(page):
                    print("Navigating to next page...")
                    if click_next_page(page):
                        page_count += 1
                        # Wait for page to load
                        page.wait_for_load_state("networkidle")
                        # Scroll down to load lazy content
                        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                        time.sleep(random.uniform(2, 4))  # Random delay to avoid detection
                    else:
                        print("Failed to click next page button. Ending pagination.")
                        break
                else:
                    print("No more pages or reached maximum page limit.")
                    break
            
            print(f"Completed scraping of {domain}. Total properties: {total_properties}")
            
        except Exception as e:
            print(f"Error scraping {domain}: {e}")
        finally:
            browser.close()
    
    # Save data to CSV
    with open(output_file, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDNAMES)
        writer.writeheader()
        
        for prop in all_properties:
            # Create a row with all possible fields
            row = {field: "" for field in FIELDNAMES}
            
            # Update with available data
            for key, value in prop.items():
                if key in FIELDNAMES:
                    row[key] = value
                    
            writer.writerow(row)
    
    print(f"Data saved to: {output_file}")
    return all_properties

def main():
    """Main function to scrape all sites"""
    print(f"Starting multi-site scraper at {TIMESTAMP}")
    print(f"Will scrape {len(REAL_ESTATE_SITES)} websites")
    
    all_properties = []
    
    # Create main output file
    main_csv_file = os.path.join(OUTPUT_FOLDER, f"all_properties_{TIMESTAMP}.csv")
    
    # Track progress
    for i, site_url in enumerate(REAL_ESTATE_SITES):
        print(f"\n{'='*50}")
        print(f"Site {i+1}/{len(REAL_ESTATE_SITES)}")
        print(f"{'='*50}")
        
        try:
            # Generate output filename
            domain = site_url.split("//")[1].split("/")[0].replace("www.", "")
            output_file = os.path.join(OUTPUT_FOLDER, f"{domain}_{TIMESTAMP}.csv")
            
            # Scrape the site
            site_properties = scrape_site(site_url, output_file)
            all_properties.extend(site_properties)
            
            # Wait between sites to avoid being blocked
            if i < len(REAL_ESTATE_SITES) - 1:
                delay = random.uniform(10, 15)
                print(f"Waiting {delay:.1f} seconds before next site...")
                time.sleep(delay)
                
        except Exception as e:
            print(f"Error processing site {site_url}: {e}")
    
    # Save all properties to a single CSV file
    with open(main_csv_file, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDNAMES)
        writer.writeheader()
        
        for prop in all_properties:
            # Create a row with all possible fields
            row = {field: "" for field in FIELDNAMES}
            
            # Update with available data
            for key, value in prop.items():
                if key in FIELDNAMES:
                    row[key] = value
                    
            writer.writerow(row)
    
    # Save all properties to a JSON file
    json_file = os.path.join(OUTPUT_FOLDER, f"all_properties_{TIMESTAMP}.json")
    with open(json_file, "w", encoding="utf-8") as file:
        json.dump(all_properties, file, indent=4, ensure_ascii=False)
    
    print(f"\nScraping completed. Total properties collected: {len(all_properties)}")
    print(f"- All properties CSV: {main_csv_file}")
    print(f"- All properties JSON: {json_file}")

if __name__ == "__main__":
    main()
