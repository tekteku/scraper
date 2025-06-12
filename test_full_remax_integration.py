"""
Test script for full Remax integration in Tunisian Property Scraper
"""

import os
import logging
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("FullIntegrationTest")

def test_remax_full_integration():
    """Test the full Remax integration by running the main scraper with just Remax enabled"""
    # Backup original SITE_CONFIGS
    from tunisian_property_scraper import SITE_CONFIGS as ORIGINAL_CONFIGS
    
    # Create a version with only Remax for testing
    remax_config = next((config for config in ORIGINAL_CONFIGS if config["name"] == "remax.com.tn"), None)
    
    if not remax_config:
        logger.error("Remax configuration not found in SITE_CONFIGS")
        return
    
    # Modify SITE_CONFIGS to only include Remax
    import tunisian_property_scraper
    tunisian_property_scraper.SITE_CONFIGS = [remax_config]
    
    # Set max pages to 2 for faster testing
    remax_config["max_pages"] = 2
    
    # Run the main function
    logger.info("Starting test with only Remax.com.tn")
    tunisian_property_scraper.main()
    
    logger.info("Test completed successfully")
    
if __name__ == "__main__":
    try:
        test_remax_full_integration()
    except Exception as e:
        logger.error(f"Error during test: {e}")
        import traceback
        traceback.print_exc()
