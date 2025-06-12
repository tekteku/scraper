# Flag to enable specific handling of Remax.com.tn's hash-based URL pagination
# Save this file and add it to your SCRAPER folder
# Then make sure this snippet is implemented in your main scraper when handling Remax URLs
# Example hash-based URL: https://www.remax.com.tn/PublicListingList.aspx#mode=gallery&tt=261&cur=TND&sb=MostRecent&page=2&sc=1048&sid=7e6fd428-3ad7-4e60-aec1-1d113cdb5f08

def handle_remax_hash_pagination(current_url, page_number):
    """
    Handle Remax.com.tn hash-based URL pagination
    
    Args:
        current_url (str): The current URL
        page_number (int): The desired page number to navigate to
        
    Returns:
        str: The URL with updated hash fragment for the requested page
    """
    # If URL already has a hash, parse it
    if "#" in current_url:
        base_url, hash_part = current_url.split('#', 1)
        
        # If hash already has page parameter, update it
        if "page=" in hash_part:
            # Replace the current page with the new page
            parts = []
            for param in hash_part.split('&'):
                if param.startswith("page="):
                    parts.append(f"page={page_number}")
                else:
                    parts.append(param)
            new_hash = '&'.join(parts)
            return f"{base_url}#{new_hash}"
        else:
            # Add page parameter to existing hash
            return f"{current_url}&page={page_number}"
    else:
        # Create a new hash with default parameters based on observed URL patterns
        return f"{current_url}#mode=gallery&tt=261&cur=TND&sb=MostRecent&page={page_number}&sc=1048"

# Example usage:
# next_url = handle_remax_hash_pagination("https://www.remax.com.tn/PublicListingList.aspx", 2)
# print(next_url)  # Should print URL with hash fragment for page 2
# 
# next_url = handle_remax_hash_pagination("https://www.remax.com.tn/PublicListingList.aspx#mode=gallery&tt=261&cur=TND&page=1", 2)
# print(next_url)  # Should update existing page=1 to page=2

"""
Important Remax.com.tn Scraping Notes:

1. The site uses ASP.NET framework with URLs containing hash fragments
2. Property listings are in .propertyListItem and .listingGridBox containers
3. Navigation to next pages requires updating the hash fragment, not the base URL
4. When adding to your scraper configuration, make sure to set:
   "hash_url_pagination": True

Property detail elements to target:
- Title: .property-title, h3, .listingTitle, .property-address, .addressLine1
- Price: .price, .property-price, .listingPrice, span with "TND" or "DT" text
- Location: .location, .property-location, .listingLocation, .addressLine2, .cityLabel
- Area: Look for text containing "m²" in .item-specs or property attributes
- Bedrooms/Bathrooms: Look for text with "chambre", "pièce", "sdb", or "salle de bain"

Example hash fragment components:
- mode=gallery      (display mode)
- tt=261            (property type ID)
- cur=TND           (currency)
- sb=MostRecent     (sort by)
- page=2            (page number)
- sc=1048           (search criteria ID)
- sid=7e6fd428-...  (session ID)

The most important parameter is 'page=' which must be updated for pagination.
"""
