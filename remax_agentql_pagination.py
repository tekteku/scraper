"""
Remax.com.tn AgentQL-based Pagination Module

This module demonstrates how to use AgentQL to handle Remax.com.tn's hash-based URL pagination.
AgentQL provides a more intuitive way to navigate through pages within the same browser session.
"""

import agentql
from agentql.sync_api import Page
import time
import logging
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("RemaxAgentQL")

# Define the GraphQL query for checking pagination status
PAGINATION_QUERY = """
{
    next_page_button_enabled: exists(
        "#ctl00_ContentPlaceHolder1_ListViewPager_NextButton:not([disabled]), .pagination a:not(.aspNetDisabled), .pagerLink:not([disabled])"
    )
    next_page_button_disabled: exists(
        "#ctl00_ContentPlaceHolder1_ListViewPager_NextButton[disabled], .pagination a.aspNetDisabled, .pagerLink[disabled]"
    )
    current_page_number
}
"""

# Define the GraphQL query for property listings
PROPERTY_LISTINGS_QUERY = """
{
    properties: queryAll(".gallery-item, .propertyListItem, .property-item, .listingGridBox") {
        title: text(".gallery-title a, h3, .property-title, .listingTitle, .property-address")
        price: text(".gallery-price-main .proplist_price, .gallery-price a, .price, span:has-text('TND'), span:has-text('DT')")
        location: text(".gallery-title a, .location, .property-location, .listingLocation")
        property_type: text(".gallery-transtype span, .propertyType")
        area: text(".gallery-icons img[data-original-title*='Mètres carré'] + span, span:has-text('m²'), .property-size")
        bedrooms: text(".gallery-icons img[data-original-title*='chambres'] + span, span:has-text('chambres'), span:has-text('pièces')")
        bathrooms: text(".gallery-icons img[data-original-title*='salles de bain'] + span, span:has-text('sdb'), span:has-text('salles de bain')")
        rooms: text(".gallery-icons img[data-original-title*='pièces'] + span")
        features: text(".features, .amenities, .propertyFeatures, .property-details")
        image_url: getAttribute(".gallery-photo img, img.img-responsive", "src")
        property_url: getAttribute(".gallery-title a, .LinkImage", "href")
        is_new: exists(".exclusive-banner:has-text('Nouveau sur le marché')")
        agent_name: text(".card-agent .popover-name a")
    }
    page_info {
        current_url
        page_hash: evaluate("window.location.hash")
    }
}
"""

def scrape_remax_with_agentql(base_url, max_pages=20, output_callback=None):
    """
    Scrape Remax.com.tn using AgentQL with proper hash-based pagination handling
    
    Args:
        base_url (str): The base URL for Remax.com.tn
        max_pages (int): Maximum number of pages to scrape
        output_callback (function): Optional callback function to process scraped data
                                   Signature: callback(properties, page_number)
    
    Returns:
        list: All property listings found across pages
    """
    logger.info(f"Starting Remax.com.tn scraping with AgentQL: {base_url}")
    
    # Start a new AgentQL page
    page = agentql.wrap(base_url)
    
    # Ensure we have the right hash in the URL for the first page
    current_url = page.current_url
    if "#" not in current_url:
        # Add default hash parameters for the first page
        hash_url = f"{base_url}#mode=gallery&tt=261&cur=TND&sb=MostRecent&page=1&sc=1048"
        logger.info(f"Setting initial hash URL: {hash_url}")
        page.navigate(hash_url)
        time.sleep(3)  # Wait for page to load with hash parameters
    
    # Initial scrolling to ensure all content is loaded
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    time.sleep(2)
    
    all_properties = []
    page_count = 1
    
    # Loop through pages as long as there's a next page and we haven't hit max_pages
    while page_count <= max_pages:
        logger.info(f"Processing Remax.com.tn page {page_count}")
        
        # Query the current page for property listings
        try:
            # Get properties from the current page
            results = session.query(PROPERTY_LISTINGS_QUERY)
            properties_data = results.to_data().get('properties', [])
            page_info = results.to_data().get('page_info', {})
            current_url = page_info.get('current_url', '')
            current_hash = page_info.get('page_hash', '')
            
            logger.info(f"Found {len(properties_data)} properties on page {page_count}")
            logger.info(f"Current URL: {current_url}")
            logger.info(f"Current hash: {current_hash}")
            
            # Add page number to each property
            for prop in properties_data:
                prop['page_number'] = page_count
                prop['source_site'] = "remax.com.tn"
                all_properties.append(prop)
            
            # Process scraped data if callback is provided
            if output_callback and callable(output_callback):
                output_callback(properties_data, page_count)
            
            # Check if there's a next page
            pagination = session.query(PAGINATION_QUERY)
            pagination_data = pagination.to_data()
            next_enabled = pagination_data.get('next_page_button_enabled', False)
            next_disabled = pagination_data.get('next_page_button_disabled', False)
            
            logger.info(f"Next page button enabled: {next_enabled}")
            logger.info(f"Next page button disabled: {next_disabled}")
            
            if next_enabled and not next_disabled:
                # Generate the new hash URL for the next page
                next_page_num = page_count + 1
                
                # Parse the current hash to update the page number
                if "#" in current_url:
                    base_url, hash_part = current_url.split('#', 1)
                    # Update the page parameter in the hash
                    if "page=" in hash_part:
                        new_hash = re.sub(r'page=\d+', f'page={next_page_num}', hash_part)
                    else:
                        new_hash = f"{hash_part}&page={next_page_num}"
                    next_url = f"{base_url}#{new_hash}"
                else:
                    # If no hash in URL (should not happen at this point), create a new one
                    next_url = f"{current_url}#mode=gallery&tt=261&cur=TND&sb=MostRecent&page={next_page_num}&sc=1048"
                
                logger.info(f"Navigating to next page: {next_url}")
                session.driver.navigate(next_url)
                page_count += 1
                
                # Wait for the page to load and scroll to show all content
                time.sleep(3)
                session.driver.scroll_to_bottom()
                time.sleep(1)
            else:
                logger.info("No more pages available or reached the end")
                break
            
        except Exception as e:
            logger.error(f"Error processing page {page_count}: {str(e)}")
            break
    
    # Close the AgentQL session
    session.close()
    logger.info(f"Remax.com.tn scraping completed. Total properties collected: {len(all_properties)}")
    return all_properties


def get_remax_property_count(base_url):
    """
    Quick function to just get the property count from Remax.com.tn
    
    Args:
        base_url (str): The base URL for Remax.com.tn
    
    Returns:
        int: Number of properties found on the first page
    """
    try:
        session = agentql.start_session(base_url)
        time.sleep(2)
        
        # Ensure we have the right hash in the URL
        current_url = session.driver.get_url()
        if "#" not in current_url:
            hash_url = f"{base_url}#mode=gallery&tt=261&cur=TND&sb=MostRecent&page=1&sc=1048"
            session.driver.navigate(hash_url)
            time.sleep(3)
        
        session.driver.scroll_to_bottom()
        time.sleep(2)
        
        results = session.query(PROPERTY_LISTINGS_QUERY)
        properties_data = results.to_data().get('properties', [])
        count = len(properties_data)
        
        session.close()
        return count
    except Exception as e:
        logger.error(f"Error getting property count: {str(e)}")
        return 0


# Test function
def test_remax_agentql():
    """Test the Remax AgentQL pagination"""
    base_url = "https://www.remax.com.tn/PublicListingList.aspx"
    
    def print_page_data(properties, page_number):
        print(f"Page {page_number}: Found {len(properties)} properties")
        for i, prop in enumerate(properties[:2]):  # Print first 2 properties
            print(f"  Property {i+1}: {prop.get('title', 'No title')} - {prop.get('price', 'No price')}")
    
    # Run the test scrape with a callback to print some data
    properties = scrape_remax_with_agentql(base_url, max_pages=3, output_callback=print_page_data)
    print(f"Total properties found: {len(properties)}")
    return properties


if __name__ == "__main__":
    test_remax_agentql()
