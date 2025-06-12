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

def wait_with_random_delay(min_seconds=1, max_seconds=5):
    """Wait for a random time between min and max seconds to appear more human-like"""
    import random
    delay = min_seconds + random.random() * (max_seconds - min_seconds)
    time.sleep(delay)

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
    page = context.new_page()
    
    try:
        # Navigate to the URL with retry mechanism
        print(f"Loading page...")
        max_page_load_attempts = 3
        page_loaded = False            for attempt in range(max_page_load_attempts):
                try:
                    # Try to navigate without waiting for networkidle first
                    print(f"Navigating to {url} (attempt {attempt+1})")
                    page.goto(url, timeout=120000, wait_until="domcontentloaded")  # Extended timeout, less strict condition
                    
                    print(f"DOM content loaded, waiting for visibility of key elements...")
                    # Wait for some key elements that indicate the page is usable
                    try:
                        # Wait for any of these selectors to appear (indicating page is somewhat loaded)
                        selectors = ["img", ".immeuble", ".views-row", "a", ".node", ".annonce-wrapper", ".header", "h1", "h2"]
                        for selector in selectors:
                            try:
                                page.wait_for_selector(selector, timeout=15000, state="visible")
                                print(f"Found visible element with selector: {selector}")
                                break
                            except:
                                continue
                    except:
                        print("Could not find any key elements but continuing...")
                    
                    # Try to wait for network idle but don't fail if it times out
                    try:
                        print("Waiting for network to become idle (but will continue regardless)...")
                        page.wait_for_load_state("networkidle", timeout=30000)
                        print("Network is idle")
                    except:
                        print("Network not idle, but continuing anyway...")
                    
                    page_loaded = True
                    print(f"Page considered loaded on attempt {attempt+1}")
                    break
                except Exception as e:
                    print(f"Error loading page on attempt {attempt+1}: {str(e)}")
                    if attempt < max_page_load_attempts - 1:
                        print(f"Waiting before retry...")
                        time.sleep(30)  # Longer wait between retries
                        
                        # Try to reset browser context if we're having persistent issues
                        if attempt == 1:
                            try:
                                print("Trying to reset browser context...")
                                context.close()
                                context = browser.new_context(
                                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
                                    viewport={"width": 1280, "height": 800}
                                )
                                page = context.new_page()
                            except:
                                print("Failed to reset context, continuing with current one...")
                    else:
                        print(f"Warning: Failed to load page after {max_page_load_attempts} attempts, but will try to continue with partial content")
        
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
        max_pages = 15  # Increased from 10 to handle more pages per region
        
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
                ".annonce-wrapper",
                ".node-immeuble",
                "article"
            ]
            
            # Try each selector with patience
            property_locator = None
            property_count = 0
            
            for selector in property_selectors:
                try:
                    print(f"Trying selector: {selector}")
                    # Wait longer for content to appear
                    try:
                        page.wait_for_selector(selector, timeout=15000, state="visible")
                    except:
                        pass
                    
                    count = page.locator(selector).count()
                    if count > 0:
                        print(f"Found {count} properties with selector: {selector}")
                        property_locator = page.locator(selector)
                        property_count = count
                        break
                    else:
                        print(f"No elements found with selector: {selector}")
                except Exception as e:
                    print(f"Error with selector '{selector}': {str(e)}")
            
            if not property_locator or property_count == 0:
                print("No properties found with primary selectors, trying alternatives...")
                
                # More generic backup selectors
                backup_selectors = [
                    "div.annonce",
                    "div:has(a:has(img))",
                    ".col:has(img)",
                    ".well", 
                    ".card",
                    ".panel",
                    ".row:has(img)"
                ]
                
                for selector in backup_selectors:
                    try:
                        count = page.locator(selector).count()
                        if count > 0:
                            print(f"Found {count} potential properties with backup selector: {selector}")
                            property_locator = page.locator(selector)
                            property_count = count
                            break
                    except Exception as e:
                        print(f"Error with backup selector '{selector}': {str(e)}")
                
                if not property_locator or property_count == 0:
                    # Save HTML for debugging
                    html = page.content()
                    html_file = os.path.join(OUTPUT_FOLDER, f"{domain}_{region}_page{page_count}.html")
                    with open(html_file, "w", encoding="utf-8") as f:
                        f.write(html)
                    print(f"Saved HTML to {html_file} for debugging")
                    
                    print("No properties found, moving to next page or region")
                    # We'll try one more page before giving up
                    if page_count == 1:
                        print("First page had no properties, trying to navigate to next page anyway...")
                    else:
                        break
            
            # Process each property with patience
            for i in range(property_count):
                try:
                    print(f"Processing property {i+1}/{property_count}...")
                    # Select current property with timeout
                    try:
                        current_property = property_locator.nth(i)
                    except Exception as e:
                        print(f"Could not select property {i+1}: {str(e)}")
                        continue
                    
                    # Take property-specific screenshot for debugging complex cases
                    if page_count == 1 and i == 0:
                        try:
                            screenshot_path = os.path.join(OUTPUT_FOLDER, f"{domain}_{region}_property1.png")
                            current_property.screenshot(path=screenshot_path)
                            print(f"Saved property screenshot to {screenshot_path}")
                        except:
                            print("Could not take property screenshot")
                    
                    # Get property HTML for debugging
                    try:
                        property_html = current_property.evaluate("el => el.outerHTML")
                        if page_count == 1 and i == 0:
                            html_path = os.path.join(OUTPUT_FOLDER, f"{domain}_{region}_property1.html")
                            with open(html_path, "w", encoding="utf-8") as f:
                                f.write(property_html)
                            print(f"Saved property HTML to {html_path}")
                    except:
                        property_html = ""
                        print("Could not extract property HTML")
                    
                    # Extract data with specific French selectors for Tecnocasa
                    
                    # Title
                    title = ""
                    title_selectors = ["h3", ".titre", ".titre-annonce", "h2", ".field-content", ".card-title", ".panel-title"]
                    for title_selector in title_selectors:
                        try:
                            elements = current_property.locator(title_selector).all()
                            for el in elements:
                                text = el.inner_text().strip()
                                if text and len(text) > 5:
                                    title = text
                                    break
                            if title:
                                break
                        except:
                            continue
                    
                    # If title is empty, try to extract from link text
                    if not title:
                        try:
                            links = current_property.locator("a").all()
                            for link in links:
                                link_text = link.inner_text().strip()
                                if link_text and len(link_text) > 5 and not link_text.startswith("http"):
                                    title = link_text
                                    break
                        except:
                            pass
                    
                    # Price - Look for text with numbers and currency indicators
                    price = ""
                    price_selectors = [".prix", ".price", "strong", ".field-name-field-prix", 
                                      "span:has-text('DT')", "span:has-text('TND')", 
                                      "*:has-text('DT')", "*:has-text('TND')"]
                    for price_selector in price_selectors:
                        try:
                            elements = current_property.locator(price_selector).all()
                            for el in elements:
                                price_text = el.inner_text().strip()
                                if re.search(r'\d', price_text) and ('DT' in price_text or 'TND' in price_text or '€' in price_text):
                                    price = extract_price(price_text)
                                    break
                            if price:
                                break
                        except:
                            continue
                    
                    # If no price found by selectors, search in all text
                    if not price and property_html:
                        try:
                            full_text = current_property.inner_text()
                            price_matches = re.findall(r'(\d[\d\s]*(?:DT|TND|€))', full_text)
                            if price_matches:
                                price = extract_price(price_matches[0])
                        except:
                            pass
                    
                    # Location
                    location = ""
                    location_selectors = [".lieu", ".location", ".adresse", ".field-name-field-ville", 
                                        "span:has-text('Adresse')", "*:has-text('Adresse:')",
                                        ".city", ".zone", ".quartier"]
                    for location_selector in location_selectors:
                        try:
                            elements = current_property.locator(location_selector).all()
                            for el in elements:
                                loc_text = el.inner_text().strip()
                                if loc_text and 'Adresse' not in loc_text and len(loc_text) > 2:
                                    location = loc_text
                                    break
                                elif 'Adresse' in loc_text and ':' in loc_text:
                                    location = loc_text.split(':', 1)[1].strip()
                                    break
                            if location:
                                break
                        except:
                            continue
                    
                    # If no location found but we have region, use that
                    if not location:
                        location = region.capitalize()
                    
                    # Bedrooms - Look for "chambres" or "pièces" in French
                    bedrooms = ""
                    bedroom_selectors = [".chambres", ".pieces", ".nb-pieces", 
                                       "span:has-text('chambre')", "span:has-text('pièce')",
                                       "*:has-text('chambre')", "*:has-text('pièce')"]
                    for bedrooms_selector in bedroom_selectors:
                        try:
                            elements = current_property.locator(bedrooms_selector).all()
                            for el in elements:
                                bedrooms_text = el.inner_text().strip()
                                if re.search(r'\d+\s*(?:chambre|pièce|pieces)', bedrooms_text.lower()):
                                    bedrooms = extract_number(bedrooms_text)
                                    break
                            if bedrooms:
                                break
                        except:
                            continue
                    
                    # If no bedrooms found, look in full text
                    if not bedrooms and property_html:
                        try:
                            full_text = current_property.inner_text()
                            bedroom_matches = re.findall(r'(\d+)\s*(?:chambre|pièce|pieces)', full_text.lower())
                            if bedroom_matches:
                                bedrooms = bedroom_matches[0]
                        except:
                            pass
                    
                    # Bathrooms - "salle de bain" in French
                    bathrooms = ""
                    bathroom_selectors = [".sdb", ".salles-de-bain", 
                                        "span:has-text('salle de bain')", "span:has-text('salle d'eau')",
                                        "*:has-text('salle de bain')", "*:has-text('salle d'eau')"]
                    for bathrooms_selector in bathroom_selectors:
                        try:
                            elements = current_property.locator(bathrooms_selector).all()
                            for el in elements:
                                bathrooms_text = el.inner_text().strip()
                                if re.search(r'\d+\s*(?:salle|bain)', bathrooms_text.lower()):
                                    bathrooms = extract_number(bathrooms_text)
                                    break
                            if bathrooms:
                                break
                        except:
                            continue
                    
                    # If no bathrooms found, look in full text
                    if not bathrooms and property_html:
                        try:
                            full_text = current_property.inner_text()
                            bath_matches = re.findall(r'(\d+)\s*(?:salle|bain)', full_text.lower())
                            if bath_matches:
                                bathrooms = bath_matches[0]
                        except:
                            pass
                    
                    # Area - "surface" in French
                    area = ""
                    area_selectors = [".surface", ".field-name-field-surface", 
                                    "span:has-text('m²')", "span:has-text('surface')",
                                    "*:has-text('m²')", "*:has-text('surface')"]
                    for area_selector in area_selectors:
                        try:
                            elements = current_property.locator(area_selector).all()
                            for el in elements:
                                area_text = el.inner_text().strip()
                                if re.search(r'\d+\s*(?:m²|surface)', area_text.lower()):
                                    area = extract_number(area_text)
                                    break
                            if area:
                                break
                        except:
                            continue
                    
                    # If no area found, look in full text
                    if not area and property_html:
                        try:
                            full_text = current_property.inner_text()
                            area_matches = re.findall(r'(\d+)\s*(?:m²|m2)', full_text.lower())
                            if area_matches:
                                area = area_matches[0]
                        except:
                            pass
                    
                    # Property type - Extract from title or dedicated field
                    property_type = ""
                    type_selectors = [".type", ".categorie", ".field-name-field-type-bien"]
                    for type_selector in type_selectors:
                        try:
                            elements = current_property.locator(type_selector).all()
                            for el in elements:
                                type_text = el.inner_text().strip()
                                if type_text:
                                    property_type = type_text
                                    break
                            if property_type:
                                break
                        except:
                            continue
                    
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
                    desc_selectors = [".description", ".resume", ".field-name-body", ".content", 
                                    ".card-text", ".property-description"]
                    for desc_selector in desc_selectors:
                        try:
                            elements = current_property.locator(desc_selector).all()
                            for el in elements:
                                desc_text = el.inner_text().strip()
                                if desc_text and len(desc_text) > 10:  # Minimum length to be a description
                                    description = desc_text
                                    break
                            if description:
                                break
                        except:
                            continue
                    
                    # Features
                    features = []
                    features_selectors = [".amenities li", ".caracteristiques li", ".field-name-field-options li",
                                        ".features li", ".options"]
                    for features_selector in features_selectors:
                        try:
                            feature_elements = current_property.locator(features_selector).all()
                            for feature_el in feature_elements:
                                feature = feature_el.inner_text().strip()
                                if feature:
                                    features.append(feature)
                            if features:
                                break
                        except:
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
                                    base_url = f"https://{domain}"
                                    src = f"{base_url}{src if src.startswith('/') else '/' + src}"
                                image_url = src
                                break
                    except:
                        pass
                    
                    # Listing URL
                    listing_url = ""
                    try:
                        link_elements = current_property.locator("a").all()
                        for link_el in link_elements:
                            href = link_el.get_attribute("href") or ""
                            if href and ("/immeubles/" in href or "/immeuble" in href or "/bien" in href):
                                if not href.startswith(("http://", "https://")):
                                    base_url = f"https://{domain}"
                                    href = f"{base_url}{href if href.startswith('/') else '/' + href}"
                                listing_url = href
                                break
                    except:
                        pass
                    
                    # If we couldn't find a proper URL but have title, look for any link
                    if not listing_url and title:
                        try:
                            link_elements = current_property.locator("a").all()
                            for link_el in link_elements:
                                href = link_el.get_attribute("href") or ""
                                if href and (domain in href or href.startswith("/")):
                                    if not href.startswith(("http://", "https://")):
                                        base_url = f"https://{domain}"
                                        href = f"{base_url}{href if href.startswith('/') else '/' + href}"
                                    listing_url = href
                                    break
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
                        "page_number": page_count,
                        "region": region
                    }
                    
                    # Only add if we have some basic data
                    if (title or property_type) and (price or location or area):
                        region_properties.append(property_data)
                        all_properties.append(property_data)
                        print(f"  Added property {i+1}: {title[:30]}... | {price} | {location}")
                    
                    # Add a small delay between properties to avoid overloading the server
                    wait_with_random_delay(1, 3)
                    
                except Exception as e:
                    print(f"Error processing property {i+1}: {str(e)}")
            
            # Save data after each page to avoid losing progress
            if region_properties:
                intermediate_csv = os.path.join(OUTPUT_FOLDER, f"{domain}_{region}_{TIMESTAMP}_page{page_count}.csv")
                intermediate_json = os.path.join(OUTPUT_FOLDER, f"{domain}_{region}_{TIMESTAMP}_page{page_count}.json")
                
                save_to_csv(region_properties, intermediate_csv)
                save_to_json(region_properties, intermediate_json)
                print(f"Saved {len(region_properties)} properties to intermediate files")                # Check if there's a next page
                if page_count < max_pages:
                    # Different next page selectors in French
                    next_page_selectors = [
                        "li.next a", 
                        "a.next",
                        ".pager-next a",
                        "a:has-text('Suivant')",
                        "a:has-text('Page suivante')",
                        "a:has-text('»')",
                        "a[rel='next']",
                        ".pagination a:has-text('›')",
                        "[aria-label='Next page']",
                        "[title='Page suivante']",
                        ".page-item:not(.disabled) a:has-text('›')",
                        ".active + li a"  # Link in the list item after the active one
                    ]
                    
                    print("Checking for next page button...")
                    # Save the current URL to compare after clicking
                    current_url = page.url
                    
                    next_clicked = False
                    for selector in next_page_selectors:
                        try:
                            next_button = page.locator(selector)
                            if next_button.count() > 0:
                                try:
                                    next_visible = next_button.first.is_visible()
                                    print(f"Found next page button with selector: {selector}, visible: {next_visible}")
                                    
                                    if next_visible:
                                        # Save URLs to detect navigation
                                        old_url = page.url
                                        
                                        # Take screenshot before clicking
                                        before_click_file = os.path.join(OUTPUT_FOLDER, f"{domain}_{region}_before_next_page{page_count}.png")
                                        page.screenshot(path=before_click_file)
                                        print(f"Saved screenshot before clicking next: {before_click_file}")
                                        
                                        # Try different click methods
                                        click_attempts = 0
                                        clicked = False
                                        
                                        while click_attempts < 3 and not clicked:
                                            try:
                                                if click_attempts == 0:
                                                    print("Trying normal click...")
                                                    next_button.first.click(timeout=15000)
                                                elif click_attempts == 1:
                                                    print("Trying JS click...")
                                                    page.evaluate(f"document.querySelector('{selector}').click()")
                                                else:
                                                    print("Trying navigate to href...")
                                                    href = next_button.first.get_attribute("href")
                                                    if href:
                                                        if not href.startswith(("http://", "https://")):
                                                            base_url = f"https://{domain}"
                                                            href = f"{base_url}{href if href.startswith('/') else '/' + href}"
                                                        print(f"Navigating directly to next page URL: {href}")
                                                        page.goto(href, timeout=90000, wait_until="domcontentloaded")
                                                
                                                clicked = True
                                            except Exception as e:
                                                print(f"Click attempt {click_attempts+1} failed: {str(e)}")
                                                click_attempts += 1
                                                time.sleep(5)
                                        
                                        if clicked:
                                            # Wait for URL to change or content to change
                                            try:
                                                print("Waiting for navigation or content change...")
                                                # First try to detect URL change
                                                change_detected = False
                                                for check in range(5):  # Check a few times
                                                    new_url = page.url
                                                    if new_url != old_url:
                                                        print(f"URL changed from {old_url} to {new_url}")
                                                        change_detected = True
                                                        break
                                                    
                                                    # If URL didn't change, check if content changed
                                                    if check == 2:  # On middle check, try to detect content change
                                                        try:
                                                            # Take a screenshot to see if page changed
                                                            after_click_file = os.path.join(OUTPUT_FOLDER, f"{domain}_{region}_after_next_page{page_count}.png")
                                                            page.screenshot(path=after_click_file)
                                                            print(f"Saved screenshot after clicking next: {after_click_file}")
                                                        except:
                                                            pass
                                                    
                                                    # Wait briefly before checking again
                                                    time.sleep(5)
                                                
                                                if change_detected or True:  # Continue anyway
                                                    page_count += 1
                                                    next_clicked = True
                                                    
                                                    # Wait for page to load with longer timeout, but don't fail if it times out
                                                    try:
                                                        page.wait_for_load_state("domcontentloaded", timeout=45000)
                                                    except:
                                                        print("Timeout waiting for page to load, continuing anyway...")
                                                    
                                                    # Wait additional time
                                                    print("Waiting for next page to fully load...")
                                                    time.sleep(15)
                                                    
                                                    # Scroll down to load lazy content
                                                    for scroll in range(3):
                                                        page.evaluate(f"window.scrollTo(0, {(scroll+1) * 1000})")
                                                        time.sleep(3)
                                                    
                                                    page.evaluate("window.scrollTo(0, 0)")
                                                    time.sleep(3)
                                                    break
                                            except Exception as e:
                                                print(f"Error after clicking next: {str(e)}")
                                except Exception as e:
                                    print(f"Error checking visibility of next button: {str(e)}")
                        except Exception as e:
                            print(f"Error with next page selector '{selector}': {str(e)}")
                    
                    if not next_clicked:
                        print("No next page button found or all attempts failed. Ending pagination for this region.")
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
            slow_mo=200
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
