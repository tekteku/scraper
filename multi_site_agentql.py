from dotenv import load_dotenv
import agentql
import csv
import json
import os
import time
from datetime import datetime
import random

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

# Define GraphQL queries for different websites
# These will need to be customized for each website based on its structure
TECNOCASA_QUERY = """
{
    results {
        properties[] {
            title
            price
            location
            bedrooms
            bathrooms
            area
            property_type
            listing_date
            image_url
            listing_url
            description
            features
            agent_info
        }
    }
}
"""

MUBAWAB_QUERY = """
{
    results {
        listings[] {
            title
            price
            location
            bedrooms
            bathrooms
            area
            property_type
            listing_date
            image_url
            listing_url
            description
            features
            agent_info
        }
    }
}
"""

MENZILI_QUERY = """
{
    results {
        properties[] {
            title
            price
            location
            bedrooms
            bathrooms
            area
            property_type
            listing_date
            image_url
            listing_url
            description
            features
            agent_info
        }
    }
}
"""

TUNISIE_ANNONCE_QUERY = """
{
    results {
        annonces[] {
            title
            price
            location
            bedrooms
            bathrooms
            area
            property_type
            listing_date
            image_url
            listing_url
            description
            features
            agent_info
        }
    }
}
"""

DARCOM_QUERY = """
{
    results {
        properties[] {
            title
            price
            location
            bedrooms
            bathrooms
            area
            property_type
            listing_date
            image_url
            listing_url
            description
            features
            agent_info
        }
    }
}
"""

FIDARI_QUERY = """
{
    results {
        listings[] {
            title
            price
            location
            bedrooms
            bathrooms
            area
            property_type
            listing_date
            image_url
            listing_url
            description
            features
            agent_info
        }
    }
}
"""

# Map websites to their queries
SITE_QUERIES = {
    "tecnocasa.tn": TECNOCASA_QUERY,
    "mubawab.tn": MUBAWAB_QUERY,
    "menzili.tn": MENZILI_QUERY,
    "tunisie-annonce.com": TUNISIE_ANNONCE_QUERY,
    "darcomtunisia.com": DARCOM_QUERY,
    "fi-dari.tn": FIDARI_QUERY
}

# Define pagination query - this may need to be customized per site
NEXT_PAGE_BTN = """
{
    next_page_button_enabled
    next_page_button_disabled
}
"""

# Create output folder if it doesn't exist
OUTPUT_FOLDER = "scraped_data"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Generate timestamp for this scraping session
TIMESTAMP = datetime.now().strftime('%Y%m%d_%H%M%S')

# CSV field names - common structure for all sites
FIELDNAMES = [
    "title", "price", "location", "bedrooms", "bathrooms", 
    "area", "property_type", "listing_date", "image_url", 
    "listing_url", "description", "features", "agent_info", 
    "source_site"
]

def get_domain(url):
    """Extract domain from URL for identifying which query to use"""
    for domain in SITE_QUERIES.keys():
        if domain in url:
            return domain
    return "unknown"

def scrape_site(site_url):
    """Scrape a single real estate website using AgentQL"""
    domain = get_domain(site_url)
    query = SITE_QUERIES.get(domain, TECNOCASA_QUERY)  # Default to Tecnocasa query if unknown
    
    print(f"\n{'='*50}")
    print(f"Scraping site: {site_url}")
    print(f"Using query template for domain: {domain}")
    print(f"{'='*50}\n")
    
    # Start a new session
    session = agentql.start_session(site_url)
    
    # Scroll to the bottom to load all content
    session.driver.scroll_to_bottom()
    time.sleep(2)  # Wait for content to load
    
    # Check if pagination exists
    try:
        pagination = session.query(NEXT_PAGE_BTN)
        has_pagination = pagination.to_data().get('next_page_button_enabled', False)
        print(f"Pagination detected: {has_pagination}")
    except Exception as e:
        print(f"Error checking pagination: {e}")
        has_pagination = False
    
    all_results = []
    page_count = 1
    
    try:
        # Process first page
        print(f"Processing page {page_count}...")
        results = session.query(query)
        page_data = process_results(results.to_data(), domain)
        all_results.extend(page_data)
        print(f"Found {len(page_data)} listings on page {page_count}")
        
        # If pagination exists, process additional pages
        while has_pagination:
            try:
                # Try to click next page button
                print("Attempting to navigate to next page...")
                session.driver.click_element(".next-page-button, .pagination-next, a.next, li.next a")
                
                # Wait for new page to load
                time.sleep(random.uniform(3, 5))
                session.driver.scroll_to_bottom()
                time.sleep(1)
                
                # Re-check pagination status
                pagination = session.query(NEXT_PAGE_BTN)
                has_pagination = pagination.to_data().get('next_page_button_enabled', False) and not pagination.to_data().get('next_page_button_disabled', False)
                
                # Scrape current page
                page_count += 1
                print(f"Processing page {page_count}...")
                results = session.query(query)
                page_data = process_results(results.to_data(), domain)
                all_results.extend(page_data)
                print(f"Found {len(page_data)} listings on page {page_count}")
                
                # Safety break - stop after 20 pages to avoid infinite loops
                if page_count >= 20:
                    print("Reached maximum page limit (20). Stopping pagination.")
                    break
                    
            except Exception as e:
                print(f"Error navigating to next page: {e}")
                print("Ending pagination")
                break
                
    except Exception as e:
        print(f"Error scraping site: {e}")
    finally:
        # Close the session
        session.close()
        
    print(f"Total listings collected from {domain}: {len(all_results)}")
    return all_results

def process_results(data, domain):
    """Process and normalize the results data based on the site structure"""
    processed_results = []
    
    try:
        # Extract result list based on domain/structure
        if domain == "tecnocasa.tn":
            items = data.get('results', {}).get('properties', [])
        elif domain == "mubawab.tn":
            items = data.get('results', {}).get('listings', [])
        elif domain == "menzili.tn":
            items = data.get('results', {}).get('properties', [])
        elif domain == "tunisie-annonce.com":
            items = data.get('results', {}).get('annonces', [])
        elif domain == "darcomtunisia.com":
            items = data.get('results', {}).get('properties', [])
        elif domain == "fi-dari.tn":
            items = data.get('results', {}).get('listings', [])
        else:
            # Default extraction attempt
            results = data.get('results', {})
            for key in results:
                if isinstance(results[key], list):
                    items = results[key]
                    break
            else:
                items = []
        
        # Process each item
        for item in items:
            # Add source site information
            item['source_site'] = domain
            processed_results.append(item)
            
    except Exception as e:
        print(f"Error processing results for {domain}: {e}")
    
    return processed_results

def save_to_csv(data, filename):
    """Save the scraped data to a CSV file"""
    file_path = os.path.join(OUTPUT_FOLDER, filename)
    with open(file_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDNAMES)
        writer.writeheader()
        
        for item in data:
            # Create a row with all possible fields
            row = {field: "" for field in FIELDNAMES}
            
            # Update with available data
            for key, value in item.items():
                if key in FIELDNAMES:
                    if isinstance(value, (dict, list)):
                        row[key] = json.dumps(value, ensure_ascii=False)
                    else:
                        row[key] = value
                        
            writer.writerow(row)
    
    print(f"Data saved to CSV: {file_path}")
    return file_path

def save_to_json(data, filename):
    """Save the scraped data to a JSON file"""
    file_path = os.path.join(OUTPUT_FOLDER, filename)
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)
    
    print(f"Data saved to JSON: {file_path}")
    return file_path

def main():
    """Main function to scrape all sites"""
    print(f"Starting multi-site scraper at {TIMESTAMP}")
    print(f"Will scrape {len(REAL_ESTATE_SITES)} websites")
    
    all_listings = []
    
    # Track progress
    for i, site_url in enumerate(REAL_ESTATE_SITES):
        print(f"\nSite {i+1}/{len(REAL_ESTATE_SITES)}: {site_url}")
        
        try:
            # Scrape the site
            site_listings = scrape_site(site_url)
            all_listings.extend(site_listings)
            
            # Save intermediate results every 3 sites
            if (i + 1) % 3 == 0 or i == len(REAL_ESTATE_SITES) - 1:
                print(f"\nSaving intermediate results ({len(all_listings)} listings so far)...")
                save_to_json(all_listings, f"real_estate_listings_intermediate_{TIMESTAMP}.json")
            
            # Random delay between sites to avoid being blocked
            if i < len(REAL_ESTATE_SITES) - 1:
                delay = random.uniform(10, 20)
                print(f"Waiting {delay:.1f} seconds before next site...")
                time.sleep(delay)
                
        except Exception as e:
            print(f"Error scraping site {site_url}: {e}")
    
    # Save final results
    print(f"\nScraping completed. Total listings collected: {len(all_listings)}")
    
    json_path = save_to_json(all_listings, f"real_estate_listings_{TIMESTAMP}.json")
    csv_path = save_to_csv(all_listings, f"real_estate_listings_{TIMESTAMP}.csv")
    
    print(f"\nScraping session completed. Files saved:")
    print(f"- JSON: {json_path}")
    print(f"- CSV: {csv_path}")

if __name__ == "__main__":
    main()
