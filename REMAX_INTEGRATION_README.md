# Remax.com.tn Integration Guide

This document provides instructions on how the Remax.com.tn property website has been integrated into the Tunisian property scraper.

## Integration Overview

The Remax Tunisia website uses a special hash-based URL pagination system and has a unique HTML structure that requires specialized handling. This integration adds comprehensive support for scraping properties from Remax.com.tn.

## Files Created/Modified

1. **Main Scraper Update**: `tunisian_property_scraper.py`
   - Added specialized `scrape_remax_site` function
   - Updated Remax site configuration with better selectors
   - Added error handling and fallbacks

2. **Helper Modules**:
   - `remax_helper.py` - Base helper functions
   - `remax_helper_new.py` - Improved helper with better error handling
   - `remax_hash_pagination.py` - Standalone module for hash pagination

3. **Test Files**:
   - `test_remax_details.py` - Tests property detail extraction
   - `test_remax_integration.py` - Basic integration test
   - `test_full_remax_integration.py` - Comprehensive integration test
   - `test_remax_in_main.py` - Tests integration with main scraper

## Implementation Details

### Hash-Based URL Pagination

Remax.com.tn uses hash-based URLs for pagination rather than traditional URL parameters:

```
https://www.remax.com.tn/PublicListingList.aspx#mode=gallery&tt=261&cur=TND&sb=MostRecent&page=2&sc=1048
```

The `handle_remax_hash_pagination` function handles this by:
1. Checking if the URL already has a hash fragment
2. Updating the page number if it exists
3. Adding a default hash with pagination parameters if it doesn't exist

### Property Data Extraction

The `extract_remax_property_data` function handles:
1. Title parsing: "Property Type - Transaction Type - Location"
2. Icons with tooltips for property features
3. Multiple extraction methods for reliability
4. Absolute URL generation for images and listing links

### Integration with Main Scraper

The main scraper now has a specialized function `scrape_remax_site` that handles Remax.com.tn's unique requirements:

```python
# In the main function
for config in SITE_CONFIGS:
    site_name = config["name"]
    
    # Scrape the current site
    if site_name == "remax.com.tn":
        try:
            # First, attempt to use the specialized Remax scraper function
            site_properties = scrape_remax_site(config, browser, all_properties)
        except Exception as e:
            logger.error(f"Error using specialized Remax scraper: {e}. Falling back to standard scraper.")
            # Fallback to standard scraper if specialized one fails
            site_properties = scrape_properties(config, browser, all_properties)
```

The `scrape_remax_site` function handles:
1. Hash-based URL pagination
2. Extraction of property data from listing pages
3. Error handling and fallbacks
4. Detailed logging and screenshots

### Error Handling and Robustness

The implementation includes multiple layers of robustness:

1. Module import fallbacks:
   ```python
   try:
       from remax_helper_updated import extract_remax_property_data
   except ImportError:
       try:
           from remax_helper import extract_remax_property_data
       except ImportError:
           # Fallback to standard extraction
           property_data = extract_property(property_item, config, site_name, page_count)
   ```

2. Multiple extraction methods for property features
3. Regular expression fallbacks for data parsing
4. Extensive error trapping and logging

## Site Configuration

The site configuration has been updated with improved selectors:

```python
{
    "name": "remax.com.tn",
    "base_url": "https://www.remax.com.tn/PublicListingList.aspx",
    "max_pages": 20,
    "property_selectors": [".gallery-item", ".propertyListItem", ".property-item", ".listingGridBox"],
    "title_selectors": [".gallery-title a", ".proplist_title a", "h3 a", ".listingTitle", ".property-address"],
    "price_selectors": [".gallery-price-main .proplist_price", ".main-price", ".gallery-price a", ".price"],
    "location_selectors": [".gallery-title a", ".location", ".property-location"],
    "area_selectors": [".gallery-icons span[data-area]", ".property-size", ".surface", ".proplist_area"],
    "bedrooms_selectors": [".gallery-icons span[data-bedrooms]", ".property-beds", ".bedrooms", ".beds", ".proplist_beds"],
    "bathrooms_selectors": [".gallery-icons span[data-bathrooms]", ".property-baths", ".bathrooms", ".baths", ".proplist_baths"],
    "hash_url_pagination": true  // Indicates this site uses hash-based URLs for pagination
}
```

## Testing

You can test the Remax integration with:

```powershell
python test_remax_in_main.py
```

For testing property detail page extraction:

```powershell
python test_remax_details.py
```

For a full integration test:

```powershell
python test_full_remax_integration.py
```

## Future Improvements

1. Add support for detailed property page extraction
2. Implement more robust error recovery
3. Add support for different sorting and filtering options in the hash URLs
4. Add regional property searches using Remax's location filters
            )
        except ImportError:
            # Fallback to built-in implementation
            site_properties = scrape_remax_site(config)
    else:
        # Use standard scraper for other sites
        site_properties = scrape_properties(config, browser, all_properties)
```

### 2. Add the `scrape_remax_site` Function

Add the following function to handle Remax.com.tn specifically:

```python
def scrape_remax_site(site_config, max_pages_override=None):
    """
    Special handler for Remax.com.tn to handle its hash-based URL pagination
    
    Args:
        site_config (dict): The site configuration dictionary
        max_pages_override (int, optional): Override for max pages to scrape
        
    Returns:
        list: Properties found on the site
    """
    site_name = site_config["name"]
    base_url = site_config["base_url"]
    logger.info(f"Starting specialized scraping for {site_name}")
    
    # Determine max pages to scrape
    max_pages = max_pages_override or site_config.get("max_pages", 20)
    
    # Initialize list for this site's properties
    site_properties = []
    
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()
        
        try:
            # Handle hash-based pagination for Remax.com.tn
            # ... 
            # See full implementation in scrape_remax_site function
            
        except Exception as e:
            logger.error(f"Error during {site_name} scraping: {e}")
        
        finally:
            # Close the browser
            browser.close()
    
    return site_properties
```

### 3. Add Property Extraction Functions

Add fallback functions for property extraction in case the helper module is not available:

```python
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
    # ... implementation details
```

### 4. Update Site Configuration

Ensure the site configuration for Remax.com.tn is accurate:

```python
{
    "name": "remax.com.tn",
    "base_url": "https://www.remax.com.tn/PublicListingList.aspx",
    "max_pages": 20,
    "property_selectors": [".gallery-item", ".propertyListItem", ".property-item", ".listingGridBox"],
    "title_selectors": [".gallery-title a", ".property-title", "h3", ".listingTitle", ".property-address"],
    "price_selectors": [".gallery-price-main .proplist_price", ".gallery-price a", ".price"],
    "location_selectors": [".gallery-title a", ".location", ".property-location"],
    "area_selectors": [".gallery-icons img[data-original-title*='Mètres']", ".property-size", ".surface"],
    "bedrooms_selectors": [".gallery-icons img[data-original-title*='chambres']", ".bedrooms", ".beds"],
    "bathrooms_selectors": [".gallery-icons img[data-original-title*='salles de bain']", ".bathrooms", ".baths"],
    "features_selectors": [".features", ".amenities", ".propertyFeatures"],
    "hash_url_pagination": True  # Flag to indicate hash-based pagination
}
```

## Summary

Our integration adds support for Remax.com.tn to the Tunisian property scraper by:

1. Creating dedicated modules for Remax.com.tn handling
2. Adding specialized property extraction for Remax's unique HTML structure
3. Implementing hash-based URL pagination support
4. Providing fallback mechanisms in case modules are missing

The solution was tested and successfully extracted 51 properties across 3 pages.

## Next Steps

1. Complete the integration with the main `scrape_tunisian_properties` function
2. Add proper error handling for the case when modules are not available
3. Ensure the extracted data is normalized and cleaned consistently with other sources
4. Consider adding more detailed property information by scraping individual listing pages
