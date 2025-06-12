from scrapegraphai import SmartScraperGraph
from dotenv import load_dotenv
import os
import json
import pandas as pd
from datetime import datetime
import time
import random

def scrape_site(url, query=None, delay=2):
    """Scrape a single site using ScrapegraphAI
    
    Args:
        url (str): The URL to scrape
        query (str, optional): Custom query to use. Defaults to None.
        delay (int, optional): Delay between requests to avoid rate limiting. Defaults to 2.
    
    Returns:
        dict: The scraped data
    """
    load_dotenv()
    
    if query is None:
        query = """Extract all real estate listings with the following information:
        - Property type (apartment, villa, house, etc.)
        - Price
        - Location/Address
        - Number of bedrooms
        - Number of bathrooms
        - Property area (sqm)
        - Additional features or amenities
        - Contact information (if available)
        - URL of the listing (if available)
        """
    
    # Configuration for SmartScraperGraph
    graph_config = {
        "openai_api_key": os.getenv("OPENAI_APIKEY"),
        "model": "gpt-4o",  # Using the more capable model for better extraction
    }
    
    print(f"Scraping: {url}")
    
    try:
        # Create an instance of SmartScraperGraph
        smart_scraper_graph = SmartScraperGraph(
            prompt=query,
            source=url,
            config=graph_config
        )
        
        # Run the scraper and extract data
        result = smart_scraper_graph.run()
        
        # Add source URL to the result
        if isinstance(result, dict):
            result["source_url"] = url
        
        # Wait to avoid overwhelming the server
        time.sleep(delay + random.uniform(1, 3))
        
        return result
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return {"error": str(e), "source_url": url}

def save_results(results, timestamp=None):
    """Save results to JSON and CSV files
    
    Args:
        results (list): List of scraped data dictionaries
        timestamp (str, optional): Timestamp to use in filenames. Defaults to None.
    """
    if timestamp is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Ensure the output folder exists
    os.makedirs('output', exist_ok=True)
    
    # Save raw JSON data
    json_path = os.path.join('output', f'real_estate_data_{timestamp}.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=4, ensure_ascii=False)
    
    print(f"Raw data saved to {json_path}")
    
    # Try to convert to DataFrame and save as CSV
    try:
        # Flatten nested results if necessary
        flat_results = []
        for result in results:
            if "listings" in result:
                for listing in result["listings"]:
                    listing["source_url"] = result.get("source_url", "")
                    flat_results.append(listing)
            else:
                flat_results.append(result)
        
        # Convert to DataFrame
        df = pd.DataFrame(flat_results)
        
        # Save to CSV
        csv_path = os.path.join('output', f'real_estate_data_{timestamp}.csv')
        df.to_csv(csv_path, index=False)
        print(f"Structured data saved to {csv_path}")
    except Exception as e:
        print(f"Could not convert to CSV: {e}")

def main():
    # List of Tunisian real estate sites to scrape
    sites = [
        "https://www.tecnocasa.tn/vendre/immeubles/nord-est-ne/cap-bon/kelibia.html",
        "https://www.mubawab.tn/fr/ct/tunis/immobilier-a-vendre",
        "https://www.mubawab.tn/fr/cc/immobilier-a-vendre-all:ci:74566,74830:sc:house-sale,villa-sale",
        "https://www.menzili.tn/immo/vente-immobilier-tunisie",
        "http://www.tunisie-annonce.com/AnnoncesImmobilier.asp?rech_cod_rub=101&rech_cod_typ=10102",
        "https://www.darcomtunisia.com/search?property_types%5B%5D=1&vocations%5B%5D=1&vocations%5B%5D=2&reference=&surface_terrain_min=&prix_max=",
        "https://fi-dari.tn/search?objectif=vendre&usage=Tout+usage&bounds=[[37.649,7.778],[30.107,11.953]]&page=1"
    ]
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    results = []
    
    print(f"Starting scraping job at {timestamp}")
    print(f"Total sites to scrape: {len(sites)}")
    
    for i, url in enumerate(sites):
        print(f"\n--- Processing site {i+1}/{len(sites)} ---")
        result = scrape_site(url)
        results.append(result)
        
        # Save interim results every 3 sites or at the end
        if (i+1) % 3 == 0 or i == len(sites) - 1:
            save_results(results, timestamp)
    
    print("\nScraping job completed!")

if __name__ == "__main__":
    main()
