import os
import re
import csv
import json
import time
import random
import logging
import pandas as pd
import numpy as np
from dotenv import load_dotenv
from datetime import datetime
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("property_scraper.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("TunisianPropertyScraper")

# Load environment variables
load_dotenv()

# Create output folders
RAW_DATA_FOLDER = "real_estate_data/raw"
CLEAN_DATA_FOLDER = "real_estate_data/clean"
SCREENSHOTS_FOLDER = "real_estate_data/screenshots"
HTML_DUMPS_FOLDER = "real_estate_data/html_dumps"

for folder in [RAW_DATA_FOLDER, CLEAN_DATA_FOLDER, SCREENSHOTS_FOLDER, HTML_DUMPS_FOLDER]:
    os.makedirs(folder, exist_ok=True)

# Generate timestamp for this session
TIMESTAMP = datetime.now().strftime('%Y%m%d_%H%M%S')

# Common field names for CSV
FIELDNAMES = [
    "title", "price", "location", "bedrooms", "bathrooms", 
    "area", "land_area", "property_type", "description", "features",
    "image_url", "listing_url", "source_site", "page_number", "region", "raw_price", "raw_area"
]

# Website configurations - comprehensive for Tunisian real estate sites
SITE_CONFIGS = [    {
        "name": "remax.com.tn",
        "base_url": "https://www.remax.com.tn/PublicListingList.aspx",
        "max_pages": 20,
        "property_selectors": [".gallery-item", ".propertyListItem", ".property-item", ".listingGridBox", ".property-container", ".listing-item", ".search-result-item", ".property-card"],
        "pagination_selectors": [".pagination a:has-text('Next')", ".pagination a:has-text('>')", "a.aspNetDisabled + a", "#ctl00_ContentPlaceHolder1_ListViewPager_NextButton", ".pagerLink"],
        "title_selectors": [".gallery-title a", ".proplist_title a", "h3 a", ".listingTitle", ".property-address", ".property-title", ".listing-title"],
        "price_selectors": [".gallery-price-main .proplist_price", ".main-price", ".gallery-price a", ".price", ".property-price", ".listing-price"],
        "location_selectors": [".gallery-title a", ".location", ".property-location", ".address", ".property-address", ".listing-location"],
        "area_selectors": [".gallery-icons span[data-area]", ".property-size", ".surface", ".proplist_area", ".area", ".property-area", ".listing-area"],
        "bedrooms_selectors": [".gallery-icons span[data-bedrooms]", ".property-beds", ".bedrooms", ".beds", ".proplist_beds", ".room-count", ".property-beds", ".listing-beds"],
        "bathrooms_selectors": [".gallery-icons span[data-bathrooms]", ".property-baths", ".bathrooms", ".baths", ".proplist_baths", ".bath-count", ".property-baths", ".listing-baths"],
        "features_selectors": [".features", ".amenities", ".propertyFeatures", ".property-features", ".listing-features"],
        "description_selectors": [".property-description", ".description", ".propertyDescription", ".listing-description"],
        "image_selectors": [".gallery-photo img", ".proplist_img", "img.img-responsive", ".property-image", ".listing-image", ".property-img", ".main-image"],
        "property_type_selectors": [".gallery-transtype span", ".property-type", ".propertyType", ".listing-type", ".property-category"],
        "agent_selectors": [".card-agent .popover-name a", ".agent-name", ".proplist_agent", ".listing-agent", ".property-agent"],
        "detail_url_selectors": [".gallery-title a", ".proplist_title a", "a.LinkImage", ".property-link", ".listing-link", "a.property-url"],
        "hash_url_pagination": True  # Indicates this site uses hash-based URLs for pagination
    },
    {
        "name": "mubawab.tn",
        "base_url": "https://www.mubawab.tn/fr/cc/immobilier-a-vendre-all:ci:74566,74830:sc:house-sale,villa-sale",
        "max_pages": 500,
        "property_selectors": [".listingBox", ".listing-card", ".card-listing"],
        "pagination_selectors": [".pagination a.next", "a.next", "a[rel='next']", ".pagination a:has-text('›')"],
        "title_selectors": [".listingTit", "h3", ".card-title", ".listing-title"],
        "price_selectors": [".priceTag", ".price", ".listing-price"],
        "location_selectors": [".listingH3", ".location", ".listing-location"],
        "area_selectors": [".surfaceArea", ".surface", ".area"],
        "bedrooms_selectors": [".rooms", ".nb-rooms", ".bedrooms", "*:has-text('chambres')"],
        "bathrooms_selectors": [".baths", ".nb-baths", ".bathrooms", "*:has-text('sdb')"],
        "features_selectors": [".features", ".amenities", ".propertyFeatures"]
    },
    {
        "name": "tunisie-annonce.com",
        "base_url": "http://www.tunisie-annonce.com/AnnoncesImmobilier.asp?rech_cod_rub=101&rech_cod_typ=10102",
        "max_pages": 500,
        "property_selectors": [".annonce", "table.tablesorter tr", ".row-annonce"],
        "pagination_selectors": ["a:has-text('Suivant')", "a:has-text('>')", ".pagination a:last-child"],
        "title_selectors": ["h2", ".titre", ".titre-annonce"],
        "price_selectors": [".prix", ".price", "span:has-text('DT')", "span:has-text('TND')"],
        "location_selectors": [".lieu", ".location", ".adresse"],
        "area_selectors": [".surface", "span:has-text('m²')"],
        "bedrooms_selectors": ["span:has-text('chambres')", "span:has-text('pièces')"],
        "bathrooms_selectors": ["span:has-text('sdb')", "span:has-text('salles de bain')"],
        "features_selectors": [".caractere", ".features"]
    },
    {        "name": "menzili.tn",
        "base_url": "https://www.menzili.tn/immo/vente-immobilier-tunisie",
        "max_pages": 500,
        "property_selectors": [".listing-item", ".property-box", ".property"],
        "pagination_selectors": [".pagination a:has-text('Suivant')", ".pagination a:last-child", "a[rel='next']"],
        "title_selectors": ["h4.li-item-hidden a.li-item-list-title", ".title", "h2", ".property-title"],
        "price_selectors": [".price", ".property-price", "span:has-text('DT')", "span:has-text('TND')"],
        "location_selectors": [".location", ".property-location", ".address"],
        "area_selectors": [".surface", ".property-area", "span:has-text('m²')", ".block-opt-1:has-text('Surf habitable')", ".block-opt-1:has-text('Surf terrain')"],
        "bedrooms_selectors": [".rooms", "span:has-text('chambres')", "span:has-text('pièces')"],
        "bathrooms_selectors": [".baths", "span:has-text('sdb')", "span:has-text('salles de bain')"],
        "features_selectors": [".features", ".amenities"],
        "land_area_selectors": [".block-opt-1:has-text('Surf terrain')"]
    },
    {
        "name": "fi-dari.tn",
        "base_url": "https://fi-dari.tn/search?objectif=vendre&usage=Tout+usage&bounds=[[37.649,7.778],[30.107,11.953]]&page=1",
        "max_pages": 500,
        "property_selectors": [".b-annonce-card-body", "a[href^='/bien/']"],
        "pagination_selectors": [".page-item:not(.disabled) .page-link:has-text('Suivant')", "a.page-link:has-text('Suivant')"],
        "title_selectors": [".card-title", "h3"],
        "price_selectors": [".text-primary", "span:has-text('DT')", "span:has-text('Prix')"],
        "location_selectors": [".fa-map-marker+*", "p:last-child", ".location"],
        "area_selectors": [".fa-arrows-alt", "span:has-text('m²')", ".area"],
        "bedrooms_selectors": [".fa-bed", "span:has-text('pièces')", "span:has-text('chambres')"],
        "bathrooms_selectors": [".fa-bath", "span:has-text('sdb')", "span:has-text('salles de bain')"],
        "features_selectors": [".features", ".amenities"]
    },    {        "name": "tecnocasa.tn",
        "base_url": "https://www.tecnocasa.tn/agence/tunisia/",
        "max_pages": 500,
        "property_selectors": [".property-item", ".estate", ".real-estate-item", ".estate-card", ".estates-list > div > a"],
        "pagination_selectors": [".pagination a:has-text('Suivant')", ".pagination a:has-text('>')", ".pagination li:last-child a", ".next a", "a[rel='next']", ".pagination a[href*='/pag-']"],
        "title_selectors": [".estate-card-title", ".property-title", "h3", "h2", ".title"],
        "price_selectors": [".estate-card-current-price", ".estate-card-price", ".property-price", ".price", "span:has-text('DT')", "span:has-text('TND')"],
        "location_selectors": [".estate-card-subtitle", ".property-location", ".location", ".address"],
        "area_selectors": [".property-area", ".area", "span:has-text('m²')"],
        "bedrooms_selectors": [".bedrooms", "span:has-text('chambres')", "span:has-text('pièces')"],
        "bathrooms_selectors": [".bathrooms", "span:has-text('sdb')", "span:has-text('salles de bain')"],
        "features_selectors": [".features", ".amenities", ".characteristics"]
    }
]

# Additional regional Tecnocasa URLs to scrape
TECNOCASA_REGIONS = [
    # Traditional URL format
    "https://www.tecnocasa.tn/agence/tunisia/tunis/",
    "https://www.tecnocasa.tn/agence/tunisia/ariana/",
    "https://www.tecnocasa.tn/agence/tunisia/ben-arous/",
    "https://www.tecnocasa.tn/agence/tunisia/manouba/",
    "https://www.tecnocasa.tn/agence/tunisia/nabeul/",
    "https://www.tecnocasa.tn/agence/tunisia/sousse/",
    "https://www.tecnocasa.tn/agence/tunisia/monastir/",
    "https://www.tecnocasa.tn/agence/tunisia/sfax/",
    # New URL format for regions with HTML extension
    "https://www.tecnocasa.tn/vendre/immeubles/centre-est-ce/sfax.html",
    "https://www.tecnocasa.tn/vendre/immeubles/nord-est-ne/bizerte.html",
    "https://www.tecnocasa.tn/vendre/immeubles/nord-est-ne/cap-bon.html",
    "https://www.tecnocasa.tn/vendre/immeubles/nord-est-ne/grand-tunis.html",
    "https://www.tecnocasa.tn/vendre/immeubles/centre-est-ce/kairouan.html",
    "https://www.tecnocasa.tn/vendre/immeubles/centre-est-ce/monastir.html",
    "https://www.tecnocasa.tn/vendre/immeubles/centre-est-ce/sousse.html",
    "https://www.tecnocasa.tn/vendre/immeubles/sud-est-se/gabes.html",
    "https://www.tecnocasa.tn/vendre/immeubles/sud-est-se/djerba.html",
    "https://www.tecnocasa.tn/vendre/immeubles/sud-est-se/medenine.html"
]

# Helper functions
def clean_text(text):
    """Clean text by removing extra spaces, newlines, etc."""
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def extract_number(text):
    """Extract numeric value from text"""
    if not text:
        return ""
    matches = re.search(r'(\d[\d\s,.\']*)(?:\s*m²|\s*chambres?|\s*pièces?|\s*sdb)?', text.lower())
    if matches:
        num = matches.group(1)
        # Clean and standardize the number format
        num = re.sub(r'[^\d.]', '', num.replace(',', '.'))
        return num
    return ""

def extract_price(text):
    """Extract price value from text with currency (DT, TND, €)"""
    if not text:
        return ""
    # Match price with various currency formats
    matches = re.search(r'(\d[\d\s,.\']*)\s*(?:DT|TND|€|Dinar|Dinars)?', text)
    if matches:
        price = matches.group(1)
        # Clean and standardize the price format
        price = re.sub(r'[^\d.]', '', price.replace(',', '.'))
        return price
    return ""

def extract_area(text):
    """Extract area value in square meters"""
    if not text:
        return ""
    # Match area with various formats
    matches = re.search(r'(\d[\d\s,.\']*)\s*(?:m²|m2|mètres?|metres?)?', text.lower())
    if matches:
        area = matches.group(1)
        # Clean and standardize the area format
        area = re.sub(r'[^\d.]', '', area.replace(',', '.'))
        return area
    return ""

def extract_bedrooms(text):
    """Extract number of bedrooms/rooms"""
    if not text:
        return ""
    # Match bedrooms with various formats
    matches = re.search(r'(\d+)\s*(?:chambres?|pièces?|rooms?|bedrooms?)', text.lower())
    if matches:
        return matches.group(1)
    return ""

def extract_bathrooms(text):
    """Extract number of bathrooms"""
    if not text:
        return ""
    # Match bathrooms with various formats
    matches = re.search(r'(\d+)\s*(?:sdb|salles? de bain|bathrooms?)', text.lower())
    if matches:
        return matches.group(1)
    return ""

def normalize_location(location):
    """Normalize location names in Tunisia"""
    location = location.lower().strip()
    
    # Map of common location spelling variants to standardized names
    location_map = {
        # Tunis region
        "tunis": "Tunis", 
        "grand tunis": "Tunis",
        "le grand tunis": "Tunis",
        # Major cities
        "ariana": "Ariana",
        "l'ariana": "Ariana",
        "ben arous": "Ben Arous",
        "manouba": "Manouba",
        "la manouba": "Manouba",
        "sousse": "Sousse",
        "nabeul": "Nabeul",
        "monastir": "Monastir",
        "sfax": "Sfax",
        "hammamet": "Hammamet",
        # Add more mappings as needed
    }
    
    # Check if location contains a known location
    for key, value in location_map.items():
        if key in location:
            return value
    
    return location.title()  # Return title-cased version if no match

def detect_property_type(title, description=""):
    """Detect property type from title and description"""
    text = (title + " " + description).lower()
    
    if "appartement" in text:
        return "Appartement"
    elif "villa" in text:
        return "Villa"
    elif "maison" in text:
        return "Maison"
    elif "studio" in text:
        return "Studio"
    elif "duplex" in text:
        return "Duplex"
    elif "bureau" in text:
        return "Bureau"
    elif "local" in text:
        return "Local Commercial"
    elif "terrain" in text:
        return "Terrain"
    elif "ferme" in text:
        return "Ferme"
    else:
        return "Autre"

def get_domain_name(url):
    """Extract domain name from URL"""
    parsed_url = urlparse(url)
    domain = parsed_url.netloc
    if domain.startswith('www.'):
        domain = domain[4:]
    return domain

def wait_with_random_delay(min_seconds=2, max_seconds=5):
    """Wait for a random amount of time between min and max seconds"""
    delay = min_seconds + (max_seconds - min_seconds) * random.random()
    logger.info(f"Waiting for {delay:.2f} seconds...")
    time.sleep(delay)

def save_to_csv(data, output_file):
    """Save data to CSV file"""
    if not data:
        logger.warning(f"No data to save to {output_file}")
        return
    
    # Get all field names from all properties
    fieldnames = set()
    for item in data:
        for key in item.keys():
            fieldnames.add(key)
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=sorted(list(fieldnames)))
        writer.writeheader()
        writer.writerows(data)
    
    logger.info(f"Saved {len(data)} items to {output_file}")

def save_to_json(data, output_file):
    """Save data to JSON file with handling for NumPy types"""
    class NumpyEncoder(json.JSONEncoder):
        """Custom encoder for NumPy data types"""
        def default(self, obj):
            if isinstance(obj, (np.integer, np.int64)):
                return int(obj)
            elif isinstance(obj, (np.floating, np.float64)):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            return super(NumpyEncoder, self).default(obj)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, cls=NumpyEncoder)
    logger.info(f"Saved {len(data)} items to {output_file}")

def scrape_remax_site(config, browser, all_properties):
    """
    Specialized scraper for Remax.com.tn with hash-based URL pagination
    
    Args:
        config (dict): Site configuration for Remax
        browser: Playwright browser instance
        all_properties (list): List of all properties collected so far
        
    Returns:
        list: Properties found on Remax.com.tn
    """
    site_name = config["name"]
    base_url = config["base_url"]
    max_pages = config.get("max_pages", 20)
    
    logger.info(f"\n{'='*80}\nStarting specialized scraping of {site_name} at URL: {base_url}\n{'='*80}")
    site_properties = []
    
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
        viewport={"width": 1366, "height": 900}
    )
    
    # Enable request interception
    context.route('**/*', lambda route: route.continue_())
    
    page = context.new_page()
    
    try:
        # Configure longer timeouts for page operations
        page.set_default_timeout(120000)  # 2 minutes
        
        # Navigate to the initial page
        logger.info(f"Navigating to {base_url}")
        page.goto(base_url, wait_until="domcontentloaded")
        wait_with_random_delay(5, 8)
        
        # Get the current URL after initial navigation
        current_url = page.url
        
        # Ensure we have the right hash in the URL for the first page
        try:
            # Try to import the specialized hash pagination function
            try:
                from remax_helper_updated import handle_remax_hash_pagination
                logger.info("Using remax_helper_updated.py for hash pagination")
            except ImportError:
                try:
                    from remax_helper import handle_remax_hash_pagination
                    logger.info("Using remax_helper.py for hash pagination")
                except ImportError:
                    from remax_hash_pagination import handle_remax_hash_pagination
                    logger.info("Using remax_hash_pagination.py")
            
            # If the URL doesn't have a hash, add the default hash for page 1
            if "#" not in current_url:
                hash_url = handle_remax_hash_pagination(base_url, 1)
                logger.info(f"Setting initial hash URL: {hash_url}")
                page.goto(hash_url, wait_until="domcontentloaded")
                wait_with_random_delay(3, 5)
        except ImportError:
            logger.warning("No Remax hash pagination module found, using inline implementation")
            # Inline implementation if modules can't be imported
            if "#" not in current_url:
                # Create default hash URL for page 1
                hash_url = f"{base_url}#mode=gallery&tt=261&cur=TND&sb=MostRecent&page=1&sc=1048"
                logger.info(f"Setting default hash URL: {hash_url}")
                page.goto(hash_url, wait_until="domcontentloaded")
                wait_with_random_delay(3, 5)
        
        # Set up screenshot folder
        domain = get_domain_name(base_url)
        screenshot_folder = os.path.join(SCREENSHOTS_FOLDER, domain)
        os.makedirs(screenshot_folder, exist_ok=True)
        
        # Start scraping pages
        page_count = 1
        
        while page_count <= max_pages:
            logger.info(f"Processing {site_name} page {page_count}")
            
            # Take a screenshot for debugging
            screenshot_path = os.path.join(screenshot_folder, f"page_{page_count}_{TIMESTAMP}.png")
            page.screenshot(path=screenshot_path)
            
            # Save the HTML source for debugging
            html_path = os.path.join(HTML_DUMPS_FOLDER, f"{domain}_page_{page_count}_{TIMESTAMP}.html")
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(page.content())
                
            # Get the current URL with hash
            current_url = page.url
            logger.info(f"Current URL: {current_url}")
              # Extract properties from the current page
            property_elements = page.query_selector_all(".gallery-item, .propertyListItem, .property-item, .listingGridBox, .property-container, .listing-item")
            logger.info(f"Found {len(property_elements)} property elements on page {page_count}")
            
            # Process each property
            for property_item in property_elements:
                try:
                    # Attempt to use specialized Remax property extraction
                    try:
                        try:
                            from remax_helper_updated import extract_remax_property_data
                            logger.info("Using remax_helper_updated.py for property extraction")
                            property_data = extract_remax_property_data(property_item, config, site_name, page_count)
                        except ImportError:
                            from remax_helper import extract_remax_property_data
                            logger.info("Using remax_helper.py for property extraction")
                            property_data = extract_remax_property_data(property_item, config, site_name, page_count)
                    except ImportError:
                        # Fallback to standard extraction
                        logger.warning("No Remax helper modules found, using standard property extraction")
                        property_data = extract_property(property_item, config, site_name, page_count)
                    
                    # Add property to list
                    site_properties.append(property_data)
                    all_properties.append(property_data)
                except Exception as e:
                    logger.error(f"Error extracting property data on {site_name} page {page_count}: {e}")
            
            # Check if we've reached the maximum number of pages
            if page_count >= max_pages:
                logger.info(f"Reached maximum pages ({max_pages})")
                break
            
            # Generate URL for next page using hash-based pagination
            next_page_num = page_count + 1
            try:
                try:
                    from remax_helper_updated import handle_remax_hash_pagination
                    next_url = handle_remax_hash_pagination(current_url, next_page_num)
                except ImportError:
                    try:
                        from remax_helper import handle_remax_hash_pagination
                        next_url = handle_remax_hash_pagination(current_url, next_page_num)
                    except ImportError:
                        from remax_hash_pagination import handle_remax_hash_pagination
                        next_url = handle_remax_hash_pagination(current_url, next_page_num)
            except ImportError:
                # Fallback to inline hash URL generation
                if "#" in current_url:
                    base_url, hash_part = current_url.split('#', 1)
                    
                    # If hash already has page parameter, update it
                    if "page=" in hash_part:
                        parts = []
                        for param in hash_part.split('&'):
                            if param.startswith("page="):
                                parts.append(f"page={next_page_num}")
                            else:
                                parts.append(param)
                        new_hash = '&'.join(parts)
                        next_url = f"{base_url}#{new_hash}"
                    else:
                        # Add page parameter to existing hash
                        next_url = f"{current_url}&page={next_page_num}"
                else:
                    # Create default hash URL
                    next_url = f"{base_url}#mode=gallery&tt=261&cur=TND&sb=MostRecent&page={next_page_num}&sc=1048"
            
            logger.info(f"Navigating to next page: {next_url}")
            
            # Go to next page
            page.goto(next_url, wait_until="domcontentloaded")
            page_count += 1
            
            # Wait for the page to load with random delay to appear more human-like
            wait_with_random_delay(3, 6)
    
    except Exception as e:
        logger.error(f"Error during {site_name} specialized scraping: {e}")
        import traceback
        logger.error(traceback.format_exc())
    
    finally:
        # Close context
        context.close()
    
    logger.info(f"{site_name} specialized scraping completed. Total properties collected: {len(site_properties)}")
    
    # Save the data for this site
    domain = get_domain_name(base_url)
    output_file = os.path.join(RAW_DATA_FOLDER, f"{domain}_{TIMESTAMP}.csv")
    save_to_csv(site_properties, output_file)
    
    # Also save as JSON
    json_output = os.path.join(RAW_DATA_FOLDER, f"{domain}_{TIMESTAMP}.json")
    save_to_json(site_properties, json_output)
    
    # Save data for each page
    page_data_dir = os.path.join(RAW_DATA_FOLDER, f"{domain}_pages_{TIMESTAMP}")
    os.makedirs(page_data_dir, exist_ok=True)
    
    # Group properties by page number
    page_properties = {}
    for prop in site_properties:
        page_num = prop.get("page_number", 0)
        if page_num not in page_properties:
            page_properties[page_num] = []
        page_properties[page_num].append(prop)
    
    # Save each page's data separately
    for page_num, props in page_properties.items():
        page_file = os.path.join(page_data_dir, f"page_{page_num}.json")
        save_to_json(props, page_file)
    
    return site_properties

def extract_property(property_item, site_config, site_name, page_count):
    """
    Basic property extraction for sites without specialized extractors
    
    Args:
        property_item: Playwright element representing a property
        site_config: Configuration for the site
        site_name: Name of the site being scraped
        page_count: Current page number
        
    Returns:
        dict: Property data
    """
    property_data = {
        "source_site": site_name,
        "page_number": page_count
    }
    
    try:
        # Title
        for selector in site_config.get("title_selectors", []):
            title_element = property_item.query_selector(selector)
            if title_element:
                property_data["title"] = title_element.text_content().strip()
                break
        
        # Price
        for selector in site_config.get("price_selectors", []):
            price_element = property_item.query_selector(selector)
            if price_element:
                property_data["price"] = price_element.text_content().strip()
                property_data["raw_price"] = property_data["price"]
                break
        
        # Location
        for selector in site_config.get("location_selectors", []):
            location_element = property_item.query_selector(selector)
            if location_element:
                property_data["location"] = location_element.text_content().strip()
                break
        
        # Area
        for selector in site_config.get("area_selectors", []):
            area_element = property_item.query_selector(selector)
            if area_element:
                property_data["area"] = area_element.text_content().strip()
                property_data["raw_area"] = property_data["area"]
                break
        
        # Bedrooms
        for selector in site_config.get("bedrooms_selectors", []):
            bedrooms_element = property_item.query_selector(selector)
            if bedrooms_element:
                property_data["bedrooms"] = bedrooms_element.text_content().strip()
                break
        
        # Bathrooms
        for selector in site_config.get("bathrooms_selectors", []):
            bathrooms_element = property_item.query_selector(selector)
            if bathrooms_element:
                property_data["bathrooms"] = bathrooms_element.text_content().strip()
                break
        
        # Features
        for selector in site_config.get("features_selectors", []):
            features_element = property_item.query_selector(selector)
            if features_element:
                property_data["features"] = features_element.text_content().strip()
                break
        
        # Image URL
        img_element = property_item.query_selector("img")
        if img_element:
            property_data["image_url"] = img_element.get_attribute("src")
        
        # Listing URL
        url_element = property_item.query_selector("a")
        if url_element:
            property_data["listing_url"] = url_element.get_attribute("href")
        
    except Exception as e:
        logger.error(f"Error extracting basic property data: {e}")
    
    return property_data

def scrape_properties(config, browser, all_properties):
    """
    Standard scraper for most sites that don't require special handling
    
    Args:
        config (dict): Site configuration
        browser: Playwright browser instance
        all_properties (list): List of all properties collected so far
        
    Returns:
        list: Properties found on the site
    """
    site_name = config["name"]
    base_url = config["base_url"]
    max_pages = config.get("max_pages", 20)
    
    logger.info(f"\n{'='*80}\nStarting scraping of {site_name} at URL: {base_url}\n{'='*80}")
    site_properties = []
    
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
        viewport={"width": 1366, "height": 900}
    )
    
    # Enable request interception (useful for some sites with anti-bot measures)
    context.route('**/*', lambda route: route.continue_())
    
    page = context.new_page()
    
    try:
        # Configure longer timeouts for page operations
        page.set_default_timeout(120000)  # 2 minutes
        
        # Navigate to the initial page
        logger.info(f"Navigating to {base_url}")
        page.goto(base_url, wait_until="domcontentloaded")
        wait_with_random_delay(5, 8)
        
        # Set up screenshot folder
        domain = get_domain_name(base_url)
        screenshot_folder = os.path.join(SCREENSHOTS_FOLDER, domain)
        os.makedirs(screenshot_folder, exist_ok=True)
        
        # Start scraping pages
        page_count = 1
        while page_count <= max_pages:
            logger.info(f"Processing {site_name} page {page_count}")
            
            # Take screenshot for debugging
            screenshot_path = os.path.join(screenshot_folder, f"page_{page_count}_{TIMESTAMP}.png")
            page.screenshot(path=screenshot_path)
            
            # Scroll page to ensure all content is loaded
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            wait_with_random_delay(2, 4)
            
            # Extract properties from the current page
            property_selectors = ", ".join(config["property_selectors"])
            property_elements = page.query_selector_all(property_selectors)
            
            logger.info(f"Found {len(property_elements)} property elements on page {page_count}")
            
            # Process each property
            for property_item in property_elements:
                try:
                    # Extract all available property information
                    property_data = extract_property(property_item, config, site_name, page_count)
                    site_properties.append(property_data)
                    all_properties.append(property_data)
                except Exception as e:
                    logger.error(f"Error extracting property data on {site_name} page {page_count}: {e}")
            
            # Save progress for this site
            output_file = os.path.join(RAW_DATA_FOLDER, f"{domain}_{TIMESTAMP}_page{page_count}.csv")
            save_to_csv(site_properties, output_file)
            
            # Check if there's a next page
            if page_count >= max_pages:
                logger.info(f"Reached maximum pages ({max_pages})")
                break
            
            # Look for pagination link
            pagination_selectors = config.get("pagination_selectors", [])
            next_page_found = False
            
            for selector in pagination_selectors:
                next_page_link = page.query_selector(selector)
                if next_page_link:
                    logger.info(f"Found next page link with selector: {selector}")
                    try:
                        next_page_link.click()
                        next_page_found = True
                        logger.info(f"Clicked next page link, waiting for load...")
                        page.wait_for_load_state("domcontentloaded")
                        wait_with_random_delay(5, 8)
                        break
                    except Exception as e:
                        logger.error(f"Error clicking next page link: {e}")
            
            if not next_page_found:
                logger.info(f"No next page link found, stopping at page {page_count}")
                break
            
            page_count += 1
            
    except Exception as e:
        logger.error(f"Error during {site_name} scraping: {e}")
    
    finally:
        # Close context when done
        context.close()
    
    logger.info(f"{site_name} scraping completed. Total properties collected: {len(site_properties)}")
    
    # Save the full data for this site
    full_output_file = os.path.join(RAW_DATA_FOLDER, f"{domain}_{TIMESTAMP}_full.csv")
    save_to_csv(site_properties, full_output_file)
    
    # Also save as JSON
    json_output = os.path.join(RAW_DATA_FOLDER, f"{domain}_{TIMESTAMP}_full.json")
    save_to_json(site_properties, json_output)
    
    return site_properties

def scrape_tecnocasa_regions(browser, all_properties):
    """
    Special handler for Tecnocasa regional websites
    
    Args:
        browser: Playwright browser instance
        all_properties: List of all properties collected so far
        
    Returns:
        list: Properties found on Tecnocasa regional sites
    """
    logger.info(f"Starting Tecnocasa regional scraping...")
    tecnocasa_properties = []
    
    # Create context with appropriate settings
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
        viewport={"width": 1366, "height": 900}
    )
    page = context.new_page()
    
    try:
        for idx, region_url in enumerate(TECNOCASA_REGIONS):
            region_name = region_url.split("/")[-1].replace("-", " ").title()
            logger.info(f"Processing Tecnocasa region {idx+1}/{len(TECNOCASA_REGIONS)}: {region_name}")
            
            # Navigate to region page
            page.goto(region_url, wait_until="domcontentloaded")
            wait_with_random_delay(5, 8)
            
            # Extract properties using selectors from Tecnocasa config
            tecnocasa_config = next((cfg for cfg in SITE_CONFIGS if cfg["name"] == "tecnocasa.tn"), None)
            
            if not tecnocasa_config:
                logger.error("Tecnocasa configuration not found, skipping regions")
                break
            
            # Extract properties from the current region page
            property_selectors = ", ".join(tecnocasa_config["property_selectors"])
            property_elements = page.query_selector_all(property_selectors)
            
            logger.info(f"Found {len(property_elements)} property elements in region: {region_name}")
            
            # Process each property
            region_properties = []
            for property_item in property_elements:
                try:
                    # Extract property data
                    property_data = extract_property(property_item, tecnocasa_config, "tecnocasa.tn", 1)
                    property_data["region"] = region_name
                    region_properties.append(property_data)
                    tecnocasa_properties.append(property_data)
                    all_properties.append(property_data)
                except Exception as e:
                    logger.error(f"Error extracting property data for region {region_name}: {e}")
            
            # Save progress for this region
            region_file = f"tecnocasa_{region_name.lower().replace(' ', '_')}_{TIMESTAMP}.csv"
            output_file = os.path.join(RAW_DATA_FOLDER, region_file)
            save_to_csv(region_properties, output_file)
            
            # Wait between regions to be considerate
            if idx < len(TECNOCASA_REGIONS) - 1:
                wait_time = 30 + random.randint(15, 45)  # 45-75 seconds
                logger.info(f"Waiting {wait_time} seconds before scraping next region...")
                time.sleep(wait_time)
    
    except Exception as e:
        logger.error(f"Error during Tecnocasa regional scraping: {e}")
    
    finally:
        # Close context when done
        context.close()
    
    logger.info(f"Tecnocasa regional scraping completed. Added {len(tecnocasa_properties)} properties")
    
    # Save all Tecnocasa properties
    output_file = os.path.join(RAW_DATA_FOLDER, f"tecnocasa_regions_{TIMESTAMP}.csv")
    save_to_json(tecnocasa_properties, output_file.replace(".csv", ".json"))
    save_to_csv(tecnocasa_properties, output_file)
    
    return tecnocasa_properties

def clean_data(input_file):
    """
    Clean and normalize property data
    
    Args:
        input_file (str): Path to input CSV file
        
    Returns:
        tuple: (cleaned DataFrame, statistics dictionary)
    """
    logger.info(f"Cleaning and normalizing data from {input_file}")
    
    try:
        # Read the raw data
        df = pd.read_csv(input_file, encoding='utf-8')
        logger.info(f"Read {len(df)} properties from {input_file}")
        
        # Statistics before cleaning
        stats = {
            "total_raw": len(df),
            "missing_price": df["price"].isna().sum(),
            "missing_location": df["location"].isna().sum(),
            "missing_area": df["area"].isna().sum(),
            "sites": df["source_site"].value_counts().to_dict()
        }
        
        # Basic cleaning
        # 1. Remove rows with missing essential data
        df_filtered = df.dropna(subset=["price", "location"], how="any")
        stats["removed_missing_essential"] = len(df) - len(df_filtered)
        
        # 2. Extract numeric values from price and area
        def extract_numeric(value):
            if pd.isna(value):
                return np.nan
            numeric_part = re.sub(r'[^\d.]', '', str(value).replace(',', '.'))
            try:
                return float(numeric_part) if numeric_part else np.nan
            except:
                return np.nan
        
        # Apply numeric extraction 
        df_filtered["price_numeric"] = df_filtered["raw_price"].apply(extract_numeric)
        df_filtered["area_numeric"] = df_filtered["raw_area"].apply(extract_numeric)
        
        # 3. Remove outliers
        price_q1 = df_filtered["price_numeric"].quantile(0.25)
        price_q3 = df_filtered["price_numeric"].quantile(0.75)
        price_iqr = price_q3 - price_q1
        
        area_q1 = df_filtered["area_numeric"].quantile(0.25)
        area_q3 = df_filtered["area_numeric"].quantile(0.75)
        area_iqr = area_q3 - area_q1
        
        df_clean = df_filtered[
            (df_filtered["price_numeric"] >= price_q1 - 3 * price_iqr) &
            (df_filtered["price_numeric"] <= price_q3 + 3 * price_iqr) &
            (df_filtered["area_numeric"] >= area_q1 - 3 * area_iqr) &
            (df_filtered["area_numeric"] <= area_q3 + 3 * area_iqr)
        ]
        
        stats["removed_outliers"] = len(df_filtered) - len(df_clean)
        stats["total_clean"] = len(df_clean)
        
        logger.info(f"Cleaned data. Started with {stats['total_raw']}, ended with {stats['total_clean']} properties")
        
        # Save the cleaned data
        output_file = os.path.join(CLEAN_DATA_FOLDER, f"all_properties_clean_{TIMESTAMP}.csv")
        df_clean.to_csv(output_file, index=False, encoding='utf-8')
        
        logger.info(f"Saved cleaned data to {output_file}")
        
        return df_clean, stats
    
    except Exception as e:
        logger.error(f"Error cleaning data: {e}")
        return pd.DataFrame(), {"error": str(e)}

def main():
    """Main function to scrape all Tunisian real estate websites"""
    start_time = datetime.now()
    logger.info(f"Starting Tunisian property scraper at {start_time}")
    all_properties = []
    
    with sync_playwright() as playwright:
        # Set up browser with slow_mo for stability in case of complex pages
        browser = playwright.chromium.launch(
            headless=False,  # Set to True for production
            args=[
                '--disable-dev-shm-usage',
                '--disable-features=site-per-process',
                '--disable-web-security',
                '--no-sandbox',
                '--window-size=1920,1080',  # Set window size
                '--start-maximized',
                '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
            ],
            slow_mo=100,  # Add a small delay between actions for stability
            timeout=180000  # 3 minutes timeout for browser operations
        )
        
        try:            # Process each website in sequence
            for config in SITE_CONFIGS:
                site_name = config["name"]
                logger.info(f"\n\n{'*'*80}\nScraping website: {site_name}\n{'*'*80}")
                
                # Scrape the current site
                if site_name == "remax.com.tn":
                    try:
                        # First, attempt to use the specialized Remax scraper function
                        site_properties = scrape_remax_site(config, browser, all_properties)
                    except Exception as e:
                        logger.error(f"Error using specialized Remax scraper: {e}. Falling back to standard scraper.")
                        # Fallback to standard scraper if specialized one fails
                        site_properties = scrape_properties(config, browser, all_properties)
                else:
                    site_properties = scrape_properties(config, browser, all_properties)
                
                # Log progress
                logger.info(f"Finished scraping {site_name}. Got {len(site_properties)} properties.")
                logger.info(f"Running total: {len(all_properties)} properties collected so far")
                
                # Save all properties collected so far
                all_csv = os.path.join(RAW_DATA_FOLDER, f"all_properties_{TIMESTAMP}.csv")
                all_json = os.path.join(RAW_DATA_FOLDER, f"all_properties_{TIMESTAMP}.json")
                
                save_to_csv(all_properties, all_csv)
                save_to_json(all_properties, all_json)
                
                logger.info(f"Updated combined data files with {len(all_properties)} total properties")
                
                # Wait between sites to be considerate
                if config != SITE_CONFIGS[-1]:  # If not the last site
                    wait_time = 60 + random.randint(30, 90)  # 1.5-2.5 minutes
                    logger.info(f"Waiting {wait_time} seconds before scraping next site...")
                    time.sleep(wait_time)
            
            # Scrape Tecnocasa regional sites 
            logger.info("\n\nStarting specialized scraping for Tecnocasa regional websites...")
            tecnocasa_properties = scrape_tecnocasa_regions(browser, all_properties)
            logger.info(f"Added {len(tecnocasa_properties)} properties from Tecnocasa regions")
            
            # Final save of raw data
            final_raw_csv = os.path.join(RAW_DATA_FOLDER, f"all_properties_raw_{TIMESTAMP}.csv")
            final_raw_json = os.path.join(RAW_DATA_FOLDER, f"all_properties_raw_{TIMESTAMP}.json")
            
            save_to_csv(all_properties, final_raw_csv)
            save_to_json(all_properties, final_raw_json)
            
            logger.info(f"Saved all {len(all_properties)} raw properties")
        
        finally:
            # Close browser
            browser.close()
    
    # Clean and process the data
    logger.info("\n\nStarting data cleaning and processing...")
    clean_df, stats = clean_data(os.path.join(RAW_DATA_FOLDER, f"all_properties_raw_{TIMESTAMP}.csv"))
    
    if clean_df is not None:
        # Save cleaned data        clean_csv = os.path.join(CLEAN_DATA_FOLDER, f"all_properties_clean_{TIMESTAMP}.csv")
        clean_json = os.path.join(CLEAN_DATA_FOLDER, f"all_properties_clean_{TIMESTAMP}.json")
        
        clean_df.to_csv(clean_csv, index=False, encoding='utf-8')
        
        # Convert DataFrame to a list of dictionaries with Python native types
        records = clean_df.to_dict(orient='records')
        # Use our custom save_to_json function that handles NumPy types
        save_to_json(records, clean_json)
        
        logger.info(f"Saved {len(clean_df)} cleaned properties to {clean_csv}")
          # Save statistics
        stats_file = os.path.join(CLEAN_DATA_FOLDER, f"data_cleaning_stats_{TIMESTAMP}.json")
        save_to_json(stats, stats_file)
        
        logger.info(f"Saved data cleaning statistics to {stats_file}")
    
    # Calculate and log statistics
    end_time = datetime.now()
    duration = end_time - start_time
    logger.info(f"\n\n{'='*80}")
    logger.info(f"Scraping completed at {end_time}")
    logger.info(f"Total duration: {duration}")
    logger.info(f"Total raw properties collected: {len(all_properties)}")
    if clean_df is not None:
        logger.info(f"Total cleaned properties: {len(clean_df)}")
    logger.info(f"Raw data saved to folder: {RAW_DATA_FOLDER}")
    logger.info(f"Cleaned data saved to folder: {CLEAN_DATA_FOLDER}")
    logger.info(f"Main Raw CSV file: all_properties_raw_{TIMESTAMP}.csv")
    logger.info(f"Main Clean CSV file: all_properties_clean_{TIMESTAMP}.csv")
    logger.info(f"{'='*80}\n")
    
    return len(all_properties)

if __name__ == "__main__":
    properties_count = main()
    print(f"\nScraping complete! Collected {properties_count} raw properties.")
