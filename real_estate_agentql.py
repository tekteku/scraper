from dotenv import load_dotenv
import agentql
import csv
import os
from datetime import datetime
import time

# Load environment variables
load_dotenv()

# Define the GraphQL query for real estate listings
REAL_ESTATE_LISTINGS = """
{
    results {
        properties[] {
            property_name
            property_price
            property_location
            bedrooms
            bathrooms
            area_sqm
            property_type
            listing_date
            image_url
            property_url
            features
        }
    }
}
"""

# Define pagination query
NEXT_PAGE_BTN = """
{
    next_page_button_enabled
    next_page_button_disabled
}
"""

def scrape_real_estate_site(url, output_file):
    """Scrape a real estate website with pagination support"""
    print(f"Starting scraping of: {url}")
    
    # Start a new AgentQL session
    session = agentql.start_session(url)
    
    # Scroll to bottom to ensure all content is loaded
    session.driver.scroll_to_bottom()
    time.sleep(2)  # Wait for content to load
    
    # Check for pagination
    pagination = session.query(NEXT_PAGE_BTN)
    print("Pagination detected")
    
    # Open CSV file for writing
    with open(output_file, "w", newline="", encoding="utf-8") as file:
        fieldnames = [
            "property_name", "property_price", "property_location", 
            "bedrooms", "bathrooms", "area_sqm", "property_type", 
            "listing_date", "image_url", "property_url", "features",
            "page_number"
        ]
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        
        # Display pagination status
        enabled = pagination.to_data().get('next_page_button_enabled')
        disabled = pagination.to_data().get('next_page_button_disabled')
        print(f"Next page button enabled: {enabled}")
        print(f"Next page button disabled: {disabled}")
        
        page_count = 1
        total_properties = 0
        
        # Loop through pages as long as there is a next page button available
        while True:
            print(f"Processing page {page_count}...")
            
            # Query the current page for property listings
            properties = session.query(REAL_ESTATE_LISTINGS)
            print(f"Retrieved page {page_count} data")
            
            # Get the property data
            try:
                property_data = properties.to_data().get('results', {}).get('properties', [])
                print(f"Found {len(property_data)} properties on this page")
                
                # Write each property to the CSV
                for prop in property_data:
                    # Add the page number
                    prop['page_number'] = page_count
                    # Write to CSV, only including fields that are in fieldnames
                    row = {field: prop.get(field, "") for field in fieldnames}
                    writer.writerow(row)
                    total_properties += 1
                
                print(f"Data from page {page_count} written to CSV")
            except Exception as e:
                print(f"Error processing properties on page {page_count}: {e}")
            
            # Check if there is a next page
            try:
                # Re-check pagination status
                pagination = session.query(NEXT_PAGE_BTN)
                enabled = pagination.to_data().get('next_page_button_enabled')
                disabled = pagination.to_data().get('next_page_button_disabled')
                
                if enabled and not disabled:
                    # Click the next page button
                    print("Navigating to next page...")
                    # This selector needs to be adjusted based on the specific website
                    session.driver.click_element(".next-page, .pagination-next, a.next, li.next a")
                    page_count += 1
                    
                    # Wait for the next page to load
                    time.sleep(3)
                    session.driver.scroll_to_bottom()
                    time.sleep(1)
                    
                    # Safety break - stop after 20 pages
                    if page_count > 20:
                        print("Reached maximum page limit (20). Stopping pagination.")
                        break
                else:
                    print("No more pages available. Ending pagination.")
                    break
            except Exception as e:
                print(f"Error navigating to next page: {e}")
                break
    
    # Close the session
    session.close()
    print(f"Scraping completed. Total properties collected: {total_properties}")
    return total_properties

def main():
    # Create output directory
    output_dir = "real_estate_data"
    os.makedirs(output_dir, exist_ok=True)
    
    # List of real estate websites to scrape
    websites = [
        "https://www.tecnocasa.tn/vendre/immeubles/nord-est-ne/cap-bon/kelibia.html?view=37.04021914770574,11.318932847702001,36.719188488461185,10.800682616690665&zoom=9.95",
        "https://www.mubawab.tn/fr/ct/tunis/immobilier-a-vendre",
        "https://www.mubawab.tn/fr/cc/immobilier-a-vendre-all:ci:74566,74830:sc:house-sale,villa-sale",
        "https://www.menzili.tn/immo/vente-immobilier-tunisie",
        "http://www.tunisie-annonce.com/AnnoncesImmobilier.asp?rech_cod_rub=101&rech_cod_typ=10102",
        "https://www.darcomtunisia.com/search?property_types%5B%5D=1&vocations%5B%5D=1&vocations%5B%5D=2&reference=&surface_terrain_min=&prix_max=",
        "https://fi-dari.tn/search?objectif=vendre&usage=Tout+usage&bounds=[[37.649,7.778],[30.107,11.953]]&page=1"
    ]
    
    # Generate timestamp for this scraping session
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Process each website
    total_properties = 0
    for i, url in enumerate(websites):
        try:
            # Extract domain for filename
            domain = url.split("//")[1].split("/")[0].replace("www.", "")
            output_file = os.path.join(output_dir, f"{domain}_{timestamp}.csv")
            
            print(f"\n{'='*50}")
            print(f"Processing site {i+1}/{len(websites)}: {domain}")
            print(f"{'='*50}")
            
            # Scrape the website
            site_properties = scrape_real_estate_site(url, output_file)
            total_properties += site_properties
            
            # Wait between sites to avoid being blocked
            if i < len(websites) - 1:
                delay = 10  # seconds
                print(f"\nWaiting {delay} seconds before next site...")
                time.sleep(delay)
                
        except Exception as e:
            print(f"Error processing site {url}: {e}")
    
    print(f"\nAll scraping completed. Total properties collected across all sites: {total_properties}")

if __name__ == "__main__":
    main()
