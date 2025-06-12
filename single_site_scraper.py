from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
import csv
import json
import os
import time
from datetime import datetime
import sys

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

# Site-specific configurations with French terms
SITE_CONFIGS = {
    # Tecnocasa.tn
    "tecnocasa.tn": {
        "property_selector": ".property-content, .property-container, .views-row",
        "title_selector": "h3, .field-content a, .property-title",
        "price_selector": ".field-name-field-prix, .property-price, .field--name-field-prix",
        "location_selector": ".field-name-field-ville, .property-location, .field--name-field-ville",
        "bedrooms_selector": ".field-name-field-nb-pieces, .field-name-field-chambres, .field--name-field-nb-pieces",
        "bathrooms_selector": ".field-name-field-salles-de-bain, .field--name-field-salles-de-bain",
        "area_selector": ".field-name-field-surface, .property-area, .field--name-field-surface",
        "property_type_selector": ".field-name-field-type-bien, .property-type, .field--name-field-type-bien",
        "description_selector": ".field-name-body, .property-description",
        "features_selector": ".field-name-field-options li, .property-features li",
        "image_selector": ".field-slideshow-image img, .property-image img",
        "listing_url_selector": ".property-title a, .field-content a, h3 a",
        "next_page_selector": ".pager-next a, .pagination a[rel='next'], a:has-text('Suivant')",
        "wait_time": 3
    },
    # Mubawab.tn
    "mubawab.tn": {
        "property_selector": "article.listingBox, li.listingBox, [data-oas='property_card']",
        "title_selector": "h2.listingTitle, .title-wrapper h2",
        "price_selector": "span.priceTag, .prices",
        "location_selector": ".locationBox, .listingLocation",
        "bedrooms_selector": ".tagProp span:has-text('chambre'), .specification:has-text('Chambres')",
        "bathrooms_selector": ".tagProp span:has-text('bain'), .specification:has-text('SDB')",
        "area_selector": ".tagProp span:has-text('m²'), .surface",
        "property_type_selector": ".listingDetails li:first-child, .propertyType",
        "description_selector": ".listingDesc, .description",
        "features_selector": ".specsList li, .specifications li",
        "image_selector": ".imageContainer img, .mainImage img",
        "listing_url_selector": "article.listingBox a, li.listingBox a, h2.listingTitle a",
        "next_page_selector": ".pagination a.icon-arrow-right-3, .paginationBox a:has-text('Suivant')",
        "wait_time": 3
    },
    # Menzili.tn
    "menzili.tn": {
        "property_selector": ".real-estate-item, .property-item, .annonce-immobiliere",
        "title_selector": ".post-title, h3.entry-title",
        "price_selector": ".price, .property-price, .prix",
        "location_selector": ".location, .property-location, .localisation",
        "bedrooms_selector": ".data-room, .rooms, .chambres",
        "bathrooms_selector": ".data-bath, .baths, .sdb",
        "area_selector": ".data-area, .area, .superficie",
        "property_type_selector": ".property-type, .type-bien",
        "description_selector": ".description, .property-description",
        "features_selector": ".amenities li, .characteristics li, .options li",
        "image_selector": ".property-featured-image img, .thumb img",
        "listing_url_selector": ".post-title a, h3.entry-title a",
        "next_page_selector": ".pagination a.next, .paged a:has-text('Suivant')",
        "wait_time": 3
    },
    # Tunisie-annonce.com
    "tunisie-annonce.com": {
        "property_selector": "tr.bgvulg, tr.ligne1, tr.ligne0",
        "title_selector": "a.clannl, a.texte_annonce",
        "price_selector": "td:nth-child(4), .prix_annonce",
        "location_selector": "td:nth-child(3), .region_annonce",
        "bedrooms_selector": "td:has-text('chambres'), .chambres",
        "bathrooms_selector": "td:has-text('sdb'), .sdb",
        "area_selector": "td:has-text('m²'), .superficie",
        "property_type_selector": "td:nth-child(2), .type_bien",
        "description_selector": ".texte_desc, .description_annonce",
        "features_selector": ".details li, .caracteristiques li",
        "image_selector": "td img, .photo_annonce img",
        "listing_url_selector": "a.clannl, a.texte_annonce",
        "next_page_selector": "a:has-text('Suivante'), .navpage a:contains('Page Suivante')",
        "wait_time": 3
    },
    # Darcomtunisia.com
    "darcomtunisia.com": {
        "property_selector": ".property-item, .property-box, .single-property",
        "title_selector": ".property-title, h3.title",
        "price_selector": ".property-price, .price",
        "location_selector": ".property-location, .location",
        "bedrooms_selector": ".property-bedrooms, .bedroom, .fa-bed",
        "bathrooms_selector": ".property-bathrooms, .bathroom, .fa-bath",
        "area_selector": ".property-area, .area, .superficie",
        "property_type_selector": ".property-type, .type",
        "description_selector": ".property-description, .description",
        "features_selector": ".property-features li, .features li",
        "image_selector": ".property-image img, .property-thumbnail img",
        "listing_url_selector": ".property-title a, h3.title a",
        "next_page_selector": ".pagination a.next, .paginate a:contains('Suivant')",
        "wait_time": 3
    },
    # Fi-dari.tn
    "fi-dari.tn": {
        "property_selector": ".property-box-data, .real-estate-item",
        "title_selector": ".card-title a, .property-title",
        "price_selector": ".property-price, .price",
        "location_selector": ".property-location, .location, p:has-text('Lieu')",
        "bedrooms_selector": "span:has-text('Chambres'), .bedrooms, .chambre",
        "bathrooms_selector": "span:has-text('Salles de bain'), .bathrooms, .sdb",
        "area_selector": "span:has-text('Surface'), .area, .surface",
        "property_type_selector": ".property-type, .type-bien",
        "description_selector": ".property-description, .description, .content",
        "features_selector": ".property-features li, .features li",
        "image_selector": ".property-box img, .property-image img",
        "listing_url_selector": ".card-title a, .property-title a",
        "next_page_selector": ".page-item:not(.disabled) .page-link:has-text('›'), .pagination .next",
        "wait_time": 3
    }
}

# Default configuration for unknown sites
DEFAULT_CONFIG = {
    "property_selector": ".property, .listing, .annonce, article, .bien-immobilier",
    "title_selector": "h1, h2, h3, .title, .titre",
    "price_selector": ".price, .prix, .cout, .tarif",
    "location_selector": ".location, .localisation, .adresse, .lieu",
    "bedrooms_selector": ".bedrooms, .chambres, .pieces",
    "bathrooms_selector": ".bathrooms, .sdb, .salles-de-bain",
    "area_selector": ".area, .surface, .superficie, .taille",
    "property_type_selector": ".type, .categorie, .type-bien",
    "description_selector": ".description, .details, .texte, .contenu",
    "features_selector": ".features li, .caracteristiques li, .options li",
    "image_selector": "img",
    "listing_url_selector": "a",
    "next_page_selector": ".next, .suivant, .pagination a[rel='next'], a:has-text('Suivant')",
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

def scrape_site(url, headless=True, max_pages=3):
    """Scrape a real estate website with pagination support"""
    domain = get_domain(url)
    config = get_site_config(domain)
    
    print(f"\nStarting scraping of: {url}")
    print(f"Using configuration for domain: {domain}")
    print(f"Will scrape up to {max_pages} pages")
    
    # List to store all properties
    all_properties = []
    
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=headless)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
            viewport={"width": 1280, "height": 800}
        )
        page = context.new_page()
        
        try:
            # Navigate to the URL
            print(f"Loading page...")
            page.goto(url, timeout=60000)
            page.wait_for_load_state("networkidle", timeout=60000)
            
            # Wait a moment
            time.sleep(config["wait_time"])
            
            # Scroll down to load lazy content
            print("Scrolling to load more content...")
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(2)
            
            page_count = 1
            total_properties = 0
            
            # Process each page
            while page_count <= max_pages:
                print(f"Processing page {page_count}...")
                
                # Take a screenshot for debugging
                screenshot_file = f"{domain}_page{page_count}.png"
                page.screenshot(path=os.path.join(OUTPUT_FOLDER, screenshot_file))
                print(f"Saved screenshot to {screenshot_file}")
                
                # Wait for properties to load
                try:
                    print(f"Looking for properties using selector: {config['property_selector']}")
                    page.wait_for_selector(config["property_selector"], timeout=10000)
                except Exception as e:
                    print(f"No properties found with selector: {config['property_selector']}")
                    print(f"Error: {str(e)}")
                    
                    # Try fallback selectors
                    fallback_selectors = [
                        ".property", ".listing", ".annonce", "article", ".item", 
                        "tr", ".card", ".product", ".bien", "li.row", ".box"
                    ]
                    for selector in fallback_selectors:
                        try:
                            count = page.locator(selector).count()
                            if count > 0:
                                print(f"Found {count} items with fallback selector: {selector}")
                                config["property_selector"] = selector
                                break
                        except:
                            continue
                
                # Count properties
                property_count = page.locator(config["property_selector"]).count()
                print(f"Found {property_count} properties on page {page_count}")
                
                # Process each property
                for i in range(property_count):
                    try:
                        # Create locator for the current property
                        property_locator = page.locator(config["property_selector"]).nth(i)
                        
                        # Extract data using inner_text for text and get_attribute for attributes
                        title = ""
                        try:
                            title_selector = config["title_selector"]
                            if property_locator.locator(title_selector).count() > 0:
                                title = property_locator.locator(title_selector).first.inner_text().strip()
                        except Exception as e:
                            print(f"Error extracting title: {str(e)}")
                        
                        price = ""
                        try:
                            price_selector = config["price_selector"]
                            if property_locator.locator(price_selector).count() > 0:
                                price = property_locator.locator(price_selector).first.inner_text().strip()
                        except Exception as e:
                            print(f"Error extracting price: {str(e)}")
                        
                        location = ""
                        try:
                            location_selector = config["location_selector"]
                            if property_locator.locator(location_selector).count() > 0:
                                location = property_locator.locator(location_selector).first.inner_text().strip()
                        except Exception as e:
                            print(f"Error extracting location: {str(e)}")
                        
                        # Extract other fields
                        bedrooms = ""
                        try:
                            bedrooms_selector = config["bedrooms_selector"]
                            if property_locator.locator(bedrooms_selector).count() > 0:
                                bedrooms = property_locator.locator(bedrooms_selector).first.inner_text().strip()
                        except Exception as e:
                            pass
                        
                        bathrooms = ""
                        try:
                            bathrooms_selector = config["bathrooms_selector"]
                            if property_locator.locator(bathrooms_selector).count() > 0:
                                bathrooms = property_locator.locator(bathrooms_selector).first.inner_text().strip()
                        except Exception as e:
                            pass
                        
                        area = ""
                        try:
                            area_selector = config["area_selector"]
                            if property_locator.locator(area_selector).count() > 0:
                                area = property_locator.locator(area_selector).first.inner_text().strip()
                        except Exception as e:
                            pass
                        
                        property_type = ""
                        try:
                            type_selector = config["property_type_selector"]
                            if property_locator.locator(type_selector).count() > 0:
                                property_type = property_locator.locator(type_selector).first.inner_text().strip()
                        except Exception as e:
                            pass
                        
                        description = ""
                        try:
                            desc_selector = config["description_selector"]
                            if property_locator.locator(desc_selector).count() > 0:
                                description = property_locator.locator(desc_selector).first.inner_text().strip()
                        except Exception as e:
                            pass
                        
                        # Extract features as a list
                        features = []
                        try:
                            features_selector = config["features_selector"]
                            features_count = property_locator.locator(features_selector).count()
                            for j in range(features_count):
                                feature = property_locator.locator(features_selector).nth(j).inner_text().strip()
                                features.append(feature)
                        except Exception as e:
                            pass
                        
                        # Extract image URL
                        image_url = ""
                        try:
                            image_selector = config["image_selector"]
                            if property_locator.locator(image_selector).count() > 0:
                                # Try src first, then data-src attributes
                                image_element = property_locator.locator(image_selector).first
                                image_url = image_element.get_attribute("src") or \
                                           image_element.get_attribute("data-src") or \
                                           image_element.get_attribute("data-lazy-src") or ""
                                
                                # If relative URL, make it absolute
                                if image_url and not image_url.startswith(("http://", "https://")):
                                    base_url = f"https://{domain}"
                                    image_url = f"{base_url}{image_url if image_url.startswith('/') else '/' + image_url}"
                        except Exception as e:
                            pass
                        
                        # Extract listing URL
                        listing_url = ""
                        try:
                            url_selector = config["listing_url_selector"]
                            if property_locator.locator(url_selector).count() > 0:
                                relative_url = property_locator.locator(url_selector).first.get_attribute("href") or ""
                                
                                # If relative URL, make it absolute
                                if relative_url:
                                    if relative_url.startswith(("http://", "https://")):
                                        listing_url = relative_url
                                    else:
                                        base_url = f"https://{domain}"
                                        listing_url = f"{base_url}{relative_url if relative_url.startswith('/') else '/' + relative_url}"
                        except Exception as e:
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
                        
                        if title or price or location:  # Only add if we have some basic data
                            all_properties.append(property_data)
                            total_properties += 1
                            print(f"  Added property {i+1}: {title[:30]}... | {price} | {location}")
                        
                    except Exception as e:
                        print(f"Error processing property {i+1}: {str(e)}")
                
                # Save data after each page to avoid losing progress
                if all_properties:
                    intermediate_csv = os.path.join(OUTPUT_FOLDER, f"{domain}_{TIMESTAMP}_page{page_count}.csv")
                    intermediate_json = os.path.join(OUTPUT_FOLDER, f"{domain}_{TIMESTAMP}_page{page_count}.json")
                    
                    save_to_csv(all_properties, intermediate_csv)
                    save_to_json(all_properties, intermediate_json)
                    print(f"Saved {len(all_properties)} properties to intermediate files")
                
                # Check if there's a next page
                if page_count < max_pages:
                    next_selector = config["next_page_selector"]
                    try:
                        # Check if next page element exists and is visible
                        has_next = page.locator(next_selector).count() > 0 and page.locator(next_selector).first.is_visible()
                        
                        if has_next:
                            print("Navigating to next page...")
                            # Take screenshot before clicking
                            page.screenshot(path=os.path.join(OUTPUT_FOLDER, f"{domain}_before_next_page{page_count}.png"))
                            
                            page.locator(next_selector).first.click()
                            page_count += 1
                            
                            # Wait for page to load
                            page.wait_for_load_state("networkidle", timeout=30000)
                            
                            # Scroll down to load lazy content
                            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                            time.sleep(3)
                        else:
                            print("No next page button found. Ending pagination.")
                            break
                    except Exception as e:
                        print(f"Error navigating to next page: {str(e)}")
                        
                        # Try fallback selectors for next page
                        fallback_next_selectors = [
                            "a:has-text('Suivant')", 
                            "a:has-text('Next')",
                            ".pagination a[rel='next']",
                            ".pagination-next",
                            ".next a",
                            "a.next",
                            ".pagination li:last-child a",
                            ".pagination a:last-child",
                            "a:has-text('›')"
                        ]
                        
                        next_clicked = False
                        for selector in fallback_next_selectors:
                            try:
                                if page.locator(selector).count() > 0 and page.locator(selector).first.is_visible():
                                    print(f"Trying fallback next page selector: {selector}")
                                    page.locator(selector).first.click()
                                    next_clicked = True
                                    page_count += 1
                                    
                                    # Wait for page to load
                                    page.wait_for_load_state("networkidle", timeout=30000)
                                    
                                    # Scroll down to load lazy content
                                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                                    time.sleep(3)
                                    break
                            except:
                                continue
                        
                        if not next_clicked:
                            break
                else:
                    print(f"Reached maximum page limit ({max_pages}). Stopping pagination.")
                    break
            
            print(f"Completed scraping of {domain}. Total properties: {total_properties}")
            
        except Exception as e:
            print(f"Error scraping {domain}: {str(e)}")
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
    """Main function to scrape a single real estate site"""
    # Default settings
    url = None
    headless = False
    max_pages = 3
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        url = sys.argv[1]
        
        # Optional parameters
        if len(sys.argv) > 2:
            try:
                max_pages = int(sys.argv[2])
            except:
                pass
            
        if len(sys.argv) > 3:
            headless = sys.argv[3].lower() in ('true', 'yes', '1')
    
    # If no URL provided, use a default or ask for input
    if not url:
        print("Available websites:")
        print("1. tecnocasa.tn")
        print("2. mubawab.tn")
        print("3. menzili.tn")
        print("4. tunisie-annonce.com")
        print("5. darcomtunisia.com")
        print("6. fi-dari.tn")
        
        choice = input("Enter a number (1-6) or paste a full URL: ")
        
        if choice == '1':
            url = "https://www.tecnocasa.tn/vendre/immeubles/nord-est-ne/cap-bon/kelibia.html"
        elif choice == '2':
            url = "https://www.mubawab.tn/fr/ct/tunis/immobilier-a-vendre"
        elif choice == '3':
            url = "https://www.menzili.tn/immo/vente-immobilier-tunisie"
        elif choice == '4':
            url = "http://www.tunisie-annonce.com/AnnoncesImmobilier.asp?rech_cod_rub=101&rech_cod_typ=10102"
        elif choice == '5':
            url = "https://www.darcomtunisia.com/search?property_types%5B%5D=1&vocations%5B%5D=1&vocations%5B%5D=2&reference=&surface_terrain_min=&prix_max="
        elif choice == '6':
            url = "https://fi-dari.tn/search?objectif=vendre&usage=Tout+usage&bounds=[[37.649,7.778],[30.107,11.953]]&page=1"
        else:
            url = choice
        
        # Get max pages
        try:
            max_pages_input = input(f"Enter maximum pages to scrape (default: {max_pages}): ")
            if max_pages_input:
                max_pages = int(max_pages_input)
        except:
            pass
        
        # Get headless mode
        try:
            headless_input = input(f"Run in headless mode? (no browser visible) (yes/no, default: {'yes' if headless else 'no'}): ")
            if headless_input:
                headless = headless_input.lower() in ('yes', 'y', 'true', '1')
        except:
            pass
    
    print(f"\nStarting scraper at {TIMESTAMP}")
    print(f"URL: {url}")
    print(f"Max pages: {max_pages}")
    print(f"Headless mode: {headless}")
    
    domain = get_domain(url)
    
    # Scrape the site
    all_properties = scrape_site(url, headless, max_pages)
    
    # Save final results
    if all_properties:
        csv_filename = os.path.join(OUTPUT_FOLDER, f"{domain}_{TIMESTAMP}_full.csv")
        json_filename = os.path.join(OUTPUT_FOLDER, f"{domain}_{TIMESTAMP}_full.json")
        
        save_to_csv(all_properties, csv_filename)
        save_to_json(all_properties, json_filename)
        
        print(f"\nScraping completed. Total properties collected: {len(all_properties)}")
        print(f"- CSV file: {csv_filename}")
        print(f"- JSON file: {json_filename}")
    else:
        print("\nNo properties were collected from the site.")

if __name__ == "__main__":
    main()
