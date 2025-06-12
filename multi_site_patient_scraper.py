import os
import re
import csv
import json
import time
import random
import logging
from dotenv import load_dotenv
from datetime import datetime
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("scraper.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("PropertyScraper")

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

# Website URLs to scrape - Each with specific configurations
SITE_CONFIGS = [
    {
        "name": "mubawab.tn",
        "base_url": "https://www.mubawab.tn/fr/cc/immobilier-a-vendre-all:ci:74566,74830:sc:house-sale,villa-sale",
        "max_pages": 500,
        "property_selectors": [".listingBox", ".listing-card", ".card-listing"],
        "pagination_selectors": [".pagination a.next", "a.next", "a[rel='next']", ".pagination a:has-text('›')"],
        "title_selectors": [".listingTit", "h3", ".card-title", ".listing-title"],
        "price_selectors": [".priceTag", ".price", ".listing-price"],
        "location_selectors": [".listingH3", ".location", ".listing-location"],
        "area_selectors": [".surfaceArea", ".surface", ".area"]
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
        "area_selectors": [".surface", "span:has-text('m²')"]
    },
    {
        "name": "menzili.tn",
        "base_url": "https://www.menzili.tn/immo/vente-immobilier-tunisie",
        "max_pages": 500,
        "property_selectors": [".listing-item", ".property-box", ".property"],
        "pagination_selectors": [".pagination a:has-text('Suivant')", ".pagination a:last-child", "a[rel='next']"],
        "title_selectors": [".title", "h2", ".property-title"],
        "price_selectors": [".price", ".property-price", "span:has-text('DT')", "span:has-text('TND')"],
        "location_selectors": [".location", ".property-location", ".address"],
        "area_selectors": [".surface", ".property-area", "span:has-text('m²')"]
    }
]

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

def get_domain_name(url):
    """Extract domain name from URL"""
    parsed_url = urlparse(url)
    domain = parsed_url.netloc
    if domain.startswith('www.'):
        domain = domain[4:]
    return domain

def wait_with_random_delay(min_seconds=3, max_seconds=8):
    """Wait for a random time between min and max seconds to appear more human-like"""
    delay = min_seconds + random.random() * (max_seconds - min_seconds)
    logger.info(f"Waiting for {delay:.2f} seconds...")
    time.sleep(delay)

def save_to_csv(data, filename):
    """Save data to CSV file"""
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=FIELDNAMES)
            writer.writeheader()
            for item in data:
                writer.writerow(item)
        return True
    except Exception as e:
        logger.error(f"Error saving to CSV {filename}: {str(e)}")
        return False

def save_to_json(data, filename):
    """Save data to JSON file"""
    try:
        with open(filename, 'w', encoding='utf-8') as jsonfile:
            json.dump(data, jsonfile, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        logger.error(f"Error saving to JSON {filename}: {str(e)}")
        return False

def scrape_properties(config, browser, all_properties):
    """Scrape properties from a website based on its configuration"""
    site_name = config["name"]
    base_url = config["base_url"]
    max_pages = config["max_pages"]
    
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
        
        # Navigate to the URL with retry mechanism
        logger.info(f"Loading initial page for {site_name}...")
        max_page_load_attempts = 5
        page_loaded = False
        
        for attempt in range(max_page_load_attempts):
            try:
                logger.info(f"Navigation attempt {attempt+1} for {site_name}")
                page.goto(base_url, timeout=180000, wait_until="domcontentloaded")
                
                logger.info(f"DOM content loaded for {site_name}, waiting for visibility of key elements...")
                # Wait for any of these selectors to appear (indicating page is somewhat loaded)
                selectors = ["img", "a", "div", "span", "h1", "h2", "h3", ".container", ".wrapper"]
                for selector in selectors:
                    try:
                        page.wait_for_selector(selector, timeout=30000, state="visible")
                        logger.info(f"Found visible element with selector: {selector}")
                        break
                    except Exception:
                        continue
                
                # Try to wait for network idle but don't fail if it times out
                try:
                    logger.info("Waiting for network to become idle...")
                    page.wait_for_load_state("networkidle", timeout=45000)
                    logger.info("Network is idle")
                except Exception:
                    logger.warning("Network not idle, but continuing anyway...")
                
                page_loaded = True
                logger.info(f"Page considered loaded on attempt {attempt+1}")
                break
            except Exception as e:
                logger.error(f"Error loading {site_name} on attempt {attempt+1}: {str(e)}")
                if attempt < max_page_load_attempts - 1:
                    logger.info(f"Waiting 45 seconds before retry...")
                    time.sleep(45)  # Longer wait between retries
                    
                    # Try to reset browser context if we're having persistent issues
                    if attempt == 1:
                        try:
                            logger.info("Trying to reset browser context...")
                            context.close()
                            context = browser.new_context(
                                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
                                viewport={"width": 1366, "height": 900}
                            )
                            page = context.new_page()
                            page.set_default_timeout(120000)
                        except Exception:
                            logger.error("Failed to reset context, continuing with current one...")
                else:
                    logger.warning(f"Failed to load {site_name} after {max_page_load_attempts} attempts, but will try to continue with partial content")
        
        if not page_loaded:
            logger.error(f"Unable to load {site_name} after multiple attempts. Skipping this site.")
            context.close()
            return []
        
        # Wait longer for the page to fully render
        logger.info(f"Waiting for {site_name} to fully initialize...")
        time.sleep(12)
        
        # Take a screenshot for debugging
        screenshot_file = f"{site_name}_homepage.png"
        page.screenshot(path=os.path.join(OUTPUT_FOLDER, screenshot_file))
        logger.info(f"Saved screenshot to {screenshot_file}")
        
        # Scroll down to load lazy content with multiple scrolls
        logger.info("Scrolling to load more content...")
        for scroll in range(5):  # Increased number of scrolls
            logger.info(f"Scroll {scroll+1}/5")
            page.evaluate(f"window.scrollTo(0, {(scroll+1) * 1200})")
            time.sleep(4)  # Wait between scrolls
        
        page.evaluate("window.scrollTo(0, 0)")  # Back to top
        time.sleep(5)
        
        page_count = 1
        
        # Process each page
        while page_count <= max_pages:
            logger.info(f"Processing {site_name} page {page_count}...")
            
            # Take a screenshot for debugging
            screenshot_file = f"{site_name}_page{page_count}.png"
            page.screenshot(path=os.path.join(OUTPUT_FOLDER, screenshot_file))
            
            # Save HTML for debugging
            html_file = os.path.join(OUTPUT_FOLDER, f"{site_name}_page{page_count}.html")
            with open(html_file, "w", encoding="utf-8") as f:
                f.write(page.content())
            
            # Get property items
            property_selectors = config["property_selectors"] + [
                ".property-item", 
                ".listing", 
                ".property-card", 
                ".estate-item",
                ".offer",
                ".annonce-container",
                ".product-item",
                ".views-row",
                ".item",
                "article"
            ]
            
            # Try each selector with patience
            property_locator = None
            property_count = 0
            
            for selector in property_selectors:
                try:
                    logger.info(f"Trying property selector: {selector}")
                    # Wait longer for content to appear
                    try:
                        page.wait_for_selector(selector, timeout=20000, state="visible")
                    except Exception:
                        pass
                    
                    count = page.locator(selector).count()
                    if count > 0:
                        logger.info(f"Found {count} properties with selector: {selector}")
                        property_locator = page.locator(selector)
                        property_count = count
                        break
                    else:
                        logger.info(f"No elements found with selector: {selector}")
                except Exception as e:
                    logger.warning(f"Error with selector '{selector}': {str(e)}")
            
            if not property_locator or property_count == 0:
                logger.warning("No properties found with primary selectors, trying alternatives...")
                
                # More generic backup selectors
                backup_selectors = [
                    "div:has(a:has(img))",
                    ".col:has(img)",
                    ".card",
                    ".panel",
                    ".box",
                    ".row:has(img)",
                    ".col-md-4",
                    ".col-sm-6"
                ]
                
                for selector in backup_selectors:
                    try:
                        count = page.locator(selector).count()
                        if count > 0:
                            logger.info(f"Found {count} potential properties with backup selector: {selector}")
                            property_locator = page.locator(selector)
                            property_count = count
                            break
                    except Exception as e:
                        logger.warning(f"Error with backup selector '{selector}': {str(e)}")
                
                if not property_locator or property_count == 0:
                    logger.error("No properties found on this page, moving to next page or site")
                    # We'll try one more page before giving up
                    if page_count == 1:
                        logger.info("First page had no properties, trying to navigate to next page anyway...")
                    else:
                        break
            
            # Process each property with patience
            for i in range(property_count):
                try:
                    logger.info(f"Processing {site_name} property {i+1}/{property_count}...")
                    # Select current property with timeout
                    try:
                        current_property = property_locator.nth(i)
                    except Exception as e:
                        logger.error(f"Could not select property {i+1}: {str(e)}")
                        continue
                    
                    # Take property-specific screenshot for debugging complex cases
                    if page_count == 1 and i == 0:
                        try:
                            screenshot_path = os.path.join(OUTPUT_FOLDER, f"{site_name}_property1.png")
                            current_property.screenshot(path=screenshot_path)
                            logger.info(f"Saved property screenshot to {screenshot_path}")
                        except Exception:
                            logger.warning("Could not take property screenshot")
                    
                    # Get property HTML for debugging
                    try:
                        property_html = current_property.evaluate("el => el.outerHTML")
                        if page_count == 1 and i == 0:
                            html_path = os.path.join(OUTPUT_FOLDER, f"{site_name}_property1.html")
                            with open(html_path, "w", encoding="utf-8") as f:
                                f.write(property_html)
                    except Exception:
                        property_html = ""
                        logger.warning("Could not extract property HTML")
                    
                    # Extract data
                    
                    # Title
                    title = ""
                    title_selectors = config["title_selectors"] + ["h3", "h2", "h1", ".title", ".name", ".property-title"]
                    for title_selector in title_selectors:
                        try:
                            elements = current_property.locator(title_selector).all()
                            for el in elements:
                                text = el.inner_text().strip()
                                if text and len(text) > 5:
                                    title = clean_text(text)
                                    break
                            if title:
                                break
                        except Exception:
                            continue
                    
                    # If title is empty, try to extract from link text
                    if not title:
                        try:
                            links = current_property.locator("a").all()
                            for link in links:
                                link_text = link.inner_text().strip()
                                if link_text and len(link_text) > 5 and not link_text.startswith("http"):
                                    title = clean_text(link_text)
                                    break
                        except Exception:
                            pass
                    
                    # Price - Look for text with numbers and currency indicators
                    price = ""
                    price_selectors = config["price_selectors"] + [
                        "strong", "*:has-text('DT')", "*:has-text('TND')", 
                        "*:has-text('€')", ".prix", ".price", ".property-price"
                    ]
                    for price_selector in price_selectors:
                        try:
                            elements = current_property.locator(price_selector).all()
                            for el in elements:
                                price_text = el.inner_text().strip()
                                if re.search(r'\d', price_text) and ('DT' in price_text or 'TND' in price_text or '€' in price_text or 'Dinar' in price_text):
                                    price = extract_price(price_text)
                                    break
                            if price:
                                break
                        except Exception:
                            continue
                    
                    # If no price found by selectors, search in all text
                    if not price and property_html:
                        try:
                            full_text = current_property.inner_text()
                            price_matches = re.findall(r'(\d[\d\s]*(?:DT|TND|€|Dinar|Dinars))', full_text)
                            if price_matches:
                                price = extract_price(price_matches[0])
                        except Exception:
                            pass
                    
                    # Location
                    location = ""
                    location_selectors = config["location_selectors"] + [
                        "span:has-text('Adresse')", "*:has-text('Adresse:')",
                        ".city", ".zone", ".quartier", ".district", ".region",
                        ".property-location", ".location-text"
                    ]
                    for location_selector in location_selectors:
                        try:
                            elements = current_property.locator(location_selector).all()
                            for el in elements:
                                loc_text = el.inner_text().strip()
                                if loc_text and 'Adresse' not in loc_text and len(loc_text) > 2:  # Minimum length
                                    location = clean_text(loc_text)
                                    break
                                elif 'Adresse' in loc_text and ':' in loc_text:
                                    location = clean_text(loc_text.split(':', 1)[1].strip())
                                    break
                            if location:
                                break
                        except Exception:
                            continue
                    
                    # If no location found, try to extract from the full text
                    if not location:
                        try:
                            full_text = current_property.inner_text()
                            # Common Tunisian cities/regions
                            cities = ["Tunis", "Sfax", "Sousse", "Kairouan", "Bizerte", "Gabès", 
                                     "Ariana", "Gafsa", "Monastir", "Ben Arous", "La Marsa", 
                                     "Kasserine", "Hammamet", "Nabeul", "Kélibia", "Mahdia"]
                            
                            for city in cities:
                                if city in full_text:
                                    location = city
                                    break
                        except Exception:
                            pass
                    
                    # Bedrooms - Look for "chambres" or "pièces" in French
                    bedrooms = ""
                    bedroom_selectors = [
                        ".chambres", ".pieces", ".nb-pieces", 
                        "span:has-text('chambre')", "span:has-text('pièce')",
                        "*:has-text('chambre')", "*:has-text('pièce')",
                        ".bedrooms", ".rooms"
                    ]
                    for bedrooms_selector in bedroom_selectors:
                        try:
                            elements = current_property.locator(bedrooms_selector).all()
                            for el in elements:
                                bedrooms_text = el.inner_text().strip()
                                if re.search(r'\d+\s*(?:chambre|pièce|pieces|bedroom|room)', bedrooms_text.lower()):
                                    bedrooms = extract_number(bedrooms_text)
                                    break
                            if bedrooms:
                                break
                        except Exception:
                            continue
                    
                    # If no bedrooms found, look in full text
                    if not bedrooms and property_html:
                        try:
                            full_text = current_property.inner_text()
                            bedroom_matches = re.findall(r'(\d+)\s*(?:chambre|pièce|pieces|bedroom|room)', full_text.lower())
                            if bedroom_matches:
                                bedrooms = bedroom_matches[0]
                        except Exception:
                            pass
                    
                    # Bathrooms - "salle de bain" in French
                    bathrooms = ""
                    bathroom_selectors = [
                        ".sdb", ".salles-de-bain", 
                        "span:has-text('salle de bain')", "span:has-text('salle d'eau')",
                        "*:has-text('salle de bain')", "*:has-text('salle d'eau')",
                        ".bathrooms", ".baths"
                    ]
                    for bathrooms_selector in bathroom_selectors:
                        try:
                            elements = current_property.locator(bathrooms_selector).all()
                            for el in elements:
                                bathrooms_text = el.inner_text().strip()
                                if re.search(r'\d+\s*(?:salle|bain|bath)', bathrooms_text.lower()):
                                    bathrooms = extract_number(bathrooms_text)
                                    break
                            if bathrooms:
                                break
                        except Exception:
                            continue
                    
                    # If no bathrooms found, look in full text
                    if not bathrooms and property_html:
                        try:
                            full_text = current_property.inner_text()
                            bath_matches = re.findall(r'(\d+)\s*(?:salle|bain|bath)', full_text.lower())
                            if bath_matches:
                                bathrooms = bath_matches[0]
                        except Exception:
                            pass
                    
                    # Area - "surface" in French
                    area = ""
                    area_selectors = config["area_selectors"] + [
                        "span:has-text('surface')",
                        "*:has-text('m²')", "*:has-text('surface')",
                        ".area", ".property-area", ".size"
                    ]
                    for area_selector in area_selectors:
                        try:
                            elements = current_property.locator(area_selector).all()
                            for el in elements:
                                area_text = el.inner_text().strip()
                                if re.search(r'\d+\s*(?:m²|m2|surface|area)', area_text.lower()):
                                    area = extract_number(area_text)
                                    break
                            if area:
                                break
                        except Exception:
                            continue
                    
                    # If no area found, look in full text
                    if not area and property_html:
                        try:
                            full_text = current_property.inner_text()
                            area_matches = re.findall(r'(\d+)\s*(?:m²|m2)', full_text.lower())
                            if area_matches:
                                area = area_matches[0]
                        except Exception:
                            pass
                    
                    # Property type - Extract from title or dedicated field
                    property_type = ""
                    type_selectors = [".type", ".categorie", ".property-type", ".category"]
                    for type_selector in type_selectors:
                        try:
                            elements = current_property.locator(type_selector).all()
                            for el in elements:
                                type_text = el.inner_text().strip()
                                if type_text:
                                    property_type = clean_text(type_text)
                                    break
                            if property_type:
                                break
                        except Exception:
                            continue
                    
                    # If no property type found, try to extract from title or full text
                    if not property_type:
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
                        
                        text_to_check = title.lower() if title else ""
                        if not text_to_check and property_html:
                            try:
                                text_to_check = current_property.inner_text().lower()
                            except Exception:
                                pass
                        
                        for key, value in property_types.items():
                            if key in text_to_check:
                                property_type = value
                                break
                    
                    # Description
                    description = ""
                    desc_selectors = [
                        ".description", ".resume", ".field-name-body", ".content", 
                        ".card-text", ".property-description", ".details",
                        ".summary", ".excerpt"
                    ]
                    for desc_selector in desc_selectors:
                        try:
                            elements = current_property.locator(desc_selector).all()
                            for el in elements:
                                desc_text = el.inner_text().strip()
                                if desc_text and len(desc_text) > 10:  # Minimum length to be a description
                                    description = clean_text(desc_text)
                                    break
                            if description:
                                break
                        except Exception:
                            continue
                    
                    # Features
                    features = []
                    features_selectors = [
                        ".amenities li", ".caracteristiques li", ".field-name-field-options li",
                        ".features li", ".options", ".property-features li", 
                        ".amenities", ".details li"
                    ]
                    for features_selector in features_selectors:
                        try:
                            feature_elements = current_property.locator(features_selector).all()
                            for feature_el in feature_elements:
                                feature = feature_el.inner_text().strip()
                                if feature:
                                    features.append(clean_text(feature))
                            if features:
                                break
                        except Exception:
                            continue
                    
                    # Image URL
                    image_url = ""
                    try:
                        image_elements = current_property.locator("img").all()
                        for img_el in image_elements:
                            src = img_el.get_attribute("src") or img_el.get_attribute("data-src") or ""
                            if src and not src.endswith(".ico") and not "logo" in src.lower():
                                # If relative URL, make it absolute
                                if not src.startswith(("http://", "https://")):
                                    base_domain = f"https://www.{site_name}"
                                    src = f"{base_domain}{src if src.startswith('/') else '/' + src}"
                                image_url = src
                                break
                    except Exception:
                        pass
                    
                    # Listing URL
                    listing_url = ""
                    try:
                        # Choose appropriate URL patterns based on the site
                        url_patterns = []
                        if "mubawab" in site_name:
                            url_patterns = ["/fr/ac/", "/ac/", "/property/"]
                        elif "tunisie-annonce" in site_name:
                            url_patterns = ["AnnoncesImmobilier", "DetailAnnonce"]
                        elif "menzili" in site_name:
                            url_patterns = ["/immo/", "/property/", "/vente/", "/bien/"]
                        else:
                            url_patterns = ["/property/", "/annonce/", "/vente/", "/achat/", "/bien/"]
                        
                        link_elements = current_property.locator("a").all()
                        for link_el in link_elements:
                            href = link_el.get_attribute("href") or ""
                            if href:
                                # Check if href matches any pattern for this site
                                if any(pattern in href for pattern in url_patterns):
                                    if not href.startswith(("http://", "https://")):
                                        if "tunisie-annonce" in site_name:
                                            base_url = "http://www.tunisie-annonce.com"
                                        else:
                                            base_url = f"https://www.{site_name}"
                                        href = f"{base_url}{href if href.startswith('/') else '/' + href}"
                                    listing_url = href
                                    break
                    except Exception:
                        pass
                    
                    # If we couldn't find a proper URL but have title, look for any link
                    if not listing_url and title:
                        try:
                            link_elements = current_property.locator("a").all()
                            for link_el in link_elements:
                                href = link_el.get_attribute("href") or ""
                                if href and (site_name in href or href.startswith("/")):
                                    if not href.startswith(("http://", "https://")):
                                        if "tunisie-annonce" in site_name:
                                            base_url = "http://www.tunisie-annonce.com"
                                        else:
                                            base_url = f"https://www.{site_name}"
                                        href = f"{base_url}{href if href.startswith('/') else '/' + href}"
                                    listing_url = href
                                    break
                        except Exception:
                            pass
                    
                    # If still no listing URL, use current page URL
                    if not listing_url:
                        listing_url = page.url
                    
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
                        "source_site": site_name,
                        "page_number": page_count,
                        "region": location or "Tunisia"
                    }
                    
                    # Only add if we have some basic data
                    if (title or property_type) and (price or location or area):
                        site_properties.append(property_data)
                        all_properties.append(property_data)
                        logger.info(f"  Added property {i+1}: {title[:30]}... | {price} | {location}")
                    else:
                        logger.warning(f"Skipped property with insufficient data: {title[:30]}")
                    
                    # Add a small delay between properties to avoid overloading the server
                    wait_with_random_delay(2, 6)
                    
                except Exception as e:
                    logger.error(f"Error processing property {i+1}: {str(e)}")
            
            # Save data after each page to avoid losing progress
            if site_properties:
                logger.info(f"Saving {len(site_properties)} properties collected so far from {site_name}...")
                intermediate_csv = os.path.join(OUTPUT_FOLDER, f"{site_name}_{TIMESTAMP}_page{page_count}.csv")
                intermediate_json = os.path.join(OUTPUT_FOLDER, f"{site_name}_{TIMESTAMP}_page{page_count}.json")
                
                save_to_csv(site_properties, intermediate_csv)
                save_to_json(site_properties, intermediate_json)
                logger.info(f"Saved intermediate data for {site_name} page {page_count}")
            
            # Check if we should continue to the next page
            if page_count < max_pages:
                # Try pagination
                logger.info(f"Looking for next page button on {site_name}...")
                next_page_selectors = config["pagination_selectors"] + [
                    "li.next a", 
                    "a.next",
                    "a:has-text('Suivant')",
                    "a:has-text('Page suivante')",
                    "a:has-text('»')",
                    "a[rel='next']",
                    ".pagination a:has-text('›')",
                    ".pagination a:has-text('>')",
                    "[aria-label='Next page']",
                    "[title='Page suivante']",
                    ".page-item:not(.disabled) a:has-text('›')",
                    ".active + li a"  # Link in the list item after the active one
                ]
                
                # Save the current URL to compare after clicking
                current_url = page.url
                
                next_clicked = False
                for selector in next_page_selectors:
                    try:
                        next_button = page.locator(selector)
                        if next_button.count() > 0:
                            try:
                                next_visible = next_button.first.is_visible()
                                logger.info(f"Found next page button with selector: {selector}, visible: {next_visible}")
                                
                                if next_visible:
                                    # Save URLs to detect navigation
                                    old_url = page.url
                                    
                                    # Take screenshot before clicking
                                    before_click_file = os.path.join(OUTPUT_FOLDER, f"{site_name}_before_next_page{page_count}.png")
                                    page.screenshot(path=before_click_file)
                                    
                                    # Try different click methods
                                    click_attempts = 0
                                    clicked = False
                                    
                                    while click_attempts < 3 and not clicked:
                                        try:
                                            if click_attempts == 0:
                                                logger.info("Trying normal click...")
                                                next_button.first.click(timeout=30000)
                                            elif click_attempts == 1:
                                                logger.info("Trying JS click...")
                                                page.evaluate(f"document.querySelector('{selector}').click()")
                                            else:
                                                logger.info("Trying navigate to href...")
                                                href = next_button.first.get_attribute("href")
                                                if href:
                                                    if not href.startswith(("http://", "https://")):
                                                        if "tunisie-annonce" in site_name:
                                                            base_url = "http://www.tunisie-annonce.com"
                                                        else:
                                                            base_url = f"https://www.{site_name}"
                                                        href = f"{base_url}{href if href.startswith('/') else '/' + href}"
                                                    logger.info(f"Navigating directly to next page URL: {href}")
                                                    page.goto(href, timeout=180000, wait_until="domcontentloaded")
                                            
                                            clicked = True
                                        except Exception as e:
                                            logger.error(f"Click attempt {click_attempts+1} failed: {str(e)}")
                                            click_attempts += 1
                                            time.sleep(10)
                                    
                                    if clicked:
                                        # Wait for URL or content to change
                                        try:
                                            logger.info("Waiting for navigation or content change...")
                                            # Multiple checks with longer timeouts
                                            change_detected = False
                                            for check in range(5):
                                                time.sleep(8)  # Wait between checks
                                                new_url = page.url
                                                if new_url != old_url:
                                                    logger.info(f"URL changed from {old_url} to {new_url}")
                                                    change_detected = True
                                                    break
                                            
                                            # Continue even if no change detected
                                            page_count += 1
                                            next_clicked = True
                                            
                                            logger.info(f"Moving to page {page_count}...")
                                            # Wait for page to load with longer timeout
                                            try:
                                                page.wait_for_load_state("domcontentloaded", timeout=60000)
                                            except Exception:
                                                logger.warning("Timeout waiting for page to load, continuing anyway...")
                                            
                                            # Wait additional time
                                            time.sleep(15)
                                            
                                            # Scroll down to load lazy content
                                            for scroll in range(4):
                                                page.evaluate(f"window.scrollTo(0, {(scroll+1) * 1200})")
                                                time.sleep(4)
                                            
                                            page.evaluate("window.scrollTo(0, 0)")
                                            time.sleep(5)
                                            break
                                        except Exception as e:
                                            logger.error(f"Error after clicking next: {str(e)}")
                            except Exception as e:
                                logger.error(f"Error checking visibility of next button: {str(e)}")
                    except Exception as e:
                        logger.warning(f"Error with next page selector '{selector}': {str(e)}")
                
                # If standard pagination failed, try URL-based pagination
                if not next_clicked:
                    logger.info("Standard pagination failed, trying URL-based pagination...")
                    try:
                        current_url = page.url
                        
                        # Different URL patterns for pagination
                        new_url = None
                        
                        # Mubawab pattern
                        if "mubawab" in site_name:
                            if "?page=" in current_url:
                                parts = current_url.split("?page=")
                                current_page_num = int(parts[1])
                                new_url = f"{parts[0]}?page={current_page_num + 1}"
                            else:
                                new_url = f"{current_url}?page={page_count + 1}"
                        
                        # Tunisie-annonce pattern
                        elif "tunisie-annonce" in site_name:
                            if "rech_page=" in current_url:
                                new_url = re.sub(r'rech_page=\d+', f'rech_page={page_count}', current_url)
                            else:
                                if "?" in current_url:
                                    new_url = f"{current_url}&rech_page={page_count}"
                                else:
                                    new_url = f"{current_url}?rech_page={page_count}"
                        
                        # Menzili pattern
                        elif "menzili" in site_name:
                            if "/page/" in current_url:
                                new_url = re.sub(r'/page/\d+', f'/page/{page_count}', current_url)
                            else:
                                base_url = current_url.rstrip('/')
                                new_url = f"{base_url}/page/{page_count}"
                        
                        # Try the new URL if constructed
                        if new_url and new_url != current_url:
                            logger.info(f"Trying URL-based pagination: {new_url}")
                            page.goto(new_url, timeout=180000, wait_until="domcontentloaded")
                            
                            # Wait for loading
                            try:
                                page.wait_for_load_state("domcontentloaded", timeout=60000)
                            except Exception:
                                logger.warning("Timeout waiting for page to load, continuing anyway...")
                            
                            # Wait additional time
                            time.sleep(15)
                            
                            # Take screenshot to verify
                            page.screenshot(path=os.path.join(OUTPUT_FOLDER, f"{site_name}_url_pagination_page{page_count}.png"))
                            
                            # Scroll to load content
                            for scroll in range(4):
                                page.evaluate(f"window.scrollTo(0, {(scroll+1) * 1200})")
                                time.sleep(4)
                            
                            page.evaluate("window.scrollTo(0, 0)")
                            time.sleep(5)
                            
                            page_count += 1
                            next_clicked = True
                    except Exception as e:
                        logger.error(f"URL-based pagination failed: {str(e)}")
                
                if not next_clicked:
                    logger.warning(f"No next page button found or all attempts failed for {site_name}. Ending pagination.")
                    break
            else:
                logger.info(f"Reached maximum page limit ({max_pages}). Stopping pagination for {site_name}.")
                break
        
        logger.info(f"Completed scraping of {site_name}. Total properties: {len(site_properties)}")
        
        # Save site-specific results
        if site_properties:
            site_csv = os.path.join(OUTPUT_FOLDER, f"{site_name}_{TIMESTAMP}_full.csv")
            site_json = os.path.join(OUTPUT_FOLDER, f"{site_name}_{TIMESTAMP}_full.json")
            
            save_to_csv(site_properties, site_csv)
            save_to_json(site_properties, site_json)
            
            logger.info(f"Saved {site_name} data to:")
            logger.info(f"- CSV: {site_csv}")
            logger.info(f"- JSON: {site_json}")
        
    except Exception as e:
        logger.error(f"Error scraping {site_name}: {str(e)}")
    finally:
        # Always close the context to free resources
        try:
            context.close()
        except Exception:
            pass
    
    return site_properties

def main():
    """Main function to scrape all configured websites"""
    start_time = datetime.now()
    logger.info(f"Starting multi-site patient scraper at {start_time}")
    
    # Create folder for this session
    session_folder = os.path.join(OUTPUT_FOLDER, TIMESTAMP)
    os.makedirs(session_folder, exist_ok=True)
    
    # List to store all properties from all sites
    all_properties = []
    
    # Use Playwright to handle browser automation
    with sync_playwright() as playwright:
        # Launch browser with specific options for improved stability
        browser = playwright.chromium.launch(
            headless=True,  # Run without UI
            args=[
                '--disable-dev-shm-usage',  # Overcome limited resource issues
                '--no-sandbox',  # Required in some environments
                '--disable-setuid-sandbox',
                '--disable-gpu',  # Disable GPU acceleration
                '--disable-web-security',  # Disable CORS and other web security features
                '--disable-features=IsolateOrigins,site-per-process',  # Disable site isolation
                '--disable-site-isolation-trials',
                '--disable-features=BlockInsecurePrivateNetworkRequests',
                '--disable-features=ScriptStreaming',  # Improve script parsing
                '--disable-infobars',
                '--window-size=1920,1080',  # Set window size
                '--start-maximized',
                '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
            ],
            slow_mo=100,  # Add a small delay between actions for stability
            timeout=180000  # 3 minutes timeout for browser operations
        )
        
        try:
            # Process each website in sequence
            for config in SITE_CONFIGS:
                site_name = config["name"]
                logger.info(f"\n\n{'*'*80}\nScraping website: {site_name}\n{'*'*80}")
                
                # Scrape the current site
                site_properties = scrape_properties(config, browser, all_properties)
                
                # Log progress
                logger.info(f"Finished scraping {site_name}. Got {len(site_properties)} properties.")
                logger.info(f"Running total: {len(all_properties)} properties collected so far")
                
                # Save all properties collected so far
                all_csv = os.path.join(OUTPUT_FOLDER, f"all_properties_{TIMESTAMP}.csv")
                all_json = os.path.join(OUTPUT_FOLDER, f"all_properties_{TIMESTAMP}.json")
                
                save_to_csv(all_properties, all_csv)
                save_to_json(all_properties, all_json)
                
                logger.info(f"Updated combined data files with {len(all_properties)} total properties")
                
                # Wait between sites to be considerate
                if config != SITE_CONFIGS[-1]:  # If not the last site
                    wait_time = 60 + random.randint(30, 90)  # 1.5-2.5 minutes
                    logger.info(f"Waiting {wait_time} seconds before scraping next site...")
                    time.sleep(wait_time)
        
        finally:
            # Close browser
            browser.close()
    
    # Calculate and log statistics
    end_time = datetime.now()
    duration = end_time - start_time
    logger.info(f"\n\n{'='*80}")
    logger.info(f"Scraping completed at {end_time}")
    logger.info(f"Total duration: {duration}")
    logger.info(f"Total properties collected: {len(all_properties)}")
    logger.info(f"Data saved to folder: {OUTPUT_FOLDER}")
    logger.info(f"Main CSV file: all_properties_{TIMESTAMP}.csv")
    logger.info(f"Main JSON file: all_properties_{TIMESTAMP}.json")
    logger.info(f"{'='*80}\n")
    
    return len(all_properties)

if __name__ == "__main__":
    properties_count = main()
    print(f"\nScraping complete! Collected {properties_count} properties.")
